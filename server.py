import os
import json
import urllib
from functools import partial
from pathlib import Path

import aiohttp
import async_timeout
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


async def get_free_seat_id(showtime_id):
    url = 'https://pay.planetakino.ua/api/v1/cart/halls'
    params = {
        'showtimeId': showtime_id,
    }
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(config.DEFAULT_TIMEOUT):
            async with session.get(url, params=params) as response:
                result = await response.json()
                data = result.get('data', {}).get('hallsSheme')

                try:
                    empty_seats = data[0]['emptySeats']
                except (TypeError, IndexError, KeyError) as e:
                    log.error('Wrong response %s: %s', e, result)
                    return config.DEFAULT_SEAT_ID

                if not empty_seats:
                    raise RuntimeError('No empty seats left!')

                # Return just first empty seat
                return empty_seats[0]


async def create_transaction(showtime_id, seat_id=None):
    url = 'https://pay.planetakino.ua/api/v1/cart/purchase'
    if seat_id is None:
        seat_id = await get_free_seat_id(showtime_id)

    log.info('Creating transaction for a seat %s', seat_id)
    payload = {
        'seatIDs': seat_id,
        'seatIDGlasses': '',
        'showtimeID': showtime_id,
    }

    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(config.DEFAULT_TIMEOUT):
            async with session.post(url, headers=config.DEFAULT_HEADERS,
                                    data=payload) as response:
                result = await response.json()
                if 'transactionId' not in result:
                    log.error('No transaction ID %s', result)
                    return

                return result['transactionId']


def get_showtime_id(url):
    parse_result = urllib.parse.urlparse(url)
    parts = filter(bool, parse_result.path.split('/'))
    return list(parts)[-1]


async def get_transaction_data(request):
    url = 'https://pay.planetakino.ua/api/v1/cart/transaction-details'
    data = await request.post()
    showtime_id = get_showtime_id(data['url'])
    desired_seat_code = data.get('seat-code') or None
    log.debug('Parsed showtime id %s', showtime_id)
    if desired_seat_code:
        log.debug('Trying to get seat %s', desired_seat_code)

    transaction_id = await create_transaction(showtime_id,
                                              seat_id=desired_seat_code)
    if transaction_id is None:
        return web.Response(text='Error during creation of transaction',
                            status=400)

    params = {
        'transactionId': transaction_id
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
    app.router.add_post('/give-me-ticket', get_transaction_data)
    setup_static_routes(app)
    uprint = partial(print, flush=True)
    port = int(os.environ.get('PORT', config.DEFAULT_PORT))

    uprint('Running aiohttp {}'.format(aiohttp.__version__))
    web.run_app(app, print=uprint, port=port)


if __name__ == '__main__':
    launch()
