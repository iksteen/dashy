from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from dashy.dashy import Dashy

if __name__ == "__main__":
    load_dotenv()

    dashy = Dashy()

    config_path = sys.argv[1] if len(sys.argv) > 1 else "conf.py"
    with Path(config_path).open("r") as f:
        content = f.read()
    conf_globals: dict[str, Any] = {"DASHY": dashy}
    exec(content, conf_globals)

    loglevel = conf_globals.get("LOGLEVEL", logging.INFO)
    logging.basicConfig(level=loglevel)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(dashy.run())
    except KeyboardInterrupt:
        loop.run_until_complete(dashy.stop())
