import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger("depope-ocr")


class Timer:
    def __init__(self, label: str, logger: logging.Logger = log):
        self.label = label
        self.logger = logger

    def __enter__(self):
        self.t0 = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.t0
        self.logger.info("[%s] %.2fs", self.label, elapsed)
