"""
Demonstrates the use of a query engine workflow to analyze a dataset with OpenAI's LLM.
Loads environment variables, initializes the engine, and executes a query asynchronously.

> python -m src.examples.example_workflow
"""

import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI

from ..query_engine import DatasetAnalyzeQueryEngineWorkflow
from ..tools import load_dataset

load_dotenv()

dataset_id_ = 'nLlhc8Fz9S5dCTQab'
table_schema_ = asyncio.run(load_dataset(dataset_id_))

llm_ = OpenAI(model='gpt-4o-mini', api_key=os.environ['OPENAI_API_KEY'])
w = DatasetAnalyzeQueryEngineWorkflow()
# query_ = 'please give me restaurants with the best reviews and their phone numbers'  # noqa:ERA001,RUF100
query_ = "SELECT * FROM dataset WHERE title = 'Lucia Pizza Of Avenue X'"  # noqa:ERA001,RUF100


async def main() -> Any:
    r = await w.run(query=query_, llm=llm_, table_name=dataset_id_, table_schema=table_schema_)
    print(f'> Question: {query_}')  # noqa:T201
    print(f'Answer: {r}')  # noqa:T201
    return r


asyncio.run(main())
