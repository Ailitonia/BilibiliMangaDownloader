import aiohttp
import json
import re
from aiohttp import ClientSession
from datetime import datetime

from .config import BilibiliCookiesConfig
from .file_handler import FileHandler, semaphore_gather
from .http_fetcher import fetch_get_json, fetch_post_json, download_file
from .logger import logger
from .model import VerifyResult, MangaEp, EpImage, ImageToken


_cookies_config = BilibiliCookiesConfig(_env_file='.env', _env_file_encoding='utf-8')
"""B站 Cookies 配置"""
logger.opt(colors=True).warning('<ly>请注意, 本工具只能下载哔哩哔哩漫画的免费章节和用户已订阅章节, 不能下载收费章节!</ly>')
logger.opt(colors=True).warning('<ly>若想要下载用户已订阅章节, 请在 .env 文件中正确配置您的用户 cookies!</ly>')


async def _verify_bilibili_cookie(*, session: ClientSession) -> None:
    """验证 Bilibili cookie 是否有效

    :return: valid, message
    """
    verify_url = 'https://api.bilibili.com/x/web-interface/nav'
    result = await fetch_get_json(url=verify_url, cookies=_cookies_config.cookies, session=session)

    verify = VerifyResult.parse_obj(result)
    if verify.code != 0 or not verify.data.isLogin:
        _cookies_config.clear()
        logger.opt(colors=True).warning(f'<r>Bilibili cookies 验证失败</r>, 登录状态异常, {verify.message}')
    else:
        logger.opt(colors=True).success(f'<lg>Bilibili cookie 已验证</lg>, 登录用户: {verify.data.uname}')


async def _query_manga_ep(comic_id: int, *, session: ClientSession) -> MangaEp:
    """根据漫画 cm id 获取章节 id 列表"""
    url = 'https://manga.bilibili.com/twirp/comic.v1.Comic/ComicDetail?device=pc&platform=web'
    query_params = {'comic_id': str(comic_id)}
    result = await fetch_post_json(url=url, session=session, cookies=_cookies_config.cookies, json=query_params)
    return MangaEp.parse_obj(result)


async def _query_ep_image(ep_id: int, *, session: ClientSession) -> EpImage:
    """根据章节 ep id 获取图片路径"""
    url = 'https://manga.bilibili.com/twirp/comic.v1.Comic/GetImageIndex?device=pc&platform=web'
    query_params = {'ep_id': str(ep_id)}
    result = await fetch_post_json(url=url, session=session, cookies=_cookies_config.cookies, json=query_params)
    return EpImage.parse_obj(result)


async def _query_image_token(image_path: str, *, session: ClientSession) -> ImageToken:
    """根据章节图片 path 获取下载图片所需要的 token"""
    url = 'https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=pc&platform=web'
    quote_path = json.dumps([image_path])
    query_params = {'urls': quote_path}
    result = await fetch_post_json(url=url, session=session, cookies=_cookies_config.cookies, json=query_params)
    return ImageToken.parse_obj(result)


async def _download_image(image_path: str, *, file: FileHandler, session: ClientSession) -> FileHandler:
    """下载单个图片

    :param image_path: 图片 path
    :param file: 指定下载目标文件
    """
    try:
        image_token = await _query_image_token(image_path=image_path, session=session)
        if image_token.code != 0:
            raise RuntimeError(f'bilibili api error: {image_token.msg}')
    except Exception as e:
        logger.error(f'获取图片资源({image_path}) token 失败, {e}')
        raise e

    try:
        downloaded_file = await download_file(url=image_token.resource_url, file=file, session=session)
    except Exception as e:
        logger.error(f'下载图片资源({image_path})失败, {e}')
        raise e
    return downloaded_file


