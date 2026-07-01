<div align="center">

# Albi0
~~[摸鱼的图书馆管理员](https://wiki.biligame.com/seerplan/%E9%98%BF%E5%B0%94%E6%AF%94%E9%9B%B6)~~<br>
🟨插件化的 Unity 游戏资源更新与提取工具🟩

</div>

## 功能特性

- 插件化：通过插件系统以支持多个游戏客户端，并提供了抽象的 manifest 版本管理器接口，便于支持热更逻辑
- 异步下载：基于 `httpx`、`anyio` 与 `tqdm` 的高速并发下载与实时进度显示
- 灵活筛选：支持按文件名 glob 模式与文件尺寸范围过滤需要下载的资源

## 已支持的游戏

- [赛尔计划](https://www.biligame.com/detail/?id=107861)
- [赛尔号 Unity 端](https://seer.61.com/)

## 安装

Albi0 提供两种使用方式：**CLI 命令行工具** 和 **Python API**。

### 使用 CLI（推荐使用 uvx）

推荐使用 `uvx` 直接运行，无需本地安装依赖，但需要先安装 `uv`，[uv 安装文档](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# 直接运行（无需安装）
uvx albi0 --help
```

### 使用 Python API

```bash
# 使用 pip 安装
pip install albi0

# 或使用 uv
uv add albi0
```

## 快速开始

### CLI 快速开始

1) 列出可用的更新器与提取器：

```bash
uvx albi0 list
```

2) 更新远程资源（示例：下载赛尔计划 AB 包）：

```bash
# 可选：切换工作目录（默认当前目录）
uvx albi0 update -n newseer.default -w ./newseer

# 仅下载指定尺寸范围内的资源（支持纯字节数或 K/M/G 后缀）
uvx albi0 update -n newseer.default --min-size 100K --max-size 5M '*.bundle'
```

3) 仅查看远程版本号（不下载资源）：

```bash
uvx albi0 update -n newseer.default --version-only
```

4) 提取资源（AB 文件 → 本地目录）：
```bash
# 使用指定提取器提取（按组名/名称）
uvx albi0 extract -n newseer "./path/to/*.ab" -o ./output

# 合并模式（将多个源文件合并为一个环境后再导出）
uvx albi0 extract -n seerproject -m "./assets/**/*.ab" -o ./out

# 原样导出（忽略自定义处理，使用默认提取器）
uvx albi0 extract -e "./raw/*.ab" -o ./raw_out
```

提示：导出路径会自动带上提取器名前缀，例如传入 `-n newseer -o ./output`，实际导出目录为 `./output/newseer/...`。

### Python API 快速开始

```python
import asyncio
import albi0

async def main():
    # 使用上下文管理器自动管理资源
    async with albi0.session():
        # 1. 加载插件
        albi0.load_plugin('newseer')
        
        # 2. 提取资源
        await albi0.extract_assets(
            'newseer',
            'path/to/*.bundle',
            output_dir='./output',
        )
        
        # 3. 更新资源
        await albi0.update_resources(
            'newseer.default',
            working_dir='./game_data',
            min_size='100K',
            max_size='5M',
        )
    # 资源自动清理

asyncio.run(main())
```

更多示例请参考 [examples/](./examples/) 目录。

## CLI 参考

### 顶层命令

```bash
uvx albi0 --help
uvx albi0 list
uvx albi0 update -n <updater_name> [-w WORKING_DIR] [-s LIMIT] [--min-size SIZE] [--max-size SIZE] [--version-only] [PATTERNS...]
uvx albi0 extract [OPTIONS] [-t THREADS] [PATTERNS...]
```

### list

- 说明：打印已注册的更新器与提取器（来自已导入的插件）

### update

- 必选参数：`-n, --updater-name` 指定更新器名称或组名（可用名称见 `list` 输出）
- 可选参数：
  - `-w, --working-dir` 切换执行时的工作目录
  - `-s, --semaphore-limit` 最大并发下载数（默认 10）
  - `--min-size` 最小文件尺寸（含），支持纯字节数或 K/M/G 后缀，如 `1048576`、`1M`
  - `--max-size` 最大文件尺寸（含），支持纯字节数或 K/M/G 后缀，如 `5242880`、`5M`
  - `--version-only` 仅获取远程版本号，不下载资源文件
- 位置参数：`PATTERNS...` 可选的文件名过滤模式（glob 语法），用于仅更新匹配的清单项
- 行为：
  - 对比远程与本地资源清单，若需要更新则并发下载资源文件并保存清单
  - 进度条展示每个文件的下载进度与总体任务进度
  - 当传入 `--version-only` 时，仅打印远程版本号并退出，不进行下载
  - 当提供 `PATTERNS...` 时，仅会下载文件名匹配 `PATTERNS...` 的条目
  - 当提供 `--min-size` / `--max-size` 时，仅会下载远程清单中尺寸落在指定范围内的条目；尺寸信息来自远程 manifest，无需额外 HTTP 请求
  - 尺寸过滤可与 `PATTERNS...` 组合使用；纯数字视为字节，带 `K`/`M`/`G` 后缀按 1024 进制解析

### extract

- 可选参数：
  - `-o, --output-dir` 导出目录（默认当前目录）
  - `-n, --extractor-name` 提取器名称或组名（默认 `default`）
  - `-e, --export-as-is` 原样导出（强制使用默认提取器）
  - `-m, --merge-extract` 合并模式（先合并环境再导出）
  - `-t, --parallel-threads` 并行处理使用的线程数，可根据 CPU 核心数调整（默认 4）
- 位置参数：`PATTERNS...` 资源文件的 glob 模式（如 `"./**/*.ab"`）
- 行为：
  - 依次加载匹配到的资源文件，调用插件注册的处理器进行导出
  - 在对象导出前后，可由插件的前/后处理器自定义处理逻辑

## 插件体系概览

- 提取器（Extractor）：在插件模块中通过构造 `Extractor()` 即完成注册
- 更新器（Updater）：在插件模块中通过构造 `Updater()` 即完成注册
- 分组机制：名称支持点号分组，例如 `newseer.default`、`seerproject.ab`；在 CLI 中传入组名可批量执行同组组件

## 典型工作流

### CLI 工作流

```bash
# 1. 查看可用组件
uvx albi0 list

# 2. 下载（或更新）远程资源
uvx albi0 update -n newseer.default -w ./workspace

# 仅下载匹配的资源（使用 glob 过滤）
uvx albi0 update -n newseer.default "*.builtin" "Shader/*"

# 仅下载指定尺寸范围内的资源
uvx albi0 update -n newseer.default --min-size 1M --max-size 10M "*.bundle"

# 调整并发数下载
uvx albi0 update -n newseer.default -s 20

# 3. 提取资源到本地
uvx albi0 extract -n newseer "./workspace/newseer/assetbundles/**/*.ab" -m -o ./exports

# 使用多线程加速提取
uvx albi0 extract -n newseer "./workspace/newseer/assetbundles/**/*.ab" -m -o ./exports -t 8
```

### Python API 工作流

```python
import asyncio
import albi0

async def main():
    # 使用上下文管理器自动管理资源
    async with albi0.session():
        # 1. 加载插件
        albi0.load_plugin('newseer')
        
        # 2. 查看可用组件
        print("提取器：", list(albi0.list_extractors().keys()))
        print("更新器：", list(albi0.list_updaters().keys()))
        
        # 3. 更新资源
        await albi0.update_resources(
            'newseer.default',
            '*.builtin', 'Shader/*',  # 过滤特定文件
            working_dir='./workspace',
            max_workers=20,           # 并发数
            min_size='1M',           # 最小文件尺寸
            max_size='10M',           # 最大文件尺寸
        )
        
        # 4. 提取资源
        await albi0.extract_assets(
            'newseer',
            './workspace/newseer/assetbundles/**/*.ab',
            output_dir='./exports',
            merge_extract=True,
            max_workers=8  # 线程数
        )
    # 资源自动清理

asyncio.run(main())
```

## Python API 参考

Albi0 提供了简单易用的 Python API，支持以下功能：

### 插件管理

```python
# 加载单个插件
albi0.load_plugin('newseer')

# 加载所有插件
albi0.load_all_plugins()

# 列出可用处理器
extractors = albi0.list_extractors()  # dict[str, str]
updaters = albi0.list_updaters()      # dict[str, str]
```

### 资源提取

```python
await albi0.extract_assets(
    extractor_name,                 # 提取器名称
    *patterns,                      # 文件路径模式（支持 glob）
    output_dir='.',                 # 输出目录
    merge_extract=False,            # 是否合并提取（将所有文件作为一个环境处理）
    max_workers=4,                  # 并行处理的最大工作线程数
    export_unknown_as_typetree=True # 未知类型是否导出为 TypeTree
)
```

### 资源更新

```python
await albi0.update_resources(
    updater_name,                   # 更新器名称（必需）
    *patterns,                      # 文件过滤模式（可选）
    working_dir=None,               # 工作目录
    manifest_path=None,             # 自定义清单路径
    max_workers=10,                 # 并发下载数
    timeout=None,                   # 单文件下载超时（秒）
    ignore_version=False,           # 是否忽略版本检查
    save_manifest=True,             # 是否保存清单
    min_size=None,                  # 最小文件尺寸，支持纯字节数或 K/M/G 后缀
    max_size=None,                  # 最大文件尺寸，支持纯字节数或 K/M/G 后缀
)

# 获取远程版本
version = await albi0.get_remote_version('newseer.default')
```

### 资源管理

```python
# 推荐：使用上下文管理器（自动清理）
async with albi0.session():
    await albi0.extract_assets('newseer', '*.bundle')
    await albi0.update_resources('newseer.default')
# 资源自动清理

# 高级：使用自定义 HTTP 客户端（配置超时、代理等）
from httpx import AsyncClient, Timeout

custom_client = AsyncClient(
    timeout=Timeout(60.0),
    proxies={"http://": "http://proxy:8080"},
    headers={"User-Agent": "MyApp/1.0"}
)

async with albi0.session(custom_client):
    await albi0.update_resources('newseer.default')
# 自定义客户端自动关闭

# 向后兼容：手动清理（不推荐）
try:
    await albi0.extract_assets('newseer', '*.bundle')
finally:
    await albi0.cleanup()
```

### 高级用法：访问核心类

```python
from albi0 import (
    Extractor,              # 资源提取器
    Updater,                # 资源更新器
    Downloader,             # 下载器
    AbstractVersionManager, # 版本管理器基类
)

# 创建自定义提取器
custom_extractor = Extractor(
    'my_custom',
    '自定义提取器',
    # 可添加自定义处理器
)

# 创建自定义更新器
custom_updater = Updater(
    'my_custom',
    '自定义更新器',
    version_manager=MyVersionManager(...),
    downloader=Downloader(...),
)
```

### API 与 CLI 对比

| 功能 | CLI 命令 | Python API |
|-----|---------|-----------|
| 提取资源 | `albi0 extract -n newseer *.bundle` | `await albi0.extract_assets('newseer', '*.bundle')` |
| 更新资源 | `albi0 update -n newseer.default` | `await albi0.update_resources('newseer.default')` |
| 按尺寸筛选下载 | `albi0 update -n newseer.default --min-size 1M --max-size 5M` | `await albi0.update_resources('newseer.default', min_size='1M', max_size='5M')` |
| 列出处理器 | `albi0 list` | `albi0.list_extractors()` / `albi0.list_updaters()` |
| 插件加载 | ✅ 自动加载 | ❌ 需手动调用 `load_plugin()` |

### 注意事项

1. **异步接口**：所有 API 函数都是异步的，需要使用 `await` 调用
2. **插件加载**：使用 API 前需要先加载相应的插件（CLI 会自动加载）
3. **资源管理**：推荐使用 `async with albi0.session()` 自动管理资源，支持传入自定义 HTTP 客户端
4. **错误处理**：API 函数会抛出异常，建议使用 try-except 处理

更多详细示例和文档，请参考：
- [examples/](./examples/) - 使用示例
- [examples/README.md](./examples/README.md) - 示例文档

## 开发流程

项目使用 `uv` 进行依赖管理与构建：

```bash
# 克隆仓库
git clone https://github.com/SeerAPI/albi0.git

# 安装依赖（包含开发/测试依赖）
uv sync

# 本地运行 CLI
uv run albi0 --help

# 运行测试，暂时还没写
# uv run --group test pytest

# 构建发行包
uv build
```

## 常见问题（FAQ）

### CLI 相关
- Q: 为什么没有看到我新写的插件生效？
  - A: CLI 会自动加载所有插件。确保插件模块在 `albi0/plugins/` 目录中，并且在 `albi0/cli/__init__.py` 中被导入。
- Q: 下载很慢/失败？
  - A: 默认并发数是 10，对于某些网络环境或服务器限制可能不是最优。可以尝试使用 `-s` 或 `--semaphore-limit` 选项减少并发数，例如 `-s 5`。如果问题仍然存在，可能需要检查网络或考虑使用代理。
- Q: 如何只下载特定大小的资源文件？
  - A: 使用 `--min-size` 和/或 `--max-size` 参数。尺寸支持纯字节数（如 `5242880`）或带 K/M/G 后缀的可读格式（如 `100K`、`5M`）。例如：`uvx albi0 update -n newseer.default --min-size 1M --max-size 10M`。Python API 中对应参数为 `min_size` 和 `max_size`。
- Q: 导出结果的格式不符合预期？
  - A: 检查对应插件的对象前处理器与资源后处理器逻辑，或使用 `-e/--export-as-is` 原样导出。

### Python API 相关
- Q: 为什么插件没有生效？
  - A: Python API 需要手动加载插件，使用 `albi0.load_plugin('plugin_name')` 或 `albi0.load_all_plugins()`。
- Q: 如何自定义 HTTP 客户端（配置超时、代理等）？
  - A: 使用 `session()` 上下文管理器传入自定义客户端：
  ```python
  from httpx import AsyncClient, Timeout
  
  client = AsyncClient(
      timeout=Timeout(60.0),
      proxies={"http://": "http://proxy:8080"}
  )
  
  async with albi0.session(client):
      await albi0.update_resources('newseer.default')
  ```
- Q: 如何处理异常？
  - A: API 函数会抛出异常，建议使用 try-except 处理：
  ```python
  async with albi0.session():
      try:
          await albi0.update_resources('newseer.default')
      except ValueError as e:
          print(f"配置错误：{e}")
      except Exception as e:
          print(f"发生错误：{e}")
  ```

## 目录结构（简要）

```
albi0/
├── api.py               # Python API 入口
├── __init__.py          # 包初始化，暴露 API
├── cli/                 # CLI 命令系统
│   ├── commands/        # 具体命令实现
│   └── __init__.py      # CLI 主框架
├── plugins/             # 插件系统
│   ├── seerproject.py   # 赛尔号Unity端插件
│   └── newseer.py       # 赛尔计划插件
├── extract/             # 资源提取核心
│   ├── extractor.py     # 提取器实现
│   └── registry.py      # 提取器注册表
├── update/              # 更新功能模块
│   ├── downloader.py    # 下载器实现
│   ├── updater.py       # 更新器实现
│   └── version.py       # 版本管理器实现
├── bytes_reader.py      # 字节流读取工具
├── utils.py             # 通用工具函数
├── typing.py            # 类型定义
├── log.py               # 日志配置
├── container.py         # 插件容器
└── request.py           # httpx 客户端封装

examples/                # Python API 使用示例
├── README.md            # 示例文档
├── basic_extract.py     # 基础提取示例
├── basic_update.py      # 基础更新示例
└── advanced_usage.py    # 高级用法示例
```

## 许可证

MIT
