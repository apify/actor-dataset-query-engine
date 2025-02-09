import logging
import pathlib
from typing import Any

import uvicorn
from apify import Actor
from llama_index.llms.openai import OpenAI
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .const import HEADERS_READINESS_PROBE
from .exceptions import DatasetLoadError, WorkflowExecutionError
from .input_model import DatasetQueryAgent as ActorInput
from .query_engine import load_dataset, run_workflow
from .utils import check_inputs


class ActorInputStandbyStarts(ActorInput):
    """Standby mode inputs params are not required to be passed when Actor starts"""

    query: str = ''
    datasetId: str = ''  # noqa:N815
    llmProviderApiKey: str = ''  # noqa: N815


logger = logging.getLogger('apify')

ACTOR_IS_AT_HOME = Actor.is_at_home()
STANDBY_MODE = Actor.config.meta_origin == 'STANDBY'

if ACTOR_IS_AT_HOME:
    HOST = Actor.config.standby_url if STANDBY_MODE else Actor.config.web_server_url
    PORT = Actor.config.standby_port if STANDBY_MODE else Actor.config.web_server_port
else:
    from dotenv import load_dotenv
    load_dotenv(pathlib.Path(__file__).parent.joinpath('.env').resolve())
    HOST = 'http://localhost'
    PORT = 4321

ACTOR_URL = f'{HOST}' if ACTOR_IS_AT_HOME else f'{HOST}:{PORT}'
STANDBY_MESSAGE = (f'Actor is running in standby mode, please provide query params at {ACTOR_URL}, you can use the '
           f'following params: {ActorInput.model_fields}')


async def process_query(actor_input: ActorInput) -> Any:
    """Process query, load dataset (if it was not loaded yet) and run workflow (query engine)"""

    dataset_id = actor_input.datasetId
    try:
        await load_dataset(dataset_id, refresh_dataset=bool(actor_input.refreshDataset))
        Actor.log.info(f'Dataset {dataset_id} loaded successfully')
    except Exception as e:
        msg = f'Error loading dataset {dataset_id} with error: {e}'
        logger.exception(msg)
        raise DatasetLoadError(msg) from e

    try:
        llm = OpenAI(model=str(actor_input.modelName), api_key=actor_input.llmProviderApiKey)
        return await run_workflow(query=actor_input.query, table_name=dataset_id, llm=llm)
    except Exception as e:
        msg = f'Error running workflow, error: {e}'
        logger.exception(msg)
        raise WorkflowExecutionError(msg) from e


async def route_root(request: Request) -> JSONResponse:

    logger.debug('Received request at /')
    if request.method != 'GET':
        return JSONResponse({'message': f'Method: {request.method} not allowed'}, status_code=405)

    if str(request.headers.get(HEADERS_READINESS_PROBE)) == '1':
        logger.debug('Received readiness probe')
        return JSONResponse({'status': 'ok'})

    query_params = dict(request.query_params.items())
    query_params.pop('token', None)
    if request.query_params:
        try:
            actor_input = ActorInput(**query_params)
            result = await process_query(actor_input)
            logger.info(f'Query {actor_input.query} processed successfully, result: {result}')
            return JSONResponse({'message': result.response, 'metadata': result.metadata })
        except Exception as e:
            msg = f'Failed to process request, error: {e}'
            logger.exception(msg)
            raise HTTPException(status_code=400, detail=msg) from e

    return JSONResponse({'message': STANDBY_MESSAGE}, status_code=200)


app = Starlette(
    debug=True,
    routes=[
        Route('/', route_root),
    ],
)


async def start_server() -> None:
    logger.info(f'Starting the HTTP server at {ACTOR_URL}')
    config = uvicorn.Config(app, port=PORT)
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    async with Actor:
        if STANDBY_MODE:
            logger.info(f'Starting the HTTP server on port {Actor.config.web_server_port}')
            await start_server()
        else:
            logger.info('Starting in query engine in the NORMAL mode')
            try:
                logger.info('Starting dataset query engine, checking inputs')
                if payload := await Actor.get_input():
                    await Actor.fail(status_message='Actor input was not provided')
                    return

                actor_input = ActorInput(**payload)
                actor_input = await check_inputs(actor_input, payload)
                await process_query(actor_input)
            except Exception as e:
                Actor.log.error('Error in inputs: %s', str(e))
                await Actor.fail(status_message=str(e))

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
