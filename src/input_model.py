# generated by datamodel-codegen:
#   filename:  input_schema.json
#   timestamp: 2025-02-07T13:23:46+00:00

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class DatasetQueryAgent(BaseModel):
    query: str = Field(
        ...,
        description="Provide a query to specify the data to be retrieved from a dataset. The query can be in natural language or SQL format. For SQL, use the table name 'dataset'\n\nExamples (when your dataset contains data scraped from google maps):\n- Find restaurant names with reviews above 4 and with at least 100 reviews\n\n- SELECT title, totalScore, reviewsCount FROM dataset;",
        title='Text or SQL query',
    )
    datasetId: str = Field(
        ..., description='Dataset ID to retrieve data from', title='Dataset ID'
    )
    modelName: Optional[
        Literal['gpt-4o-mini', 'gpt-4o', 'o1', 'o1-mini', 'o3-mini']
    ] = Field(
        'gpt-4o-mini',
        description='Specify the LLM for SQL generation and query synthesis. Currently supports OpenAI models with varying capabilities and performance characteristics.\n',
        title='OpenAI model (OpenAI is only supported provider now)',
    )
    llmProviderApiKey: str = Field(
        ...,
        description='API key for accessing a Large Language Model',
        title='LLM Provider API key (OpenAI is only supported provider now)',
    )
    refreshDataset: Optional[bool] = Field(
        False,
        description='In the standby mode, dataset is loaded once and reused to optimize performance. This parameter allows to reload dataset to ensure updated data is available.',
        title='Refresh dataset',
    )
    limit: Optional[int] = Field(
        None,
        description='Maximum number of items to return. By default there is no limit.',
        title='Limit number of dataset items used for query',
    )
    offset: Optional[int] = Field(
        0,
        description='Number of items that should be skipped at the start. The default value is 0',
        title='Number of items to skip from the start',
    )
