# Dataset query engine

FIXME: TODO
ACTOR push dataset!!!

This Actor allows you to use natural language to query and retrieve results from an [Apify dataset](https://docs.apify.com/platform/storage/dataset).
It provides a query engine that loads a dataset, executes SQL queries against the data, and synthesizes results.

## 🎯 How can you use the query engine?

If you have a dataset scraped using any Apify Actor, you can easily extract relevant insights from it.  

For example, if you use the [Google Maps Email Extractor](https://apify.com/lukaskrivka/google-maps-with-contact-details) to search for **"the best pizza in New York,"** you’ll get a dataset containing contact details and restaurant information.  

With the **query engine**, you can ask questions like:  

```
"Provide a list of top restaurants with the best reviews, along with their phone numbers."
```

The Actor will respond with:  

```
Here are some restaurants with outstanding reviews and their corresponding phone numbers:

1. Smith Street Pizza - (347) ....
2. Gravesend Pizza - (718) ....
3. Lucia Pizza of Avenue X - (718) ....
```

This makes it easy to extract useful data without manually filtering through large datasets. 🚀  

## 🛢 How does the query agent work?

The query engine operates using two configurable approaches: AI Agent or Agentic workflow.
While the AI Agent provides flexibility and autonomous reasoning, the Agentic Workflow ensures predictable and controlled processing.
The choice is determined by the useAgent parameter.

### AI Agent using [LlamaIndex ReAct Agent](https://docs.llamaindex.ai/en/stable/understanding/agent/) 

When `useAgent` is set to `true`, the system employs the ReAct (Reasoning and Acting) framework. 
In this mode, the agent works autonomously and interprets the user's query and determines the optimal strategy to achieve the desired outcome. 
It utilizes a set of tools, such as `is_query_sql`, `user_query_to_sql`, `execute_sql`, and `synthesize_results`, to process the query. 
The agent decides which tools to use and in what sequence.


### Agentic [Workflow](https://docs.llamaindex.ai/en/stable/module_guides/workflow/) 

When `useAgent` is set to `false`, the system follows a predefined, deterministic workflow. 
In this mode, the user's query is processed through a fixed sequence of steps. 
This approach ensures predictable outcomes. 
Workflows chain together several events (tools) and follow a predefined flow. 
They consist of individual `steps`, with each step designed to process specific event types and generate subsequent events.

## Tools

- **`load_dataset(dataset_id, refresh_dataset=False)`** – Loads a dataset from Apify into **DuckDB**, extracts schema, and maps SQL types to Python.  
- **`is_query_sql(query)`** – Detects if a query is in SQL using regex.  
- **`user_query_to_sql(query, table_name, table_schema)`** – Converts natural language to SQL using **LLM**.  
- **`execute_sql(sql_query)`** – Runs an SQL query in **DuckDB** and returns results.  
- **`synthesize_results(query, sql_query, db_results, table_schema)`** – Generates a **human-readable response** from SQL results using **LLM**.  

## ⚙️ Usage  

Actor can be used in two ways: **as a standard Actor** by passing an input, or in **Standby mode** via an HTTP request.

### Normal Actor run  

You can run the Actor "normally" via the **Apify API, schedule, integrations, or manually** in the Apify Console. 
On start, you provide an input JSON object with settings, such as `query` and `datasetId`.
The Actor loads the dataset into **DuckDB (in-memory)** and uses it to generate an answer.
The disadvantage of this approach is that for every subsequent run, the dataset needs to be **reloaded into memory**, which adds overhead.
Additionally, starting a **Docker container** takes time, and the Actor can handle only **one query at a time**, making it inefficient for high-frequency queries.

### Standby web server  

The Actor supports **[Standby mode](https://docs.apify.com/platform/actors/running/standby)**, where it runs an HTTP server that processes queries on demand.
This mode eliminates the need to **reload the dataset** for each request and **removes container startup time**.

To use the Dataset query engine in **Standby mode**, send an HTTP GET request to:  

```
https://database-query-engine.apify.actor/query?token=<APIFY_API_TOKEN>&query=return+phone+number&llmProviderApiKey=<OPENAI_API_KEY>
```
where `<OPENAI_API_KEY>` is your **[OpenAI API Key](https://platform.openai.com/api-keys)**, and  
`<APIFY_API_TOKEN>` is your **[Apify API Token](https://console.apify.com/settings/integrations)**.  
Alternatively, you can pass the Apify `token` using the `Authorization` HTTP header for improved security.  

The response is a JSON object containing the query results.  

#### Query parameters  

The `/` GET HTTP endpoint supports the following parameters:  

| Parameter             | Type     | Default          | Description                                                                                                                      |
|----------------------|---------|------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `query`             | string  | N/A              | SQL query or a natural language query. If a natural language query is provided, it is converted to SQL before execution.       |
| `datasetId`         | string  | N/A              | The ID of the dataset to query.                                                                                                |
| `modelName`         | string  | `gpt-4o-mini`    | Specifies the LLM for SQL generation and query synthesis. Currently supports OpenAI models.                                    |
| `llmProviderApiKey` | string  | N/A              | API key for accessing a Large Language Model.                                                                                  |
| `refreshDataset`    | boolean | `false`          | If enabled, reloads the dataset to ensure updated data is available.                                                           |
| `limit`            | integer | No limit         | Maximum number of items to return.                                                                                             |
| `offset`           | integer | `0`              | Number of items to skip before returning data.                                                                                 |
| `useAgent`         | boolean | `true`           | Enables AI-powered query handling instead of a deterministic workflow. The AI Agent can handle more tasks but may be less reliable. |


## 🔌 Integration with LLMs  

Dataset query engine has been designed for easy integration with LLM applications, GPTs, and Model Context Protocol.

### OpenAPI schema

Here you can find the [OpenAPI 3.1.0 schema](https://apify.com/jiri.spilka/database-query-engine/api/openapi).
The schema includes all available query parameters, but only `query`, `datasetId`, and `llmProviderApiKey` are required.
You can omit other parameters if their default values are suitable for your application.

### OpenAI GPTs

You can add the Dataset query engine to your GPTs by creating a custom action. Here's a quick guide:

1. Go to [**My GPTs**](https://chatgpt.com/gpts/mine) on ChatGPT website and click **+ Create a GPT**.
2. Complete all required details in the form.
3. Under the **Actions** section, click **Create new action**.
4. In the Action settings, set **Authentication** to **API key** and choose Bearer as **Auth Type**.
5. In the **schema** field, paste the OpenAPI 3.1.0 schema

Learn more about [adding custom actions to your GPTs with Apify Actors](https://blog.apify.com/add-custom-actions-to-your-gpts/) on Apify Blog.

### Anthropic: Model Context Protocol (MCP) Server (in progress)

NOTE: The requirement to provide `llmProviderApiKey` as an Actor input is currently a blocker.
This can be resolved using Price Per Event pricing (or Price Per Job).
If this is blocking your use case, please provide feedback by raising an issue.

The dataset query engine can also be used as an [MCP server](https://github.com/modelcontextprotocol) and integrated with AI applications and other AI agents, such as Claude Desktop.
You can integrate it using **Apify's [Actors MCP Server](https://apify.com/apify/actors-mcp-server)**. Simply provide `query`, `datasetId`, and `llmProviderApiKey` to receive an answer.
To use it, start the **Actors MCP Server** with the **Dataset query engine** included in the list of available Actors.

- For deployment on the **Apify platform**, follow the **[Standby mode setup](https://apify.com/apify/actors-mcp-server#standby-web-server)**.
- For running the Actor **locally over stdio**, refer to the **[Claude Desktop setup](https://apify.com/apify/actors-mcp-server#claude-desktop)**.

## 👷🏼 Development

The dataset query engine Actor has open source available on [GitHub](https://github.com/apify/actor-dataset-query-engine.git),
so that you can modify and develop it yourself. Here are the steps how to run it locally on your computer.

Download the source code:

```bash
git clone https://github.com/apify/actor-dataset-query-engine.git
cd actor-dataset-query-engine
```

Install dependencies:

```bash
uv sync
```

Setup input arguments in `actor-dataset-query-engine/storage/key_value_stores/default/INPUT.json`

```
{
  "query": "email of Italian restaurants in New York",
  "datasetId": "YOUR-DATASET-ID",
  "llmProviderApiKey": "YOUR-LLM-PROVIDER-API-KEY"
}
```

And then you can run it locally using [Apify CLI](https://docs.apify.com/cli) as follows:

```bash
apify run -p
```
