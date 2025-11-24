import logging
from loguru import logger


def setup_logging(log_file_path="./log/main.log", project_prefix=None):
    logger.remove()
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(name)s - %(message)s"
    )

    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.ERROR)
    root_logger.addHandler(console_handler)

    if project_prefix is not None:
        for name in logging.root.manager.loggerDict.keys():
            logging.getLogger(name).disabled = True
    logging.getLogger("mcp").disabled = True


if __name__ == "__main__":
    print("Just for the demo usage of the logging module")
    setup_logging(project_prefix="IntelliSearch")

    logger = logging.getLogger(__name__)
    TOOL_CALL_ERROR = 35
    logging.addLevelName(TOOL_CALL_ERROR, "TOOL CALL ERROR")

    logger.info("Chat client initialization started.")
    logger.log(TOOL_CALL_ERROR, "An error occurred during tool execution.")
