from logging import getLogger, StreamHandler, FileHandler, Formatter, INFO
import sys

logger = getLogger("tunesynctool-api")

formatter = Formatter("%(asctime)s - %(levelname)s - %(message)s")


stream_handler = StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

file_handler = FileHandler("app.log")
file_handler.setFormatter(formatter)

logger.handlers = [stream_handler, file_handler]

logger.setLevel(INFO)