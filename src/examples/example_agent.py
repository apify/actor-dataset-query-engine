"""
Processes user queries on a dataset with the help of an LLM (OpenAI GPT-4o).
It identifies SQL queries, converts user queries to SQL if required, executes the query,
and synthesizes results into a readable format for the user.

> python -m src.examples.example_agent
"""

import asyncio
import os

from dotenv import load_dotenv
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI

from ..query_agent import run_agent
from ..tools import execute_sql, is_query_sql, load_dataset, synthesize_results, user_query_to_sql

load_dotenv()

determine_query_tool = FunctionTool.from_defaults(fn=is_query_sql)
user_query_to_sql_tool = FunctionTool.from_defaults(fn=user_query_to_sql)
execute_sql_tool = FunctionTool.from_defaults(fn=execute_sql)
results_synthesize_tool = FunctionTool.from_defaults(fn=synthesize_results)


dataset_id_ = 'nLlhc8Fz9S5dCTQab'

llm_ = OpenAI(model='gpt-4o-mini', api_key=os.environ['OPENAI_API_KEY'], temperature=0)

print(f'Dataset {dataset_id_} loaded successfully')  # noqa:T201
query_ = 'please give me restaurants with the best reviews and their phone numbers'  # noqa:ERA001,RUF100
# query_ = "SELECT * FROM dataset WHERE title = 'Lucia Pizza Of Avenue X'"  # noqa:ERA001,RUF100
# query_ = 'find restaurants with wheelchair accessible entrance'  # noqa:ERA001,RUF100

table_schema_ = asyncio.run(load_dataset(dataset_id_))
answer = asyncio.run(run_agent(query_, dataset_id_, table_schema_, llm_))
print(f'Answer {answer}')  # noqa:T201
