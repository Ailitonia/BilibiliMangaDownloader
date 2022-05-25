"""
@Author         : Ailitonia
@Date           : 2022/05/25 18:28
@FileName       : file_handler.py
@Project        : BilibiliMangaDownloader 
@Description    : file handler
@GitHub         : https://github.com/Ailitonia
@Software       : PyCharm 
"""

import os
import sys
import asyncio
import pathlib
import aiofiles
import zipfile
from copy import deepcopy
from asyncio import Future
from typing import TypeVar, ParamSpec, Generator, Callable, Coroutine, Awaitable, Optional, Any
from functools import wraps, partial
from contextlib import asynccontextmanager


_root_folder: pathlib.Path = pathlib.Path(os.path.abspath(sys.path[0]))
"""下载文件夹路径"""
if not _root_folder.exists():
    _root_folder.mkdir()


P = ParamSpec("P")
T = TypeVar("T")
R = TypeVar("R")


def run_sync(func: Callable[P, R]) -> Callable[P, Coroutine[None, None, R]]:
    """一个用于包装 sync function 为 async function 的装饰器

    :param func: 被装饰的同步函数
    """

    @wraps(func)
    async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_running_loop()
        p_func = partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, p_func)

    return _wrapper


async def semaphore_gather(
        tasks: list[Future[T] | Coroutine[Any, Any, T] | Generator[Any, Any, T] | Awaitable[T]],
        semaphore_num: int,
        *,
        return_exceptions: bool = True) -> tuple[T | BaseException, ...]:
    """使用 asyncio.Semaphore 来限制一批需要并行的异步函数

    :param tasks: 任务序列
    :param semaphore_num: 单次并行的信号量限制
    :param return_exceptions: 是否在结果中包含异常
    """
    _semaphore = asyncio.Semaphore(semaphore_num)

    async def _wrap_coro(
            coro: Future[T] | Coroutine[Any, Any, T] | Generator[Any, Any, T] | Awaitable[T]) -> Coroutine[Any, Any, T]:
        async with _semaphore:
            return await coro

    return await asyncio.gather(*(_wrap_coro(coro) for coro in tasks), return_exceptions=return_exceptions)


class FileHandler(object):
    """文件操作工具"""
    _local_root: pathlib.Path = _root_folder

    def __init__(self, *args: str):
        self.path = self._local_root
        if args:
            self.path = self.path.joinpath(*[str(x) for x in args])

    def __repr__(self) -> str:
        return f'<FileHandler(path={self.path})>'

    def __call__(self, *args) -> "FileHandler":
        new_obj = deepcopy(self)
        new_obj.path = self.path.joinpath(*[str(x) for x in args])
        return new_obj

    @property
    def parent(self) -> "FileHandler":
        new_obj = deepcopy(self)
        new_obj.path = self.path.parent
        return new_obj

    @staticmethod
    def check_directory(func: Callable[P, R]) -> Callable[P, R]:
        """装饰一个方法, 需要实例 path 为文件夹时才能运行"""
        @wraps(func)
        def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            self: "FileHandler" = args[0]
            if self.path.exists() and self.path.is_dir():
                return func(*args, **kwargs)
            else:
                raise ValueError(f'"{self.path}" is not a directory, or directory {self.path} not exists')
        return _wrapper

    @staticmethod
    def check_file(func: Callable[P, R]) -> Callable[P, R]:
        """装饰一个方法, 需要实例 path 为文件时才能运行"""
        @wraps(func)
        def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            self: "FileHandler" = args[0]
            if self.path.exists() and self.path.is_file():
                return func(*args, **kwargs)
            elif not self.path.exists():
                if not self.path.parent.exists():
                    pathlib.Path.mkdir(self.path.parent, parents=True)
                return func(*args, **kwargs)
            else:
                raise ValueError(f'"{self.path}" is not a file, or file {self.path} not exists')
        return _wrapper

    @property
    def resolve_path(self) -> str:
        return str(self.path.resolve())

    @asynccontextmanager
    @check_file
    async def async_open(self, mode, encoding: str | None = None, **kwargs):
        """返回文件 async handle"""
        async with aiofiles.open(file=self.path, mode=mode, encoding=encoding, **kwargs) as _afh:
            yield _afh

    @classmethod
    def _create_zip(
            cls,
            input_files: list["FileHandler"],
            output_file: "FileHandler",
            *,
            compression: int = zipfile.ZIP_DEFLATED
    ) -> "FileHandler":
        """创建 zip 压缩文件

        :param input_files: 被压缩的文件列表
        :param output_file: 输出的压缩文件
        :param compression: 压缩级别参数
        """
        if output_file.path.suffix != '.zip':
            raise ValueError('Output file suffix must be ".zip"')

        if not output_file.path.parent.exists():
            pathlib.Path.mkdir(output_file.path.parent, parents=True)

        with zipfile.ZipFile(output_file.path.resolve(), mode='w', compression=compression) as zip_f:
            for file in input_files:
                if file.path.exists() and file.path.is_file():
                    zip_f.write(file.path.resolve(), arcname=file.path.name)
        return output_file

    @check_directory
    async def create_zip(
            self,
            *,
            compression: int = zipfile.ZIP_DEFLATED,
            output_file: Optional["FileHandler"] = None
    ) -> "FileHandler":
        """将当前目录中的文件压缩到 zip 文件, 异步方法

        :param compression: 压缩级别参数
        :param output_file: 输出的压缩文件, 默认为当前目录的父目录
        """
        file_list: list["FileHandler"] = []
        for dir_path, dir_names, file_names in os.walk(self.path):
            if file_names:
                for file_name in file_names:
                    file_list.append(self(dir_path, file_name))

        if output_file is None:
            output_file = self.parent(f'{self.path.name}.zip')

        loop = asyncio.get_running_loop()
        p_func = partial(self._create_zip, input_files=file_list, output_file=output_file, compression=compression)
        zip_file = await loop.run_in_executor(None, p_func)
        return zip_file


__all__ = [
    'FileHandler',
    'semaphore_gather'
]
