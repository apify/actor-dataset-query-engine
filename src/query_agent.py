import logging
import os
from typing import Any

from llama_index.core.agent import ReActAgent
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI

from .tools import LLMRegistry, execute_sql, is_query_sql, load_dataset, synthesize_results, user_query_to_sql

determine_query_tool = FunctionTool.from_defaults(fn=is_query_sql)
user_query_to_sql_tool = FunctionTool.from_defaults(fn=user_query_to_sql)
execute_sql_tool = FunctionTool.from_defaults(fn=execute_sql)
results_synthesize_tool = FunctionTool.from_defaults(fn=synthesize_results)


logger = logging.getLogger('apify')


async def run_agent(query: str, table_name: str, table_schema: dict[str, Any], llm: OpenAI) -> AgentChatResponse:
    """
    Runs an agent to process a query using an LLM and tools.

    The function initializes a ReAct agent with specific tools to process a user-provided query.
    It sets the provided LLM, loads the schema for the dataset identified by the table name,
    constructs a context for the agent, and processes the query through the agent. The response
    generated by the agent is logged and returned as output.

    Args:
        query: Query string provided by the user for processing.
        table_name: The name of the table whose schema is to be used for the query.
        table_schema: Schema of the database table.
        llm: The language model to be used for processing.

    Returns:
        A string containing the response from the agent.
    """
    LLMRegistry.set(llm)

    context = f'Table name provided by user: {table_name}. Table schema: {table_schema}'

    # Initialize the ReAct Agent with the Tools (LLM not pre-instantiated)
    agent = ReActAgent.from_tools(
        [
            determine_query_tool,
            user_query_to_sql_tool,
            execute_sql_tool,
            results_synthesize_tool,
        ],
        llm=llm,
        verbose=True,
        allow_parallel_tool_calls=False,
        context=context,
    )

    response: AgentChatResponse = await agent.achat(query)
    logger.info(f'Agent answer: {response.response}')
    return response


if __name__ == '__main__':
    import asyncio

    from dotenv import load_dotenv

    load_dotenv()

    dataset_id_ = 'nLlhc8Fz9S5dCTQab'

    llm_ = OpenAI(model='gpt-4o-mini', api_key=os.environ['OPENAI_API_KEY'], temperature=0)

    print(f'Dataset {dataset_id_} loaded successfully')  # noqa:T201
    query_ = 'please give me restaurants with the best reviews and their phone numbers'  # noqa:ERA001,RUF100
    # query_ = "SELECT * FROM dataset WHERE title = 'Lucia Pizza Of Avenue X'"  # noqa:ERA001,RUF100

    table_schema_ = asyncio.run(load_dataset(dataset_id_))
    answer = asyncio.run(run_agent(query_, dataset_id_, table_schema_, llm_))
    print(f'Answer {answer}')  # noqa:T201