async def _download_ep(ep_id: int, *, folder: FileHandler, session: ClientSession) -> FileHandler:
    """下载章节全部图片并压缩

    :param ep_id: 章节id
    :param folder: 指定下载路径
    """
    try:
        ep_image = await _query_ep_image(ep_id=ep_id, session=session)
        if ep_image.code != 0:
            raise RuntimeError(f'bilibili api error: {ep_image.msg}')
    except Exception as e:
        logger.error(f'获取漫画章节({ep_id})图片资源失败, {e}')
        raise e

    all_count = len(ep_image.all_image_path)
    logger.info(f'已成功获取章节({ep_id})图片资源, 共 {all_count} 张图片, 开始下载')
    tasks = [_download_image(image_path=image_path, session=session,
                             file=folder(f'{ep_id}_page_{index}.{image_path.split(".")[-1]}'))
             for index, image_path in enumerate(ep_image.all_image_path)]

    download_result = await semaphore_gather(tasks=tasks, semaphore_num=16, return_exceptions=True)
    exceptions = [x for x in download_result if isinstance(x, BaseException)]
    fail_count = len(exceptions)

    logger.info(f'下载漫画章节({ep_id})完成, 成功: {all_count - fail_count}, 失败: {fail_count}, 开始创建压缩文件')

    try:
        zip_file = await folder.create_zip()
    except Exception as e:
        logger.info(f'压缩漫画章节({ep_id})失败, {e}')
        raise e

    logger.info(f'漫画章节({ep_id})下载压缩成功, 文件路径: {zip_file.resolve_path}')
    return zip_file


def _replace_filename(filename: str) -> str:
    """移除文件名中的特殊字符"""
    filename = re.sub(r'[\\/:*"<>|]', '_', filename)
    filename = re.sub(r'\?', '？', filename)
    return filename


async def download_manga(comic_id: int, ep_index: int | None = None) -> None:
    """下载漫画

    :param comic_id: 漫画 id
    :param ep_index: 章节 id
    """
    t_suffix: str = datetime.now().strftime('%Y%m%d-%H%M%S')
    _timeout: int = 10
    async with aiohttp.ClientSession(timeout=_timeout) as session:
        if not _cookies_config.cookies:
            logger.opt(colors=True).warning('<r>未配置 bilibili 用户 Cookies</r>, <ly>只能下载免费章节</ly>')
        else:
            await _verify_bilibili_cookie(session=session)

        try:
            manga_ep = await _query_manga_ep(comic_id=comic_id, session=session)
            if manga_ep.code != 0:
                raise RuntimeError(f'bilibili api error: {manga_ep.msg}')
        except Exception as e:
            logger.error(f'获取漫画({comic_id})章节失败, {e}')
            raise e

        logger.info(f'已获取漫画"{manga_ep.data.title}"章节列表, 共 {manga_ep.data.total} 章')

        if ep_index is not None and ep_index not in manga_ep.all_ep_list:
            raise ValueError(f'指定的章节 id 不属于漫画"{manga_ep.data.title}"')

        tasks = [
            _download_ep(
                session=session, ep_id=ep.id,
                folder=FileHandler(
                    'download',
                    f'{comic_id}_{_replace_filename(manga_ep.data.title)}_{t_suffix}',
                    f'{ep.id}_{_replace_filename(ep.short_title)}_{_replace_filename(ep.title)}'
                )
            )
            for ep in manga_ep.data.ep_list
            if (ep_index is None) or (ep_index is not None and ep_index in manga_ep.all_ep_list and ep.id == ep_index)
        ]

        all_count = len(tasks)
        download_result = await semaphore_gather(tasks=tasks, semaphore_num=2, return_exceptions=True)

        exceptions = [x for x in download_result if isinstance(x, BaseException)]
        fail_count = len(exceptions)

        logger.info(f'下载漫画"{manga_ep.data.title}"完成, 成功: {all_count - fail_count}, 失败: {fail_count}')

    logger.success(f'漫画"{manga_ep.data.title}"下载任务全部完成')


__all__ = [
    'download_manga'
]
