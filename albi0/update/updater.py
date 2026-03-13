from collections.abc import Iterable
from pathlib import Path

import anyio
import click
from tqdm.asyncio import tqdm

from albi0.container import ProcessorContainer
from albi0.typing import DownloadPostProcessMethod

from .downloader import Downloader, DownloadParams
from .version import AbstractVersionManager

updaters: ProcessorContainer['Updater'] = ProcessorContainer()


class Updater:
	def __init__(
		self,
		name: str,
		desc: str,
		*,
		version_manager: AbstractVersionManager,
		downloader: Downloader,
		postprocess_handler: DownloadPostProcessMethod | None = None,
	) -> None:
		self.name = name
		self.desc = desc
		self.version_manager = version_manager
		self.downloader = downloader
		self.postprocess_handler = postprocess_handler

		updaters[self.name] = self

	def _log_message(self, message: str) -> None:
		click.echo(f'更新器|[{self.name}]: {message}')

	async def update(
		self,
		*,
		progress_bar: tqdm | None = None,
		save_manifest: bool = True,
		patterns: Iterable[str] = (),
		semaphore: anyio.Semaphore | None = None,
		timeout: float | None = None,
	) -> None:
		"""异步更新资源文件

		检查版本是否过期，如果需要更新则下载新的资源文件并保存清单，过滤后没有需要更新的文件时不会保存清单。

		Args:
			progress_bar: 进度条
			semaphore: 并发限制
			save_manifest: 是否保存清单
			patterns: glob语法的文件名过滤模式，用于过滤希望检查更新的文件，
			如果为空则检查所有文件。
			timeout: 单个文件下载超时时间（秒），None 表示不限制
		"""
		manifest = self.version_manager.generate_update_manifest(*patterns)
		if not manifest:
			self._log_message('没有需要更新的文件，运行结束')
			return

		items = manifest.items
		self._log_message(f'需要更新的文件数量: {len(items)}')
		tasks = [
			DownloadParams(url=item.remote_filename, filename=Path(local_fn))
			for local_fn, item in items.items()
		]
		if tasks:
			await self.downloader.downloads(
				*tasks,
				progress_bar=progress_bar,
				postprocess_handler=self.postprocess_handler,
				semaphore=semaphore,
				timeout=timeout,
			)

		if not tasks:
			self._log_message('没有需要更新的文件，不保存资源清单')
			return

		if not save_manifest:
			self._log_message('参数save_manifest为False，不保存资源清单')
			return

		self.version_manager.save_manifest_to_local(manifest)
		self._log_message('资源清单更新完成')
