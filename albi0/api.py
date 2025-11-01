"""Albi0 Python API

为 Albi0 提供简单易用的 Python 异步 API 接口，用于资源提取和更新。
"""

import glob
import importlib
import itertools
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
from tqdm.asyncio import tqdm

from albi0.extract.extractor import extractors
from albi0.log import logger
from albi0.request import client as httpx_client
from albi0.typing import PathTypes
from albi0.update.updater import updaters
from albi0.update.version import Manifest

if TYPE_CHECKING:
	from httpx import AsyncClient


# 插件管理
_loaded_plugins: set[str] = set()

AVAILABLE_PLUGINS = {
	'newseer': 'albi0.plugins.newseer',
	'seerproject': 'albi0.plugins.seerproject',
}


def load_plugin(plugin_name: str) -> None:
	"""加载指定的插件
	
	Args:
		plugin_name: 插件名称，如 'newseer' 或 'seerproject'
		
	Raises:
		ValueError: 当插件名称不存在时
	"""
	if plugin_name in _loaded_plugins:
		logger.debug(f'插件 {plugin_name} 已加载，跳过')
		return
	
	if plugin_name not in AVAILABLE_PLUGINS:
		available = ', '.join(AVAILABLE_PLUGINS.keys())
		raise ValueError(f'未知的插件：{plugin_name}。可用插件：{available}')
	
	module_path = AVAILABLE_PLUGINS[plugin_name]
	try:
		importlib.import_module(module_path)
		_loaded_plugins.add(plugin_name)
		logger.info(f'插件 {plugin_name} 加载成功')
	except Exception as e:
		logger.error(f'加载插件 {plugin_name} 失败：{e}')
		raise


def load_all_plugins() -> None:
	"""加载所有可用的插件"""
	for plugin_name in AVAILABLE_PLUGINS:
		try:
			load_plugin(plugin_name)
		except Exception as e:
			logger.warning(f'加载插件 {plugin_name} 时出错：{e}')


# 列出处理器
def list_extractors() -> dict[str, str]:
	"""列出所有已注册的提取器
	
	Returns:
		字典，键为提取器名称，值为提取器描述
	"""
	return {name: extractor.desc for name, extractor in extractors.items()}


def list_updaters() -> dict[str, str]:
	"""列出所有已注册的更新器
	
	Returns:
		字典，键为更新器名称，值为更新器描述
	"""
	return {name: updater.desc for name, updater in updaters.items()}


# 核心 API 函数
async def extract_assets(
	extractor_name: str = 'default',
	*patterns: str,
	output_dir: PathTypes = '.',
	merge_extract: bool = False,
	max_workers: int = 4,
	export_unknown_as_typetree: bool = True,
) -> None:
	"""异步提取 Unity 资源文件
	
	Args:
		extractor_name: 提取器名称或组名，默认为 'default'
		*patterns: 文件路径模式，支持 glob 语法，如 'path/to/*.bundle'
		output_dir: 输出目录路径
		merge_extract: 是否合并提取（将所有文件作为一个环境处理）
		max_workers: 并行处理的最大工作线程数
		export_unknown_as_typetree: 未知类型是否导出为 TypeTree
		
	Raises:
		ValueError: 当提取器不存在时
		
	Examples:
		>>> import asyncio
		>>> import albi0
		>>> 
		>>> async def main():
		...     albi0.load_plugin('newseer')
		...     # 使用默认提取器
		...     await albi0.extract_assets('data/*.bundle')
		...     
		...     # 指定提取器
		...     await albi0.extract_assets('newseer', 'data/*.bundle', output_dir='./output')
		>>> 
		>>> asyncio.run(main())
	"""
	# 处理文件路径模式
	if not patterns:
		raise ValueError('必须提供至少一个文件路径模式')
	
	ab_paths: set[Path] = {
		Path(path).resolve()
		for path in itertools.chain.from_iterable(map(glob.iglob, patterns))
	}
	
	if not ab_paths:
		logger.warning(f'没有找到匹配的文件：{patterns}')
		return
	
	# 获取提取器
	extractor_set = extractors.get_processors(extractor_name)
	if not extractor_set:
		raise ValueError(f'找不到提取器/组：{extractor_name}')
	
	# 执行提取
	for extractor in extractor_set:
		logger.info(f'运行提取器：{extractor.name}')
		try:
			extractor.extract_asset(
				*ab_paths,
				export_dir=Path(output_dir) / extractor_name if extractor_name != 'default' else output_dir,
				merge_extract=merge_extract,
				max_workers=max_workers,
				export_unknown_as_typetree=export_unknown_as_typetree,
			)
			logger.info(f'✅ {extractor.name} 提取完成')
		except Exception as e:
			logger.exception(f'❌ {extractor.name} 提取失败：{e}')
			raise


