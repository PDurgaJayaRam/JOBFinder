"""Custom uvicorn loop setup that forces ProactorEventLoop on Windows.

Uvicorn's default asyncio setup forces SelectorEventLoop on Windows when
use_subprocess=True (reload mode). SelectorEventLoop doesn't support
asyncio.create_subprocess_exec which Playwright needs. This module
overrides that to use ProactorEventLoop.
"""
import asyncio
import sys


def proactor_loop_setup(use_subprocess: bool = False) -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
