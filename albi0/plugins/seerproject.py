from contextlib import suppress
import gzip
from pathlib import Path
from typing import TYPE_CHECKING

import orjson
from slpp import slpp
from UnityPy.classes import PPtr
from UnityPy.enums.ClassIDType import ClassIDType

from albi0.extract import Extractor
from albi0.extract.registry import (
	AssetPostHandlerGroup,
	ObjPreHandlerGroup,
	StopExtractThisObject,
)
from albi0.typing import ObjectPath
from albi0.update import Downloader, Updater
from albi0.update.version import LocalFileName, Manifest, ManifestItem
from albi0.updaters import YooVersionManager
from albi0.updaters.yoo_version_manager import PackageManifest
from albi0.utils import join_path, join_url, remove_all_suffixes

if TYPE_CHECKING:
	from UnityPy.classes import TextAsset, Texture2D
	from UnityPy.files.ObjectReader import ObjectReader


def load_lua_table(data: str):
	"""加载lua数据为Python object"""
	start = data.find('{')
	return slpp.decode(data[start:] if start != -1 else data)


def default_decryption_method(data: memoryview):
	if data[:32] == b'\00' * 32:
		return data[32:]

	return data


class SeerProjectVersionManager(YooVersionManager):
	def _simplify_manifest(self, data: PackageManifest) -> Manifest:
		version = data['PackageVersion']
		items = {}
		for item in data['BundleList']:
			local_basename = item['BundleName']
			remote_filehash = item['FileHash']
			local_fn = LocalFileName(join_path(self.local_path, local_basename))
			items[local_fn] = ManifestItem(
				f'{join_url(self.remote_path, remote_filehash)}.bundle',
				f'{local_basename}.bundle',
				remote_filehash.encode(),
				item['FileSize'],
			)
		return Manifest(version=version, items=items)


obj_pre = ObjPreHandlerGroup()
asset_post = AssetPostHandlerGroup()
Extractor(
	'seerproject',
	'赛尔计划资源提取器',
	decryption_method=default_decryption_method,
	asset_posthandler_group=asset_post,
	obj_prehandler_group=obj_pre,
)


@asset_post.register()
def non_bundle_package_handler(obj: 'ObjectReader', export_dir: Path):
	assets_file = obj.assets_file
	container = assets_file.container
	if (
		len(values := container.values()) == 1
		and isinstance(values[0], PPtr)
		and Path(filename := container.keys()[0]).suffix in ('.unity', '.prefab')
	):
		export_filename: Path = Path(export_dir, filename)
		export_filename.parent.mkdir(parents=True, exist_ok=True)
		export_filename.write_bytes(assets_file.save(packer='original'))
		raise StopExtractThisObject

	return obj, export_dir


@obj_pre.register(ClassIDType.TextAsset)
def textasset_prehandler(
	obj: 'TextAsset', obj_path: ObjectPath
) -> tuple['TextAsset', ObjectPath]:
	suffix = '.txt'
	if len(suffixes := obj_path.suffixes):
		if suffixes[0] in ('.atlas', '.skel'):
			suffix = suffixes[0]

	script = obj.m_Script.encode('utf-8', 'surrogateescape')
	with suppress(gzip.BadGzipFile):
		script = gzip.decompress(script)

	if obj_path.is_relative_to('Assets/Game/Lua/'):
		suffix = '.lua'
		text = script.decode()

		if obj_path.parts[-2] == 'data':
			suffix = '.json'
			lua_table = ''.join(text.splitlines()[:-1])  # 删除最后一行
			script = orjson.dumps(
				load_lua_table(lua_table),
				option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS,
			)

	obj.m_Script = script.decode('utf-8', 'surrogateescape')

	obj_path = remove_all_suffixes(obj_path).with_suffix(suffix)
	return obj, obj_path


@obj_pre.register(ClassIDType.Sprite)
@obj_pre.register(ClassIDType.Texture2D)
def texture2d_prehandler(
	obj: 'Texture2D', obj_path: ObjectPath
) -> tuple['Texture2D', ObjectPath]:
	if obj.image.mode == 'RGBA' and obj_path.suffix != '.png':
		obj_path = obj_path.with_suffix('.png')
	return obj, obj_path


Updater(
	'seerproject.ab',
	'赛尔计划AB包下载器',
	version_manager=SeerProjectVersionManager(
		'SpPackage',
		remote_path='https://sp.61.com/source/taomee/Android/',
		local_path='./seerproject/assetbundles',
	),
	downloader=Downloader(),
)
