#!/usr/bin/env python
"""基础资源提取示例

演示如何使用 Albi0 Python API 提取 Unity 资源包。
"""

import asyncio

import albi0


async def main():
	# 使用上下文管理器自动管理资源
	async with albi0.session():
		# 1. 加载所需的插件
		print("加载 newseer 插件...")
		albi0.load_plugin('newseer')
		
		# 2. 查看可用的提取器
		extractors = albi0.list_extractors()
		print(f"可用的提取器：{list(extractors.keys())}")
		
		# 3. 提取资源
		# 注意：请替换为实际的资源文件路径
		print("\n开始提取资源...")
		await albi0.extract_assets(
			'newseer',
			'path/to/assetbundle/*.bundle',  # 支持 glob 模式
			output_dir='./output',
			max_workers=4,  # 并行处理线程数
		)
		
		print("✅ 提取完成！")
	# 资源自动清理


if __name__ == '__main__':
	asyncio.run(main())

