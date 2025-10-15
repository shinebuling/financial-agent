import json
import os
import operator
from typing import TypedDict, Annotated, Sequence

from dotenv import load_dotenv
from langchain_community.tools import PolygonLastQuote, PolygonTickerNews, PolygonFinancials, PolygonAggregates
from langchain_community.utilities.polygon import PolygonAPIWrapper
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.messages import FunctionMessage
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai.chat_models import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langgraph.prebuilt import ToolInvocation

from app.tools import discounted_cash_flow, owner_earnings, roic, roe

# Load the environment variables
load_dotenv()

# DeepSeek-R1 wrapper that handles message format conversion
from langchain_core.messages.utils import convert_to_messages

class DeepSeekChatOpenAI(ChatOpenAI):
    def _convert_input(self, input):
        """Override to handle LangChain message format for DeepSeek-R1"""
        if isinstance(input, list):
            # Convert LangChain format to OpenAI format
            converted_messages = []
            for msg in input:
                if hasattr(msg, 'content'):
                    # Already a proper message object
                    converted_messages.append(msg)
                elif isinstance(msg, dict):
                    # Convert dict format
                    content = msg.get('content', '')
                    msg_type = msg.get('type', 'human')
                    
                    if msg_type == 'human':
                        converted_messages.append(HumanMessage(content=content))
                    elif msg_type == 'ai':
                        converted_messages.append(AIMessage(content=content))
                    elif msg_type == 'system':
                        converted_messages.append(SystemMessage(content=content))
                    else:
                        # Fallback to human message
                        converted_messages.append(HumanMessage(content=content))
                else:
                    converted_messages.append(msg)
            
            return super()._convert_input(converted_messages)
        return super()._convert_input(input)

model = DeepSeekChatOpenAI(
    model="DeepSeek-V3",  # 修正模型名称
    base_url="https://ai.gitee.com/v1",
    api_key=os.getenv("GITEE_API_KEY"),
    streaming=True,
    max_tokens=1024,
    temperature=0.6,
    model_kwargs={
        "top_p": 0.8,
        "extra_body": {
            "top_k": 20,
        },
        "frequency_penalty": 1.1,
    }
)

# Create the tools
polygon = PolygonAPIWrapper()
integration_tools = [
    PolygonLastQuote(api_wrapper=polygon),
    PolygonTickerNews(api_wrapper=polygon),
    PolygonFinancials(api_wrapper=polygon),
    PolygonAggregates(api_wrapper=polygon),
]

local_tools = [discounted_cash_flow, roe, roic, owner_earnings]
tools = integration_tools + local_tools

tool_executor = ToolExecutor(tools)

functions = [convert_to_openai_function(t) for t in tools]
model = model.bind_functions(functions)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state['messages']
    last_message = messages[-1]
    # If there is no function call, then we finish
    if "function_call" not in last_message.additional_kwargs:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


# Define the function that calls the model
def call_model(state):
    messages = state['messages']
    try:
        print(f"DEBUG: Calling model with messages: {messages}")
        
        # Ensure messages are properly formatted
        formatted_messages = []
        for msg in messages:
            print(f"DEBUG: Processing message: {msg}, type: {type(msg)}")
            
            if hasattr(msg, 'content') and hasattr(msg, 'type'):
                # Already a proper LangChain message object
                formatted_messages.append(msg)
            elif isinstance(msg, dict):
                # Convert dict format to proper message objects
                content = msg.get('content', '')
                msg_type = msg.get('type', 'human')
                
                print(f"DEBUG: Converting dict message - type: {msg_type}, content: {content}")
                
                if msg_type == 'human':
                    formatted_messages.append(HumanMessage(content=content))
                elif msg_type == 'ai':
                    formatted_messages.append(AIMessage(content=content))
                elif msg_type == 'system':
                    formatted_messages.append(SystemMessage(content=content))
                else:
                    formatted_messages.append(HumanMessage(content=content))
            else:
                formatted_messages.append(msg)
        
        print(f"DEBUG: Formatted messages: {formatted_messages}")
        
        response = model.invoke(formatted_messages)
        print(f"DEBUG: Model response: {response}")
        
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}
        
    except Exception as e:
        print(f"ERROR in call_model: {e}")
        print(f"ERROR type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error message as AI response
        error_response = AIMessage(content=f"抱歉，处理您的请求时遇到错误：{str(e)}")
        return {"messages": [error_response]}


# Define the function to execute tools
def call_tool(state):
    messages = state['messages']
    # Based on the continue condition
    # we know the last message involves a function call
    last_message = messages[-1]
    # We construct an ToolInvocation from the function_call
    action = ToolInvocation(
        tool=last_message.additional_kwargs["function_call"]["name"],
        tool_input=json.loads(last_message.additional_kwargs["function_call"]["arguments"]),
    )
    # We call the tool_executor and get back a response
    response = tool_executor.invoke(action)
    # We use the response to create a FunctionMessage
    function_message = FunctionMessage(content=str(response), name=action.tool)
    # We return a list, because this will get added to the existing list
    return {"messages": [function_message]}


# Define a new graph
workflow = StateGraph(AgentState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # END is a special node marking that the graph should finish.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # Otherwise we finish.
        "end": END
    }
)

# We now add a normal edge from `tools` to `agent`.
workflow.add_edge('action', 'agent')

# Finally, we compile it!
agent = workflow.compile()
