import sys
import asyncio
import qasync


async def noop():
    pass


def run(coro=None, *, app_arguments=None):
    '''Runs async function as a main GUI application. Blocks until application exits'''
    if app_arguments is not None:
        prog_name = sys.argv[0] if len(sys.argv) > 0 else ''
        sys.argv.clear()
        sys.argv.extend([prog_name, *app_arguments])

    save = None
    if coro is None:
        coro = noop()

    async def runner():
        nonlocal save
        save = await coro

        f = asyncio.Future()
        qasync.QApplication.instance().aboutToQuit.connect(f.cancel)

        try:
            await f
        except asyncio.exceptions.CancelledError:
            pass

    qasync.run(runner())
