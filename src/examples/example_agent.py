from dotenv import load_dotenv
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI

load_dotenv()

def multiply(a: float, b: float) -> float:
    """Multiply two numbers and returns the product"""
    return a * b

def add(a: float, b: float) -> float:
    """Add two numbers and returns the sum"""
    return a + b

def subtract(a: float, b: float) -> float:
    """Subtract two numbers and returns the difference"""
    return a - b

multiply_tool = FunctionTool.from_defaults(fn=multiply)
add_tool = FunctionTool.from_defaults(fn=add)
subtract_tool = FunctionTool.from_defaults(fn=subtract)

llm = OpenAI(model='gpt-4o-mini',temperature=0)
agent = ReActAgent.from_tools([multiply_tool, add_tool, subtract_tool], llm=llm, verbose=True)

response = agent.chat('What is 20+(2*4)-20? Use a tool to calculate every step.')

print(response)