async def update_resources(
	updater_name: str,
	*patterns: str,
	working_dir: PathTypes | None = None,
	manifest_path: PathTypes | None = None,
	max_workers: int = 10,
	ignore_version: bool = False,
	save_manifest: bool = True,
) -> None:
	"""异步更新资源文件
	
	检查版本并下载需要更新的资源文件。
	
	Args:
		updater_name: 更新器名称或组名
		*patterns: 文件名过滤模式（glob 语法），如 '*.bundle'，为空则更新所有文件
		working_dir: 工作目录，资源将下载到此目录
		manifest_path: 自定义清单文件路径
		max_workers: 并发下载的最大数量
		ignore_version: 是否忽略版本号检查，仅比对资源清单
		save_manifest: 是否保存资源清单到本地
		
	Raises:
		ValueError: 当更新器不存在时
		
	Examples:
		>>> import asyncio
		>>> import albi0
		>>> 
		>>> async def main():
		...     albi0.load_plugin('newseer')
		...     await albi0.update_resources(
		...         'newseer.default',
		...         '*.bundle',
		...         working_dir='./game_data'
		...     )
		>>> 
		>>> asyncio.run(main())
	"""
	# 切换工作目录
	original_cwd = None
	if working_dir:
		original_cwd = os.getcwd()
		os.chdir(working_dir)
	
	try:
		# 获取更新器
		updater_set = updaters.get_processors(updater_name)
		if not updater_set:
			raise ValueError(f'找不到更新器/组：{updater_name}')
		
		# 执行更新
		for updater in updater_set:
			# 设置自定义清单路径
			if manifest_path:
				logger.info(f'使用自定义清单文件路径：{manifest_path}')
				updater.version_manager.local_manifest_path = str(manifest_path)
			
			logger.info(f'运行更新器：{updater.name}')
			
			# 检查版本
			local_version = updater.version_manager.load_local_version() if updater.version_manager.is_local_version_exists else '无'
			remote_version = updater.version_manager.get_remote_version()
			
			logger.info(f'本地版本：{local_version}')
			logger.info(f'远程版本：{remote_version}')
			
			if not updater.version_manager.is_version_outdated and not ignore_version:
				logger.info('版本最新，无需更新')
				continue
			
			logger.info('开始更新...')
			await updater.update(
				progress_bar=tqdm(desc='下载资源文件', unit='file'),
				patterns=patterns,
				semaphore=anyio.Semaphore(max_workers),
				save_manifest=save_manifest,
			)
			
			final_version = updater.version_manager.load_local_version()
			logger.info(f'✅ 更新完成！本地版本：{final_version}')
	
	finally:
		# 恢复原工作目录
		if original_cwd:
			os.chdir(original_cwd)


async def get_remote_version(updater_name: str) -> str:
	"""获取远程版本号
	
	Args:
		updater_name: 更新器名称
		
	Returns:
		远程版本号字符串
		
	Raises:
		ValueError: 当更新器不存在时
	"""
	updater = updaters.get(updater_name)
	if not updater:
		raise ValueError(f'找不到更新器：{updater_name}')
	
	return updater.version_manager.get_remote_version()


async def get_remote_manifest(updater_name: str) -> Manifest:
	"""获取远程清单
	
	Args:
		updater_name: 更新器名称
		
	Returns:
		Manifest: 远程清单
	"""
	updater = updaters.get(updater_name)
	if not updater:
		raise ValueError(f'找不到更新器：{updater_name}')
	
	return updater.version_manager.get_remote_manifest()

@asynccontextmanager
async def session(client: 'AsyncClient | None' = None):
	"""创建会话上下文，自动管理资源
	
	这是推荐的资源管理方式，使用 `async with` 语句自动清理资源。
	
	Args:
		client: 可选的 httpx.AsyncClient 实例。如果提供，将用于所有网络请求。
			如果为 None，使用默认的全局客户端。
			注意：自定义客户端会在上下文结束时自动关闭。
	
	Yields:
		None
	
	Examples:
		>>> # 使用默认配置
		>>> import albi0
		>>> 
		>>> async with albi0.session():
		...     albi0.load_plugin('newseer')
		...     await albi0.update_resources('newseer.default')
		
		>>> # 使用自定义客户端（配置超时、代理等）
		>>> from httpx import AsyncClient, Timeout
		>>> 
		>>> custom_client = AsyncClient(
		...     timeout=Timeout(60.0),
		...     proxies={"http://": "http://proxy:8080"},
		...     headers={"User-Agent": "MyApp/1.0"}
		... )
		>>> 
		>>> async with albi0.session(custom_client):
		...     albi0.load_plugin('newseer')
		...     await albi0.update_resources('newseer.default')
	"""
	from albi0 import request
	
	# 保存原客户端引用
	original_client = request.client
	custom_client_provided = client is not None
	
	if custom_client_provided:
		# 使用自定义客户端
		request.client = client
	
	try:
		yield  # 进入上下文
	finally:
		# 清理资源
		if custom_client_provided:
			# 关闭自定义客户端并恢复原客户端
			await request.client.aclose()
			request.client = original_client
		else:
			# 关闭默认客户端
			await request.client.aclose()


async def cleanup() -> None:
	"""清理资源，关闭 HTTP 客户端等
	
	注意：推荐使用 `async with albi0.session()` 上下文管理器替代手动调用此函数。
	此函数保留用于特殊场景和向后兼容。
	
	Examples:
		>>> # 不推荐：手动清理
		>>> try:
		...     await albi0.extract_assets('*.bundle')
		... finally:
		...     await albi0.cleanup()
		
		>>> # 推荐：使用上下文管理器
		>>> async with albi0.session():
		...     await albi0.extract_assets('*.bundle')
	"""
	await httpx_client.aclose()


__all__ = [
	'load_plugin',
	'load_all_plugins',
	'list_extractors',
	'list_updaters',
	'extract_assets',
	'update_resources',
	'get_remote_version',
	'session',
	'cleanup',
]

