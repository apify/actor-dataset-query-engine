from llama_index.core.prompts import PromptTemplate
from llama_index.core.prompts.prompt_type import PromptType

HEADERS_READINESS_PROBE = 'x-apify-container-server-readiness-probe'

DEFAULT_DATASET_PROMPT_TMPL = (
    "You are given a table named: '{table_name}' with schema, "
    'generate only SQLite SQL query (no surrounding text) to answer the given question.\n'
    'Table schema:\n'
    '{table_schema}\n'
    'Question: {question}\n\n'
    'SQLQuery: '
)
DEFAULT_DATASET_PROMPT = PromptTemplate(DEFAULT_DATASET_PROMPT_TMPL, prompt_type=PromptType.TEXT_TO_SQL)

DEFAULT_RESPONSE_SYNTHESIS_PROMPT_TMPL = (
    'Given a query, synthesize a response based on SQL query results'
    ' to satisfy the query. Only include details that are relevant to'
    " the query. If you don't know the answer, then say that.\n"
    'SQL Query: {sql_query}\n'
    'Table Schema: {table_schema}\n'
    'SQL Response: {sql_response}\n'
    'Query: {query_str}\n'
    'Response: '
)

DEFAULT_RESPONSE_SYNTHESIS_PROMPT = PromptTemplate(
    DEFAULT_RESPONSE_SYNTHESIS_PROMPT_TMPL, prompt_type=PromptType.SQL_RESPONSE_SYNTHESIS
)
