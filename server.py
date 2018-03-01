import os
import json
from functools import partial
from pathlib import Path

import aiohttp
from aiohttp import web
from aiohttp import hdrs
from aiohttp import ClientSession

import config
from utils import log
from bound import get_json


PROJECT_ROOT = Path(os.path.dirname(os.path.realpath(__file__)))


async def index(request):
    # Content-Type: text/html;
    headers = {
        hdrs.CONTENT_TYPE: 'text/html',
    }
    response = web.FileResponse('index.html', headers=headers)
    return response


async def get_transaction_data(request):
    url = 'https://pay.planetakino.ua/api/v1/cart/transaction-details'
    params = {
        'transactionId': 22099423
    }
    async with ClientSession() as session:
        result = await get_json(session, url,
                                params=params, headers=config.DEFAULT_HEADERS)
        if 'data' not in result:
            return web.json_response(result, status=400)

        data = result['data']
        seat = data['seat'][0]

    dumps = partial(json.dumps, ensure_ascii=False)
    return web.json_response({
        'movie_name': data['movieName_ua'],
        'movie_date': data['showDate'],
        'movie_hall': data['theaterHall'],
        'movie_tech': data['technology'],
        'row_num': seat['row'],
        'seat_num': seat['seat'],
        'barcode': seat['ticketBarcode'],
    }, dumps=dumps)


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
    app.router.add_get('/ch', get_transaction_data)
    setup_static_routes(app)
    uprint = partial(print, flush=True)
    port = int(os.environ.get('PORT', 8080))

    uprint('Running aiohttp {}'.format(aiohttp.__version__))
    web.run_app(app, print=uprint, port=port)


if __name__ == '__main__':
    launch()
