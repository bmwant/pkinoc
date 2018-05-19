import asyncio

from server import (
    get_free_seat_id,
)


async def test_get_free_seat_id():
    showtime_id = '470864'  # it's for deadpool, hah
    seat_id = await get_free_seat_id(showtime_id)
    assert seat_id
    print(seat_id)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_get_free_seat_id())
