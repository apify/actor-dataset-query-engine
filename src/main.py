import logging
from http.server import SimpleHTTPRequestHandler

import uvicorn
from apify import Actor
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .const import HEADERS_READINESS_PROBE

logger = logging.getLogger('apify')


class GetHandler(SimpleHTTPRequestHandler):
    """A simple GET HTTP handler that will respond with a message."""

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello from Actor Standby!')


async def root(request: Request) -> JSONResponse:
    if request.method == 'GET':
        if request.headers.get(HEADERS_READINESS_PROBE):
            logger.debug('Received readiness probe')
            return JSONResponse({'status': 'ok'})

        return JSONResponse({'message': 'Hello from Actor'})

    return JSONResponse({'message': 'Method not allowed'}, status_code=405)


app = Starlette(debug=True, routes=[
    Route('/', root),
])

def serve() -> None:
    logger.info(f'Starting the HTTP server on port {Actor.config.web_server_port}')
    config = uvicorn.Config(app, port=Actor.config.standby_port)
    server = uvicorn.Server(config)
    server.run()

async def main() -> None:
    async with Actor:
        logger.info(f'Starting the HTTP server on port {Actor.config.web_server_port}')
        serve()


if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(serve())
