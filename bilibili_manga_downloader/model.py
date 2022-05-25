"""
@Author         : Ailitonia
@Date           : 2022/05/25 19:51
@FileName       : model.py
@Project        : BilibiliMangaDownloader 
@Description    : downloader model
@GitHub         : https://github.com/Ailitonia
@Software       : PyCharm 
"""

from pydantic import BaseModel, AnyUrl


class _VerifyData(BaseModel):
    """cookie 验证 data"""
    isLogin: bool
    uname: str | None
    mid: str | None


class VerifyResult(BaseModel):
    """cookie 验证结果"""
    code: int
    message: str
    data: _VerifyData


class _BiliApiBaseModel(BaseModel):
    """bilibili api 返回数据 model 基类"""
    code: int
    msg: str


class MangaEp(_BiliApiBaseModel):
    """漫画的全部章节"""

    class _Data(BaseModel):
        class _EpInfo(BaseModel):
            id: int
            ord: int
            title: str
            short_title: str
            cover: AnyUrl

        id: int
        title: str
        horizontal_cover: AnyUrl
        square_cover: AnyUrl
        vertical_cover: AnyUrl
        last_ord: int
        is_finish: int
        evaluate: str
        total: int
        ep_list: list[_EpInfo]

    data: _Data

    @property
    def all_ep_list(self) -> list[int]:
        return [x.id for x in self.data.ep_list]


class EpImage(_BiliApiBaseModel):
    """漫画章节的全部图片"""

    class _Data(BaseModel):
        class _Images(BaseModel):
            path: str
            x: int
            y: int

        path: str
        images: list[_Images]

    data: _Data

    @property
    def all_image_path(self) -> list[str]:
        return [x.path for x in self.data.images]


class ImageToken(_BiliApiBaseModel):
    """漫画章节图片获取 token"""

    class _Data(BaseModel):
        url: str
        token: str

    data: list[_Data]

    @property
    def resource_url(self) -> str:
        return f'{self.data[0].url}?token={self.data[0].token}'


__all__ = [
    'VerifyResult',
    'MangaEp',
    'EpImage',
    'ImageToken'
]
