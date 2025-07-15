# backend/app/core/logger.py

import logging

def setup_logger() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("Agribot_new")
    logger.setLevel(logging.INFO)   