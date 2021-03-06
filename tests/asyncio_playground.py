if __name__ == '__main__':
    import asyncio

    async def test(val):
        print('a'+str(val))
        await asyncio.sleep(5)
        print('b'+str(val))

    async def main(loop):
        for i in range(10):
            asyncio.ensure_future(test(i), loop=loop)
        return

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    pending = asyncio.Task.all_tasks(loop)  # needed to 'discover' the co-routines made in the sub function main()!
    loop.run_until_complete(asyncio.gather(*pending))  # gather and run_until_complete for all outstanding coroutines
