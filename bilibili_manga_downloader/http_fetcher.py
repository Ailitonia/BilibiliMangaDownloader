"""
@Author         : Ailitonia
@Date           : 2022/05/25 19:04
@FileName       : http_fetcher.py
@Project        : BilibiliMangaDownloader 
@Description    : http fetcher
@GitHub         : https://github.com/Ailitonia
@Software       : PyCharm 
"""

from typing import Any
from aiohttp import ClientSession, ClientTimeout

from .file_handler import FileHandler


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
