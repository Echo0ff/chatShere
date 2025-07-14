import logging.config
import os  # 导入 os 模块
from typing import Dict

from .config import settings

LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

# 彩色日志格式
COLORED_LOG_FORMAT = "%(log_color)s[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s"
# 普通文件日志格式
FILE_LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s"


def get_logging_config() -> Dict:
    """
    获取日志配置字典。
    这个字典详细定义了日志的格式、处理器和记录器。
    """
    LOG_LEVEL = settings.log_level.upper()

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": "colorlog.ColoredFormatter",  # 使用 colorlog 的格式化器
                "format": COLORED_LOG_FORMAT,
                "log_colors": LOG_COLORS,
            },
            "standard": {
                "format": FILE_LOG_FORMAT,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "colored",
                "level": LOG_LEVEL,
                "stream": "ext://sys.stdout",  # 输出到标准输出
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",  # 使用滚动文件处理器
                "formatter": "standard",
                "level": LOG_LEVEL,
                "filename": "logs/chatsphere.log",  # 日志文件路径
                "maxBytes": 10 * 1024 * 1024,  # 每个文件最大 10 MB
                "backupCount": 5,  # 保留最近的 5 个备份文件
                "encoding": "utf-8",
            },
        },
        "loggers": {
            # Root logger: 项目中所有未使用 getLogger("specific_name") 的日志都会用这个
            "": {
                "handlers": ["console", "file"],
                "level": LOG_LEVEL,
            },
            # Uvicorn 日志记录器: 统一它们的格式
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",  # Uvicorn 日志可以保持 INFO
                "propagate": False,  # 防止日志向 root logger 传播，避免重复记录
            },
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }


def setup_logging():
    """
    应用日志配置。在 FastAPI 应用启动时调用此函数。
    """
    # 在应用配置之前，先确保日志目录存在
    log_dir = "logs"
    # 我们从配置字典中动态获取日志文件名，避免硬编码
    # 注意：这需要 get_logging_config() 函数先被定义
    config = get_logging_config()
    log_filename = config.get("handlers", {}).get("file", {}).get("filename")

    if log_filename:
        log_dir = os.path.dirname(log_filename)
        os.makedirs(log_dir, exist_ok=True)

    logging.config.dictConfig(config)
