import aiohttp
import asyncio
import async_timeout


async def get_json(session, url, params=None):
    params = params or {}
    async with async_timeout.timeout(10):
        async with session.get(url, params=params) as response:
            return await response.json()


async def main():
    url = 'https://pay.planetakino.ua/api/v1/cart/check-promocode'
    params = {
        'transactionId': 22075644,
        'promoCod': 234513,
        'theaterId': 'imax-kiev',
        'seatId': 800004,
    }
    async with aiohttp.ClientSession() as session:
        result = await get_json(session, url, params)
        print(result)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

