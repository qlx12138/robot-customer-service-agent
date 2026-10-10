"""日志记录"""

import logging
from utils.path_tool import get_abs_path
import os
from datetime import datetime


#日记保存的根目录
LOG_ROOT = get_abs_path("logs")

#确保日志保存的根目录存在
os.makedirs(LOG_ROOT, exist_ok=True)

#日志的格式配置
DEFAULT_LOG_FORMAT = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s"
)

def get_logger(
        name:str = "agent",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        log_file = None
) -> logging.Logger:
    """获取日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 设置日志记录器的最低级别为DEBUG

    #避免重复添加处理器
    if logger.hasHandlers():
        return logger

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)

    # 文件处理器
    if not log_file:
        log_file_path = os.path.join(LOG_ROOT, f"{name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    else:
        log_file_path = log_file

    file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)

    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

#快捷获取日志记录器
logger = get_logger()


if __name__ == "__main__":
    logger.info("这是一个信息日志")
    logger.error("这是一个错误日志")
    logger.warning("这是一个警告日志")
    logger.debug("这是一个调试日志")