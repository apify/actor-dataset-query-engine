import logging
import re
from typing import Any

import duckdb
import polars as pl
import sqlite_utils
from apify_client import ApifyClientAsync
from llama_index.core import QueryBundle, Response
from llama_index.core.indices.struct_store.sql_retriever import DefaultSQLParser
from llama_index.llms.openai import OpenAI

from .const import DEFAULT_DATASET_PROMPT, DEFAULT_RESPONSE_SYNTHESIS_PROMPT
from .utils import get_python_type

# Constant for detecting starting SQL keywords, with typical commands such as SELECT, INSERT, etc.
SQL_QUERY_PATTERN = re.compile(
    r'^\s*(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|DROP|ALTER)\b',
    re.IGNORECASE
)
DROP_TABLE_QUERY = 'DROP TABLE IF EXISTS {table_name};'
SHOW_TABLES_QUERY = 'SHOW TABLES;'

logger = logging.getLogger('apify')


class LLMRegistry:
    _llm: OpenAI | None = None

    @classmethod
    def get(cls) -> OpenAI:
        if cls._llm is None:
            raise ValueError('OpenAI instance has not been set.')
        return cls._llm

    @classmethod
    def set(cls, new_llm: OpenAI) -> None:
        cls._llm = new_llm


async def load_dataset(dataset_id: str, *, refresh_dataset: bool = False) -> dict[str, Any] | None:
    """
    Load a dataset into DuckDB after fetching it from Apify.

    If the dataset already exists in the DuckDB in-memory tables and `refresh_dataset` is set to False,
    it skips the loading process.

    Args:
        dataset_id: The unique identifier of the dataset to be loaded.
        refresh_dataset: A flag to indicate if the dataset should be reloaded.

    Returns:
        table_schema: A dictionary representing the structure of the dataset table
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

    # Get the table schema in the formatL VARCHAR, INT, etc.
    sql_schema = duckdb.sql(f'DESCRIBE {dataset_id}').fetchall()
    # convert the SQL schema to a dictionary of column names and python types (for pydantic validation)
    table_schema = {}
    for col in sql_schema:
        col_name, sql_type = col[0], col[1]
        table_schema[col_name] = get_python_type(sql_type)

    return table_schema


def is_query_sql(query: str) -> bool:
    """
    Determine whether the given string is a SQL query based on common SQL keywords.

    Args:
        query (str): String to evaluate

    Returns:
        bool: True if the string is a SQL query, False otherwise.
    """
    return bool(SQL_QUERY_PATTERN.match(query))

async def user_query_to_sql(query: str, table_name: str, table_schema: dict[str, Any]) -> str:
    """
    Converts a user query written in natural language into a SQL query.
    If you need to use LIKE statement for an array, you need to unnest it first.

    Args:
        query: The natural language query input from the user.
        table_name: Name of the database table that will be queried.
        table_schema: A dictionary describing the schema of the table, including field names and data types.

    Returns:
        A string containing the SQL query interpreted from the input parameters.
    """
    llm = LLMRegistry.get()
    prompt = DEFAULT_DATASET_PROMPT
    # Get the SQL query with text-to-SQL prompt, provide table name and schema to ensure correctness
    response_str = await llm.apredict(
        prompt=prompt,
        table_name=table_name,
        table_schema=table_schema,
        question=query,
    )
    sql_parser = DefaultSQLParser()
    return sql_parser.parse_response_to_sql(response_str, QueryBundle(query_str=query))


def execute_sql(sql_query: str) -> list[dict[str, Any]] | None:
    """
    Executes an SQL query and returns the result.

    Args:
        sql_query (str): The SQL query string to be executed.

    Returns:
        list[dict[str,Any]]: The result of the executed query as a list of dictionaries
    """

    try:
        return duckdb.sql(sql_query).df().to_dict(orient='records')
    except sqlite_utils.utils.sqlite3.OperationalError as exc:
        logger.exception(f'Error executing query: {sql_query}')
        raise ValueError('Invalid query') from exc


def synthesize_results(
        query: str, sql_query: str, db_results: list[dict[str, Any]], table_schema: dict[str, Any]
) -> Response:
    """
    Synthesize a human-readable response using an LLM based on provided SQL query, schema, and database results.

    Args:
        query (str): The original user query or intent that the synthesized response should address.
        sql_query (str): The SQL query executed against the database.
        db_results (list[dict[str, Any]]): The raw results obtained from the database following the execution
            of the SQL query.
        table_schema (dict[str, Any]): A dictionary representing the structure of the involved database tables.

    Returns:
        Response: An object containing the response generated by the language model and related metadata.
    """
    llm = LLMRegistry.get()

    response_str = llm.predict(
        DEFAULT_RESPONSE_SYNTHESIS_PROMPT,
        sql_query=sql_query,
        table_schema=table_schema,
        sql_response=db_results,
        query_str=query,
    )
    response_metadata = {'sql_query': sql_query, 'table_schema': str(table_schema)}
    return Response(response=response_str, metadata=response_metadata)
