"""Simple test script to check Pylontech BMS communication"""
from custom_components.pylontech.pylontech import PylontechBMS
import asyncio
import logging
import sys

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)


async def _test_command():
    pylon = PylontechBMS("192.168.1.193", 1234)
    await asyncio.wait_for(pylon.connect(), 2)
    cmd = await asyncio.wait_for(pylon.info(), 1)
    await pylon.disconnect()
    print(cmd)


asyncio.run(_test_command())
