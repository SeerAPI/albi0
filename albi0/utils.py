from collections.abc import Generator, Iterable, Iterator
from contextlib import contextmanager
import fnmatch
import functools
import gzip
import hashlib
import itertools
import os
from pathlib import Path
import time
from typing import Any, AnyStr, Callable, ParamSpec, TypeVar
import asyncio

import httpx
from tqdm import tqdm

from albi0.log import logger
from albi0.typing import PathTypes, T_PathLike

T = TypeVar('T')
P = ParamSpec('P')


def retry(
	max_retries: int = 3,
	base_delay: float = 1.0,
	max_delay: float = 60.0,
	backoff_factor: float = 2.0,
	exceptions: tuple[type[Exception], ...] = (httpx.HTTPError,),
):
	"""
	指数退避重试装饰器，支持同步和异步函数。

	Args:
		max_retries: 最大重试次数
		base_delay: 初始等待时间（秒）
		max_delay: 最大等待时间（秒）
		backoff_factor: 指数退避因子
		exceptions: 触发重试的异常类型
	"""

	def decorator(func: Callable[P, T]) -> Callable[P, T]:
		if asyncio.iscoroutinefunction(func):

			@functools.wraps(func)
			async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
				delay = base_delay
				last_exception = None
				for i in range(max_retries + 1):
					try:
						return await func(*args, **kwargs)
					except exceptions as e:
						last_exception = e
						if i == max_retries:
							logger.error(f'达到最大重试次数 ({max_retries})，最后一次错误: {e}')
							raise
						logger.warning(
							f'请求失败: {e}，正在进行第 {i + 1} 次重试，等待 {delay:.2f}s...'
						)
						await asyncio.sleep(delay)
						delay = min(delay * backoff_factor, max_delay)
				if last_exception:
					raise last_exception
				raise RuntimeError('Unreachable')

			return async_wrapper  # type: ignore
		else:

			@functools.wraps(func)
			def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
				delay = base_delay
				last_exception = None
				for i in range(max_retries + 1):
					try:
						return func(*args, **kwargs)
					except exceptions as e:
						last_exception = e
						if i == max_retries:
							logger.error(f'达到最大重试次数 ({max_retries})，最后一次错误: {e}')
							raise
						logger.warning(
							f'请求失败: {e}，正在进行第 {i + 1} 次重试，等待 {delay:.2f}s...'
						)
						time.sleep(delay)
						delay = min(delay * backoff_factor, max_delay)
				if last_exception:
					raise last_exception
				raise RuntimeError('Unreachable')

			return sync_wrapper

	return decorator


def retry_call(
	func: Callable[..., T],
	*args: Any,
	max_retries: int = 3,
	base_delay: float = 1.0,
	max_delay: float = 60.0,
	backoff_factor: float = 2.0,
	exceptions: tuple[type[Exception], ...] = (httpx.HTTPError,),
	**kwargs: Any,
) -> T:
	"""
	直接调用函数并进行重试，支持同步和异步。
	"""
	_retry: Any = retry(
		max_retries=max_retries,
		base_delay=base_delay,
		max_delay=max_delay,
		backoff_factor=backoff_factor,
		exceptions=exceptions,
	)
	return _retry(func)(*args, **kwargs)


class Hash:
	def __init__(self, data):
		self.data = data

	@classmethod
	def from_file(cls, filename: PathTypes):
		filename = Path(filename)
		return cls(filename.read_bytes())

	def md5(self) -> str:
		# 创建一个MD5哈希对象
		return hashlib.md5(self.data).hexdigest()

	def sha256(self) -> str:
		# 创建一个SHA256哈希对象
		return hashlib.sha256(self.data).hexdigest()


class FileHash(Hash):
	def __init__(self, filename: PathTypes):
		self.filename = Path(filename)
		super().__init__(self.filename.read_bytes())


def find_files(
	filenames: Iterable[AnyStr], patterns: Iterable[AnyStr]
) -> Iterator[AnyStr]:
	if not patterns:
		for filename in filenames:
			yield filename
	else:
		filter_partial = functools.partial(fnmatch.filter, filenames)
		for filename in itertools.chain(*map(filter_partial, patterns)):
			yield filename


def decompress_file(
	filename: Path, new_filename: Path, remove_original_file: bool = False
):
	"""解压一个gzip文件"""
	with gzip.open(filename, mode='rb') as f_in:
		data = f_in.read()
	with open(new_filename, 'wb') as f_out:
		f_out.write(data)
	if remove_original_file:
		filename.unlink()


def decompress_dir(
	dirname: Path,
	*,
	pattern: str,
	new_suffix: str | None = None,
	remove_original_file: bool = False,
) -> None:
	"""解压目录下所有的gzip文件"""
	files = list(dirname.glob(pattern))
	for file in tqdm(files, desc='解压中'):
		new_filename = file
		if new_suffix is not None:
			new_filename = new_filename.with_suffix(new_suffix)
		try:
			decompress_file(file, new_filename, remove_original_file)
		except gzip.BadGzipFile:
			logger.debug(f'{file.name}不是gzip压缩文件，跳过')


def remove_all_suffixes(filename: T_PathLike) -> T_PathLike:
	"""删除路径的所有后缀"""
	root, suffix = os.path.splitext(filename)
	while suffix:
		root, suffix = os.path.splitext(root)

	return type(filename)(root)  # type: ignore


@contextmanager
def set_directory(path: PathTypes):
	"""Sets the cwd within the context

	Args:
	    path (Path): The path to the cwd

	Yields:
	    None
	"""

	origin = Path().absolute()
	try:
		os.chdir(path)
		yield
	finally:
		os.chdir(origin)


T_Path = TypeVar('T_Path', bound=PathTypes)


def join_path(path: T_Path, *args: PathTypes) -> T_Path:
	import os

	return type(path)(os.path.join(path, *args))


def join_url(base: str, *urls: str) -> str:
	from urllib.parse import urljoin

	for url in urls:
		base = urljoin(base, url)

	return base


@contextmanager
def timer(
	message_template: str = '{name} 耗时: {duration:.2f}s', **kwargs
) -> Generator[None, None, None]:
	"""一个简单的计时器上下文管理器

	Args:
		message_template: 最终展示的字符串模板.
		**kwargs: 模板中可用的额外参数.
	"""
	import click

	start_time = time.perf_counter()
	try:
		yield
	finally:
		end_time = time.perf_counter()
		duration = end_time - start_time
		click.echo(message_template.format(duration=duration, **kwargs))
