"""Server entry point - forces ProactorEventLoop for Playwright on Windows.

Uvicorn's default asyncio setup forces SelectorEventLoop on Windows when
reload=True, which breaks Playwright's subprocess creation. We monkey-patch
uvicorn's loop setup to use ProactorEventLoop instead.
"""
import sys
import asyncio

# MUST be set before uvicorn imports anything
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Monkey-patch uvicorn's asyncio loop setup to NOT override our policy
    import uvicorn.loops.asyncio as _loop_mod
    def _proactor_setup(use_subprocess: bool = False) -> None:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    _loop_mod.asyncio_setup = _proactor_setup

import uvicorn

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="127.0.0.1", port=8001, reload=True)
