import logging
from typing import Any

from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step
from llama_index.llms.openai import OpenAI

from .tools import LLMRegistry, execute_sql, is_query_sql, load_dataset, synthesize_results, user_query_to_sql

logger = logging.getLogger('apify')


class DatasetAnalyzerEvent(Event):
    """
    Event is a pydantic object with the following attributes:
        query (str): The generated SQL query.
        table_schema (Dict[str, Any]): Schema of the analyzed table.
        results (List[Dict[str, Any]]): Query execution results.
    """

    query: str
    table_schema: dict[str, Any]


class SynthesizeEvent(Event):
    sql_query: str
    table_schema: dict[str, Any]
    results: list[dict[str, Any]]


class DatasetAnalyzeQueryEngineWorkflow(Workflow):
    @step
    async def user_query_analyzer(self, ctx: Context, ev: StartEvent) -> DatasetAnalyzerEvent | SynthesizeEvent:
        """
        Analyzes user-provided query and dataset for either SQL synthesis or further dataset analysis.

        Args:
            ctx (Context): The context object where intermediate data is stored.
            ev (StartEvent): The event payload containing information such as 'llm', 'query', and 'table_name'.

        Returns:
            DatasetAnalyzerEvent | SynthesizeEvent: If the query is determined to be a valid SQL,
                returns SynthesizeEvent containing the synthesized  query, the table schema, and the query results.
                For non-SQL queries, returns DatasetAnalyzerEvent with the query and the table schema.

        """
        llm = ev.get('llm')
        query = ev.get('query')
        table_name = ev.get('table_name')
        table_schema = ev.get('table_schema')

        await ctx.set('llm', llm)
        await ctx.set('query', ev.get('query'))
        await ctx.set('table_name', ev.get('table_name'))
        await ctx.set('table_schema', ev.get('table_schema'))

        LLMRegistry.set(llm)

        if is_query_sql(query):
            sql_query = query.replace('dataset', table_name)
            results = execute_sql(sql_query)
            return SynthesizeEvent(sql_query=sql_query, table_schema=table_schema, results=results)

        return DatasetAnalyzerEvent(query=query, table_schema=table_schema)

    @step
    async def dataset_analyzer(self, ctx: Context, ev: DatasetAnalyzerEvent) -> SynthesizeEvent:
        """
        Analyzes a dataset by converting a user query to an SQL query, executing the query,
        and returning the results along with the table schema.

        Args:
            ctx (Context): The execution context that provides access to runtime data like
                the table name.
            ev (DatasetAnalyzerEvent): An event object containing the user query and
                table schema relevant for generating and executing the SQL query.

        Returns:
            SynthesizeEvent: An event containing the executed SQL query, the table schema
                used, and the results of the query.
        """
        table_name = await ctx.get('table_name', default=None)
        table_schema = await ctx.get('table_schema', default=None)

        query = ev.query

        sql_query = await user_query_to_sql(query, table_name, table_schema)
        results = execute_sql(sql_query)
        return SynthesizeEvent(sql_query=sql_query, table_schema=table_schema, results=results)

    @step
    async def synthesize(self, ctx: Context, ev: SynthesizeEvent) -> StopEvent:
        """
        Synthesizes results from a SQL query.

        Args:
            ctx (Context): The context from which data is retrieved.
            ev (SynthesizeEvent): The event containing the SQL query, results, and table schema.

        Returns:
            StopEvent: An event containing the synthesized result.
        """
        query = await ctx.get('query', default=None)
        response = synthesize_results(query, ev.sql_query, ev.results, ev.table_schema)
        logger.info(f'Workflow answer: {response.response}')
        return StopEvent(result=response)


async def run_workflow(
        query: str, table_name: str, table_schema: dict[str, Any], llm: OpenAI, verbose: bool = False
) -> Any:
    w = DatasetAnalyzeQueryEngineWorkflow(verbose=verbose)
    return await w.run(query=query, llm=llm, table_name=table_name, table_schema=table_schema)
