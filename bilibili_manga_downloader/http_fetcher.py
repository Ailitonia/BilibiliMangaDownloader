"""
@Author         : Ailitonia
@Date           : 2022/05/25 19:04
@FileName       : http_fetcher.py
@Project        : BilibiliMangaDownloader 
@Description    : http fetcher
@GitHub         : https://github.com/Ailitonia
@Software       : PyCharm 
"""

import inspect
from aiohttp import ClientSession, ClientTimeout
from asyncio.exceptions import TimeoutError as _TimeoutError
from typing import TypeVar, ParamSpec, Callable, Coroutine, Any
from functools import wraps

from .file_handler import FileHandler
from .logger import logger


_DEFAULT_HEADERS = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate',
    'accept-language': 'zh-CN,zh;q=0.9',
    'dnt': '1',
    'origin': 'https://manga.bilibili.com',
    'referer': 'https://manga.bilibili.com/',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/101.0.4951.67 Safari/537.36'
}


P = ParamSpec("P")
R = TypeVar("R")


class ExceededAttemptError(Exception):
    """重试次数超过限制异常"""


def retry(attempt_limit: int = 3):
    """装饰器, 自动重试, 仅用于异步函数

    :param attempt_limit: 重试次数上限
    """

    def decorator(func: Callable[P, Coroutine[None, None, R]]) -> Callable[P, Coroutine[None, None, R]]:
        if not inspect.iscoroutinefunction(func):
            raise ValueError('The decorated function must be coroutine function')

        @wraps(func)
        async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            attempts_num = 0
            _module = inspect.getmodule(func)
            while attempts_num < attempt_limit:
                try:
                    return await func(*args, **kwargs)
                except _TimeoutError:
                    logger.opt(colors=True).debug(
                        f'<lc>Decorator Retry</lc> | <ly>{_module.__name__ if _module is not None else "Unknown"}.'
                        f'{func.__name__}</ly> <r>Attempted {attempts_num + 1} times</r> <c>></c> <r>TimeoutError</r>')
                except Exception as e:
                    logger.opt(colors=True).warning(
                        f'<lc>Decorator Retry</lc> | <ly>{_module.__name__ if _module is not None else "Unknown"}.'
                        f'{func.__name__}</ly> <r>Attempted {attempts_num + 1} times</r> <c>></c> '
                        f'<r>Exception {e.__class__.__name__}</r>: {e}')
                finally:
                    attempts_num += 1
            else:
                logger.opt(colors=True).error(
                    f'<lc>Decorator Retry</lc> | <ly>{_module.__name__ if _module is not None else "Unknown"}.'
                    f'{func.__name__}</ly> <r>Attempted {attempts_num} times</r> <c>></c> '
                    f'<r>Exception ExceededAttemptError</r>: The number of failures exceeds the limit of attempts. '
                    f'<lc>Parameters(args={args}, kwargs={kwargs})</lc>')
                raise ExceededAttemptError('The number of failures exceeds the limit of attempts')
        return _wrapper

    return decorator


@retry(attempt_limit=3)
async def fetch_get_json(
        url: str,
        session: ClientSession,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        cookies: dict | None = None,
        proxy:  dict | None = None,
        timeout: int = 5,
        **kwargs
) -> Any:
    """使用 get 方法获取并解析 json 数据"""
    headers = _DEFAULT_HEADERS if headers is None else headers
    timeout = ClientTimeout(total=timeout)

    async with session.get(
            url=url, params=params, headers=headers, cookies=cookies, proxy=proxy, timeout=timeout, **kwargs) as rp:
        result = await rp.json()
    return result


@retry(attempt_limit=3)
async def fetch_post_json(
        url: str,
        session: ClientSession,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        cookies: dict | None = None,
        proxy:  dict | None = None,
        timeout: int = 5,
        **kwargs
) -> Any:
    """使用 post 方法获取并解析 json 数据"""
    headers = _DEFAULT_HEADERS if headers is None else headers
    timeout = ClientTimeout(total=timeout)

    async with session.post(
            url=url, params=params, headers=headers, cookies=cookies, proxy=proxy, timeout=timeout, **kwargs) as rp:
        result = await rp.json()
    return result


@retry(attempt_limit=3)
async def download_file(
        url: str,
        file: FileHandler,
        session: ClientSession,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        cookies: dict | None = None,
        proxy: dict | None = None,
        timeout: int = 20,
        **kwargs
) -> FileHandler:
    """下载文件到指定位置"""
    headers = _DEFAULT_HEADERS if headers is None else headers
    timeout = ClientTimeout(total=timeout)

    async with session.get(
            url=url, params=params, headers=headers, cookies=cookies, proxy=proxy, timeout=timeout, **kwargs) as rp:
        result = await rp.read()

    async with file.async_open('wb') as af:
        await af.write(result)
    return file


__all__ = [
    'fetch_get_json',
    'fetch_post_json',
    'download_file'
]
