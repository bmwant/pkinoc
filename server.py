import os
from functools import partial
from pathlib import Path

import aiohttp
from aiohttp import web
from aiohttp import hdrs

from utils import log


PROJECT_ROOT = Path(os.path.dirname(os.path.realpath(__file__)))


async def index(request):
    # Content-Type: text/html;
    headers = {
        hdrs.CONTENT_TYPE: 'text/html',
    }
    response = web.FileResponse('index.html', headers=headers)
    return response


def setup_static_routes(app):
    app.router.add_static('/static/',
                          path=PROJECT_ROOT / 'static',
                          name='static')
    app.router.add_static('/node_modules/',
                          path=PROJECT_ROOT / 'node_modules',
                          name='node_modules')


def launch():
    app = web.Application()
    app.router.add_get('/', index)
    setup_static_routes(app)
    uprint = partial(print, flush=True)
    port = int(os.environ.get('PORT', 8080))

    uprint('Running aiohttp {}'.format(aiohttp.__version__))
    web.run_app(app, print=uprint, port=port)


if __name__ == '__main__':
    launch()
