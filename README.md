# Dataset query engine

FIXME: TODO
ACTOR push dataset!!!

This Actor allows you to use natural language to query and retrieve results from an [Apify dataset](https://docs.apify.com/platform/storage/dataset).
It provides a query engine that loads a dataset, executes SQL queries against the data, and synthesizes results.

## How can you use the query engine?

If you have a dataset scraped using any Apify Actor, you can easily extract relevant insights from it.  

For example, if you use the [Google Maps Email Extractor](https://apify.com/lukaskrivka/google-maps-with-contact-details) to search for **"the best pizza in New York,"** you’ll get a dataset containing contact details and restaurant information.  

With the **Query engine**, you can ask questions like:  

- **"Provide a list of top restaurants with the best reviews, along with their phone numbers."**  

The Actor will respond with:  

```
Here are some restaurants with outstanding reviews and their corresponding phone numbers:

1. Smith Street Pizza - (347) ....
2. Gravesend Pizza - (718) ....
3. Lucia Pizza of Avenue X - (718) ....
```

This makes it easy to extract useful data without manually filtering through large datasets. 🚀  

## How does the query agent work?

The Query engine operates using two configurable approaches: AI Agent or Agentic workflow.
While the AI Agent provides flexibility and autonomous reasoning, the Agentic Workflow ensures predictable and controlled processing.
The choice is determined by the useAgent parameter.

### AI Agent using [llama index react agent](https://docs.llamaindex.ai/en/stable/understanding/agent/) 

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

Actor can be used in two ways: **as a standard Actor** by passing an inout, or in **Standby mode** via an HTTP request.  c

### Normal Actor Run  

You can run the Actor "normally" via the **Apify API, schedule, integrations, or manually** in the Apify Console. 
On start, you provide an input JSON object with settings, such as `query` and `datasetId` and you will receive Agent response in the Actor output.

### Standby Web Server  

The Actor supports **[Standby mode](https://docs.apify.com/platform/actors/running/standby)**, where it runs an HTTP server that processes queries on demand. This mode is preferred for production applications, as it eliminates container startup time and allows handling multiple requests in parallel, improving efficiency.  

To use the Database Query Engine in **Standby mode**, send an HTTP GET request to:  

```
https://database-query-engine.apify.actor/query?token=<APIFY_API_TOKEN>&query=SELECT+*+FROM+dataset
```

where `<APIFY_API_TOKEN>` is your **[Apify API token](https://console.apify.com/settings/integrations)**.  
Alternatively, you can pass the token using the `Authorization` HTTP header for improved security.  

The response is a JSON object containing the query results.  

---

### Query Parameters  

The `/` GET HTTP endpoint supports the following parameters:  

| Parameter        | Type    | Default  | Description                                                                                                              |
|-----------------|---------|----------|--------------------------------------------------------------------------------------------------------------------------|
| `query`         | string  | N/A      | SQL query or a natural language query. If a natural language query is provided, it is converted to SQL before execution. |
| `datasetId`     | string  | N/A      | The ID of the dataset to query.                                                                                          |
| `limit`         | number  | No limit | The maximum number of results to return.                                                                                 |
| `offset`        | number  | `0`      | The number of results to skip before returning data.                                                                     |
| `refreshDataset`| boolean | `false`  | Whether to reload the dataset before executing the query.                                                                |
| `useAgent`      | boolean | `false`  | Enables AI-powered query handling instead of direct SQL execution.                                                       |
| `llmModel`      | string  | `gpt-4o-mini` | The OpenAI model used for natural language to SQL conversion.                                                            |

---

## 🔌 Integration with LLMs  

The **Database Query Engine** is designed for **seamless integration with LLM applications**, OpenAI Assistants, and **RAG pipelines**.  

## Usage

### Running Locally

1. **Install Dependencies:**  
   Make sure you have Python 3.12.8 installed along with the required packages (see your `requirements.txt` for details). For example:

```shell script
pip install -r requirements.txt
```

2. **Start the Actor:**  
   To run the HTTP server in Standby mode, execute:

```shell script
python main.py
```

   The server will start on a specified host and port (by default, these are configured in the file). You can change these settings by modifying the configuration constants.

3. **Send a Query Request:**  
   Once the server is running, you can send queries using a tool like `curl`. For example:

```shell script
curl "http://localhost:4321/?query=select+*+from+restaurants&datasetId=<DATASET_ID>&llmProviderApiKey=<LLM_API_KEY>"
```

   Replace `<DATASET_ID>` and `<LLM_API_KEY>` with your respective values.

### API Endpoints

- **Root Route (`/`):**  
  Handles incoming GET requests that include query parameters. The main parameters include:
  - `query`: A text string (or SQL query) to process.
  - `datasetId`: Identifier for the dataset to be loaded and queried.
  - `llmProviderApiKey`: API key for the LLM provider (if the response needs further synthesis).

The endpoint uses the `process_query` method (defined in main.py) to direct the incoming request to the underlying dataset query engine (query_engine.py).


## Licensing

This project is open source. Please review the [LICENSE](LICENSE) file for more details.