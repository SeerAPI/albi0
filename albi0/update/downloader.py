from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Literal, NamedTuple

import aiofiles
import anyio
import httpx
from httpx import URL
from tqdm.asyncio import tqdm

from ..request import client as default_client
from ..typing import DownloadPostProcessMethod
from ..utils import Hash, retry

if TYPE_CHECKING:
	from httpx import AsyncClient, Response
	from httpx._types import URLTypes


class DownloadParams(NamedTuple):
	url: 'URLTypes'
	filename: Path
	method: Literal['GET', 'POST'] = 'GET'
	md5: str | None = None


class Downloader:
	_global_client: ClassVar['AsyncClient'] = default_client

	def __init__(self, client: 'AsyncClient | None' = None, limit: int = 10):
		self._client = client or self._global_client
		self._semaphore = anyio.Semaphore(limit)

	@retry()
	async def _get_data(
		self,
		url: 'URLTypes',
		*,
		method: Literal['GET', 'POST'] = 'GET',
		md5: str | None = None,
	) -> bytes:
		url = URL(str(url))
		async with self._client.stream(method, url, timeout=None) as res:
			res: 'Response'
			res.raise_for_status()

			data = b''
			with tqdm(
				total=int(res.headers.get('content-length', 0)),
				unit_scale=True,
				unit_divisor=1024,
				unit='B',
				desc=f'{url.path.split("/")[-1]}下载中',
				leave=False,
			) as progress_bar:
				num_bytes_downloaded = res.num_bytes_downloaded
				async for chunk in res.aiter_bytes():
					data += chunk
					progress_bar.update(res.num_bytes_downloaded - num_bytes_downloaded)
					num_bytes_downloaded = res.num_bytes_downloaded

		if md5 is not None and Hash(data).md5() != md5:
			raise httpx.HTTPError(f'MD5校验失败: {url}')

		return data

	async def download(
		self,
		url: 'URLTypes',
		filename: Path,
		*,
		method: Literal['GET', 'POST'] = 'GET',
		md5: str | None = None,
		postprocess_handler: DownloadPostProcessMethod | None = None,
		semaphore: anyio.Semaphore | None = None,
	):
		async with semaphore or self._semaphore:
			data = await self._get_data(url, method=method, md5=md5)
			if postprocess_handler is not None:
				data = postprocess_handler(data)

			filename.parent.mkdir(parents=True, exist_ok=True)
			async with aiofiles.open(filename, mode='wb') as f:
				await f.write(data)

	async def downloads(
		self,
		*params: DownloadParams,
		semaphore: anyio.Semaphore | None = None,
		progress_bar: tqdm | None = None,
		postprocess_handler: DownloadPostProcessMethod | None = None,
	) -> None:
		total = len(params)
		# 这里不能使用 or 表达式，因为 tqdm 的 total 属性还没有设置，
		# 此时调用 __bool__ 会报错
		pbar = (
			tqdm(total=total, desc='下载中', unit='file')
			if progress_bar is None
			else progress_bar
		)
		pbar.total = total
		with pbar:

			async def _handle(p: DownloadParams):
				await self.download(
					p.url,
					p.filename,
					method=p.method,
					md5=p.md5,
					postprocess_handler=postprocess_handler,
					semaphore=semaphore,
				)
				pbar.update()

			async with anyio.create_task_group() as tg:
				for param in params:
					tg.start_soon(_handle, param)
