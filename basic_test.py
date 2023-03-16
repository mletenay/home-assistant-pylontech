"""Simple test script to check Pylontech BMS communication"""
from custom_components.pylontech_console.pylontech import PylontechConsole
import asyncio
import logging
import sys

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)


async def _test_command():
    console = PylontechConsole("192.168.1.193", 1234)
    await console.connect()
    cmd = await console.unit()
    print(cmd)


asyncio.run(_test_command())
