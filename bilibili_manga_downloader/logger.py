"""
@Author         : Ailitonia
@Date           : 2022/05/25 19:25
@FileName       : logger.py
@Project        : BilibiliMangaDownloader 
@Description    : logger
@GitHub         : https://github.com/Ailitonia
@Software       : PyCharm 
"""

import sys
import loguru


logger = loguru.logger

default_format: str = (
    "<g>{time:MM-DD HH:mm:ss}</g> "
    "[<lvl>{level}</lvl>] "
    "<c><u>{name}</u></c> | "
    "{message}"
)
"""默认日志格式"""
logger.remove()
logger_id = logger.add(
    sys.stdout,
    level=0,
    colorize=True,
    diagnose=False,
    format=default_format,
)

__all__ = [
    'logger'
]
