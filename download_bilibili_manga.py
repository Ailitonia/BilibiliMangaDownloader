"""
@Author         : Ailitonia
@Date           : 2022/05/25 19:07
@FileName       : downloader_main.py
@Project        : BilibiliMangaDownloader 
@Description    : 
@GitHub         : https://github.com/Ailitonia
@Software       : PyCharm 
"""

import sys
import asyncio
from argparse import ArgumentParser
from bilibili_manga_downloader import download_manga
from bilibili_manga_downloader.logger import logger


def _create_argument_parser() -> ArgumentParser:
    """命令解析器"""
    parser = ArgumentParser(description='bilibili漫画下载')
    parser.add_argument('-c', '--comic-id', type=str, default='', help='漫画id')
    parser.add_argument('-e', '--ep-index', type=str, default='', help='章节序号')
    return parser


if __name__ == '__main__':
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    arg = _create_argument_parser().parse_args(args=sys.argv[1:])

    if not arg.comic_id:
        logger.opt(colors=True).info('您没有指定需要下载的漫画 id, 通常漫画 id 可以在漫画主页 url 中找到, '
                                     '例如: https//manga.bilibili.com/detail/mc<lc>31031</lc> 中的 "<lc>31031</lc>"')
        comic_id = input('请输入想要下载的漫画id:\n漫画id: ')
    else:
        comic_id = arg.comic_id

    if not comic_id.isdigit():
        logger.error(f'{comic_id} 不是可用的漫画 id! 漫画 id 应当为纯数字!')
        sys.exit()

    comic_id = int(comic_id)

    if not arg.ep_index:
        logger.opt(colors=True).info('您没有指定需要下载的漫画章节数, 将会下载该漫画全部章节')
        ep_index = None
    else:
        ep_index = arg.ep_index
        if not ep_index.isdigit():
            logger.error(f'{ep_index} 不是可用的漫画章节数! 漫画章节数应当为纯数字!')
            sys.exit()
        ep_index = int(ep_index)

    asyncio.run(download_manga(comic_id=comic_id, ep_index=ep_index))
