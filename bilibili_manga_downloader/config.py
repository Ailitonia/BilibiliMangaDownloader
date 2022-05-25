"""
@Author         : Ailitonia
@Date           : 2022/05/25 19:05
@FileName       : config.py
@Project        : BilibiliMangaDownloader 
@Description    : bilibili account cookie config
@GitHub         : https://github.com/Ailitonia
@Software       : PyCharm 
"""

from typing import Optional
from pydantic import BaseSettings


class BilibiliCookiesConfig(BaseSettings):
    sessdata: Optional[str]
    bili_jct: Optional[str]

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    @property
    def cookies(self) -> dict | None:
        if self.sessdata and self.bili_jct:
            return {'SESSDATA': self.sessdata, 'bili_jct': self.bili_jct}
        return None

    def clear(self) -> None:
        self.sessdata = None
        self.bili_jct = None


__all__ = [
    'BilibiliCookiesConfig'
]
