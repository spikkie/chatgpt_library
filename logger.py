# app/logger.py

import logging
import sys

# LOG_LEVEL = "INFO"  # or "DEBUG" for more detail
LOG_LEVEL = "DEBUG"  # or "DEBUG" for more detail

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger("forex-market-prep")  # Or any project name
