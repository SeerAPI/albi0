#!/usr/bin/env python
"""高级用法示例

演示如何直接使用 Albi0 的核心类创建自定义提取器和更新器。
"""

import asyncio

import albi0
from albi0 import Extractor


async def custom_extractor_example():
	"""自定义提取器示例"""
	print("=" * 60)
	print("自定义提取器示例")
	print("=" * 60)
	
	# 创建自定义提取器
	custom_extractor = Extractor(
		'custom',
		'自定义提取器示例',
		# 可以添加自定义的解密方法、处理器等
		# decryption_method=my_decrypt_func,
		# asset_posthandler_group=my_asset_handlers,
		# obj_prehandler_group=my_obj_handlers,
		# export_handler_group=my_export_handlers,
	)
	
	print(f"创建了提取器：{custom_extractor.name}")
	print(f"描述：{custom_extractor.desc}")
	
	# 提取器会自动注册到全局容器
	print(f"已注册的提取器：{list(albi0.list_extractors().keys())}")


async def batch_update_example():
	"""批量更新多个包示例"""
	print("\n" + "=" * 60)
	print("批量更新示例")
	print("=" * 60)
	
	# 加载插件
	albi0.load_plugin('newseer')
	
	# 定义要更新的包和对应的文件模式
	update_tasks = [
		('newseer.default', ['*.bundle']),
		('newseer.config', ['config_*.json']),
		('newseer.pet', ['pet_*.bundle']),
	]
	
	for updater_name, patterns in update_tasks:
		print(f"\n更新 {updater_name}...")
		try:
			await albi0.update_resources(
				updater_name,
				*patterns,
				working_dir='./game_data',
				max_workers=5,
			)
			print(f"✅ {updater_name} 更新完成")
		except Exception as e:
			print(f"❌ {updater_name} 更新失败：{e}")


async def merge_extract_example():
	"""合并提取示例"""
	print("\n" + "=" * 60)
	print("合并提取示例")
	print("=" * 60)
	
	albi0.load_plugin('newseer')
	
	# 合并提取：将多个资源包作为一个整体环境处理
	# 这对于有依赖关系的资源包很有用
	await albi0.extract_assets(
		'newseer',
		'path/to/bundle1.bundle',
		'path/to/bundle2.bundle',
		'path/to/bundle3.bundle',
		output_dir='./merged_output',
		merge_extract=True,  # 开启合并提取
		max_workers=4,
	)
	
	print("✅ 合并提取完成")


async def list_all_processors():
	"""列出所有可用处理器"""
	print("\n" + "=" * 60)
	print("所有可用处理器")
	print("=" * 60)
	
	# 加载所有插件
	albi0.load_all_plugins()
	
	print("\n提取器：")
	for name, desc in albi0.list_extractors().items():
		print(f"  • {name}: {desc}")
	
	print("\n更新器：")
	for name, desc in albi0.list_updaters().items():
		print(f"  • {name}: {desc}")


async def custom_client_example():
	"""自定义 HTTP 客户端示例"""
	print("\n" + "=" * 60)
	print("自定义 HTTP 客户端示例")
	print("=" * 60)
	
	from httpx import AsyncClient, Timeout
	
	# 创建自定义客户端（配置超时、代理等）
	custom_client = AsyncClient(
		timeout=Timeout(connect=10.0, read=60.0, write=30.0, pool=5.0),
		# proxies={"http://": "http://proxy:8080"},  # 代理配置
		headers={"User-Agent": "MyApp/1.0"},
		follow_redirects=True,
	)
	
	print("使用自定义客户端（超时配置、自定义 UA）")
	
	# 在上下文管理器中使用自定义客户端
	async with albi0.session(custom_client):
		albi0.load_plugin('newseer')
		print("自定义客户端已设置，可以进行网络请求...")
		# await albi0.update_resources('newseer.default')
	
	print("✅ 自定义客户端已自动关闭")


async def main():
	"""运行所有示例"""
	# 使用上下文管理器自动管理资源
	async with albi0.session():
		await custom_extractor_example()
		await list_all_processors()
		# await batch_update_example()  # 需要实际的资源文件
		# await merge_extract_example()  # 需要实际的资源文件
	
	# 演示自定义客户端用法
	await custom_client_example()
	
	print("\n" + "=" * 60)
	print("✅ 所有示例运行完成")
	print("=" * 60)


if __name__ == '__main__':
	asyncio.run(main())

