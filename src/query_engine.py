import logging
import os
from typing import Any

import duckdb
import polars as pl
import sqlite_utils
from apify_client import ApifyClientAsync
from llama_index.core.base.response.schema import Response
from llama_index.core.indices.struct_store.sql_retriever import DefaultSQLParser
from llama_index.core.utils import print_text
from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step
from llama_index.llms.openai import OpenAI

from .const import DEFAULT_DATASET_PROMPT, DEFAULT_RESPONSE_SYNTHESIS_PROMPT
from .utils import get_python_type

logger = logging.getLogger('apify')

SHOW_TABLES_QUERY = 'SHOW TABLES;'
DROP_TABLE_QUERY = 'DROP TABLE IF EXISTS {table_name};'


async def load_dataset(dataset_id: str, *, refresh_dataset: bool = False) -> None:
    """Load dataset from Apify into memory.

    Registers the dataset in duckdb using dataset_id as the table name.
    """
    existing_tables = duckdb.sql(SHOW_TABLES_QUERY)
    dataset_exists = dataset_id in str(existing_tables)

    if refresh_dataset or not dataset_exists:
        client = ApifyClientAsync()
        items = await client.dataset(dataset_id).get_items_as_bytes()
        dataset = pl.read_json(items)

        if dataset_exists:
            duckdb.sql(DROP_TABLE_QUERY.format(table_name=dataset_id))

        duckdb.register(dataset_id, dataset)
        logger.debug(f'Dataset {dataset_id} loaded successfully')
    else:
        logger.debug(f'Dataset {dataset_id} already loaded')


async def query_sql_dataset(dataset_id: str, sql_query: str) -> Any:
    """Query the dataset using a SQL query, replace 'dataset' with dataset_id.

    Load the dataset if it is not already loaded.
    """
    r = duckdb.sql('SHOW TABLES;')
    if dataset_id not in str(r):
        logger.debug(f'Dataset {dataset_id} not found ... loading dataset')
        await load_dataset(dataset_id)

    sql_query = sql_query.replace('dataset', dataset_id)
    return duckdb.sql(sql_query).fetchall()


class DatasetAnalyzerEvent(Event):
    """
    Event that contains results of analysis.

    Event is a pydantic object with the following attributes:
        sql_query (str): The generated SQL query.
        table_schema (Dict[str, Any]): Schema of the analyzed table.
        results (List[Dict[str, Any]]): Query execution results.
    """

    sql_query: str
    table_schema: dict[str, Any]
    results: list[dict[str, Any]]


class DatasetAnalyzeQueryEngineWorkflow(Workflow):
    @step
    async def dataset_analyzer(self, ctx: Context, ev: StartEvent) -> DatasetAnalyzerEvent:
        """
        Analyze Apify datatest using a SQL-like query approach.

        This asynchronous method sets up an in-memory duckdb database and loads Apify dataset into it.
        It generates a SQL query based on a natural language question, executes the query, and returns the results.

        Args:
            ctx (Context): The context object for storing data during execution.
            ev (StartEvent): The event object containing input parameters.

        Returns:
            DatasetAnalyzerEvent: An event object containing the SQL query, table schema, and query results.

        The method performs the following steps:
        - Extracts necessary data from the input event.
        - Generates a SQL query using a LLM based on the input question.
        - Executes the SQL query and retrieves the results.
        - Returns the results along with the SQL query and table schema.
        """
        await ctx.set('query', ev.get('query'))
        await ctx.set('llm', ev.get('llm'))

        query = ev.get('query')
        table_name = ev.get('table_name')
        llm = ev.get('llm')

        prompt = DEFAULT_DATASET_PROMPT

        await load_dataset(table_name)
        # Get the table schema in the formatL VARCHAR, INT, etc.
        sql_schema = duckdb.sql(f'DESCRIBE {table_name}').fetchall()

        # convert the SQL schema to a dictionary of column names and python types (for pydantic validation)
        table_schema = {}
        for col in sql_schema:
            col_name, sql_type = col[0], col[1]
            table_schema[col_name] = get_python_type(sql_type)

        # Get the SQL query with text-to-SQL prompt, provide table name and schema to ensure correctness
        response_str = await llm.apredict(
            prompt=prompt,
            table_name=table_name,
            table_schema=table_schema,
            question=query,
        )

        sql_parser = DefaultSQLParser()
        sql_query = sql_parser.parse_response_to_sql(response_str, query)

        try:
            # Execute the SQL query
            results = duckdb.sql(sql_query).df().to_dict(orient='records')
        except sqlite_utils.utils.sqlite3.OperationalError as exc:
            print_text(f'Error executing query: {sql_query}')
            raise ValueError('Invalid query') from exc

        return DatasetAnalyzerEvent(sql_query=sql_query, table_schema=table_schema, results=results)

    @step
    async def synthesize(self, ctx: Context, ev: DatasetAnalyzerEvent) -> StopEvent:
        """Synthesize the response."""
        llm = await ctx.get('llm', default=None)
        query = await ctx.get('query', default=None)

        response_str = llm.predict(
            DEFAULT_RESPONSE_SYNTHESIS_PROMPT,
            sql_query=ev.sql_query,
            table_schema=ev.table_schema,
            sql_response=ev.results,
            query_str=query,
        )
        response_metadata = {'sql_query': ev.sql_query, 'table_schema': str(ev.table_schema)}
        response = Response(response=response_str, metadata=response_metadata)
        return StopEvent(result=response)


async def run_workflow(query: str, table_name: str, llm: OpenAI) -> Any:
    w = DatasetAnalyzeQueryEngineWorkflow()
    return await w.run(query=query, llm=llm, table_name=table_name)


if __name__ == '__main__':
    import asyncio

    from dotenv import load_dotenv

    load_dotenv()

    dataset_id_ = 'gNcf77u0UikBXXtf7'

    llm_ = OpenAI(model='gpt-4o-mini', api_key=os.environ['OPENAI_API_KEY'])
    w = DatasetAnalyzeQueryEngineWorkflow()
    print(f'Dataset {dataset_id_} loaded successfully')  # noqa:T201
    query_ = 'I need phone numbers for places in Rockaway Park city'

    async def main() -> Any:
        r = await w.run(query=query_, llm=llm_, table_name=dataset_id_)
        print(f'> Question: {query_}')  # noqa:T201
        print(f'Answer: {r}')  # noqa:T201
        return r

    asyncio.run(main())
