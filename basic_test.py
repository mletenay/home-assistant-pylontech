"""Simple test script to check Pylontech BMS communication"""

import asyncio
import logging
import sys

from custom_components.pylontech.pylontech import PylontechBMS

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)


async def _test_command():
    pylon = PylontechBMS("192.168.2.51", 1234)
    await asyncio.wait_for(pylon.connect(), 2)
    cmd = await asyncio.wait_for(pylon.info(), 1)
    await pylon.disconnect()
    print(cmd)


asyncio.run(_test_command())
