#!/usr/bin/env python
"""基础资源更新示例

演示如何使用 Albi0 Python API 更新游戏资源。
"""

import asyncio

import albi0


async def main():
	# 使用上下文管理器自动管理资源
	async with albi0.session():
		# 1. 加载所需的插件
		print("加载 newseer 插件...")
		albi0.load_plugin('newseer')
		
		# 2. 查看可用的更新器
		updaters = albi0.list_updaters()
		print(f"可用的更新器：{list(updaters.keys())}")
		
		# 3. 检查远程版本
		print("\n检查远程版本...")
		remote_version = await albi0.get_remote_version('newseer.default')
		print(f"远程版本：{remote_version}")
		
		# 4. 更新资源
		print("\n开始更新资源...")
		await albi0.update_resources(
			'newseer.default',
			# '*.bundle',  # 可选：只更新特定文件模式
			working_dir='./game_data',  # 工作目录
			max_workers=10,  # 并发下载数
			ignore_version=False,  # 是否忽略版本检查
		)
		
		print("✅ 更新完成！")
	# 资源自动清理


if __name__ == '__main__':
	asyncio.run(main())

