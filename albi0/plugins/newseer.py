from typing import TYPE_CHECKING

from httpx import AsyncClient
from packaging.version import Version
from UnityPy.enums.ClassIDType import ClassIDType

from albi0.bytes_reader import BytesReader
from albi0.extract.extractor import Extractor
from albi0.extract.registry import AssetPostHandlerGroup, ObjPreHandlerGroup
from albi0.typing import ObjectPath
from albi0.update import Downloader, Updater
from albi0.updaters import YooVersionManager
from albi0.updaters.yoo_version_manager import (
	PackageAssetInfo,
	PackageBundleInfo,
	YooManifestParser,
)

if TYPE_CHECKING:
	from UnityPy.classes import Texture2D


headers = {
	'user-agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
	'referer': r'https://newseer.61.com',
}

downloader = Downloader(AsyncClient(headers=headers))

obj_pre = ObjPreHandlerGroup()
asset_post = AssetPostHandlerGroup()
Extractor(
	'newseer',
	'赛尔号资源提取器',
	asset_posthandler_group=asset_post,
	obj_prehandler_group=obj_pre,
)


@obj_pre.register(ClassIDType.Sprite)
@obj_pre.register(ClassIDType.Texture2D)
def texture2d_prehandler(
	obj: 'Texture2D', obj_path: ObjectPath
) -> tuple['Texture2D', ObjectPath]:
	if obj.image.mode == 'RGBA' and obj_path.suffix != '.png':
		obj_path = obj_path.with_suffix('.png')
	return obj, obj_path


class NewseerManifestParser(YooManifestParser):
	def _parse_asset_infos(
		self,
		reader: BytesReader,
		version: str,
		count: int,
	) -> list[PackageAssetInfo]:
		"""解析资源信息列表"""
		return [
			PackageAssetInfo(
				Address='',
				AssetPath=reader.text(),
				AssetGUID=None,
				AssetTags=[],
				BundleID=reader.int(),
				DependIDs=reader.int_list(),
			)
			for _ in range(count)
		]

	def _parse_bundle_list(
		self, reader: BytesReader, version: str, count: int
	) -> list[PackageBundleInfo]:
		"""解析Bundle列表"""
		return [
			PackageBundleInfo(
				BundleName=reader.text(),
				UnityCRC=reader.uint() if Version(version) > Version('1.5.1') else None,
				FileHash=reader.text(),
				FileCRC=reader.text(),
				FileSize=reader.long(),
				IsRawFile=reader.boolean(),
				LoadMethod=reader.byte(),
				Tags=[],
				ReferenceIDs=reader.int_list(),
			)
			for _ in range(count)
		]


Updater(
	'newseer.default',
	'赛尔号AB包下载器 DefaultPackage部分',
	version_manager=YooVersionManager(
		'DefaultPackage',
		remote_path='https://newseer.61.com/Assets/StandaloneWindows64/DefaultPackage/',
		local_path='./newseer/assetbundles/DefaultPackage/',
		manifest_factory=NewseerManifestParser(),
		version_factory=int,
	),
	downloader=downloader,
)


Updater(
	'newseer.config',
	'赛尔号AB包下载器 ConfigPackage部分',
	version_manager=YooVersionManager(
		'ConfigPackage',
		remote_path='https://newseer.61.com/Assets/StandaloneWindows64/ConfigPackage/',
		local_path='./newseer/assetbundles/ConfigPackage/',
		manifest_factory=NewseerManifestParser(),
		version_factory=int,
	),
	downloader=downloader,
)


Updater(
	'newseer.pet',
	'赛尔号AB包下载器 PetAnimPackage部分',
	version_manager=YooVersionManager(
		'PetAnimPackage',
		remote_path='https://newseer.61.com/Assets/StandaloneWindows64/PetAnimPackage/',
		local_path='./newseer/assetbundles/PetAnimPackage/',
		manifest_factory=NewseerManifestParser(),
		version_factory=int,
	),
	downloader=downloader,
)


Updater(
	'newseer.startup',
	'赛尔号AB包下载器 StartupPackage部分',
	version_manager=YooVersionManager(
		'StartupPackage',
		remote_path='https://newseer.61.com/Assets/StandaloneWindows64/StartupPackage/',
		local_path='./newseer/assetbundles/StartupPackage/',
		manifest_factory=NewseerManifestParser(),
		version_factory=int,
	),
	downloader=downloader,
)
