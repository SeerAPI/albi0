"""
字节数组读写工具类
"""

from enum import Enum
import struct


class Writer:
	"""字节写入工具类"""

	@staticmethod
	def byte(value: int) -> bytes:
		"""写入单字节"""
		return bytes([value])

	@staticmethod
	def short(value: int, little_endian: bool = True) -> bytes:
		"""写入有符号 16 位整数"""
		format_str = '<h' if little_endian else '>h'
		return struct.pack(format_str, value)

	@staticmethod
	def ushort(value: int, little_endian: bool = True) -> bytes:
		"""写入无符号 16 位整数"""
		format_str = '<H' if little_endian else '>H'
		return struct.pack(format_str, value)

	@staticmethod
	def int(value: int, little_endian: bool = True) -> bytes:
		"""写入有符号 32 位整数"""
		format_str = '<i' if little_endian else '>i'
		return struct.pack(format_str, value)

	@staticmethod
	def uint(value: 'int', little_endian: bool = True) -> bytes:
		"""写入无符号 32 位整数"""
		format_str = '<I' if little_endian else '>I'
		return struct.pack(format_str, value)

	@staticmethod
	def long(value: 'int', little_endian: bool = True) -> bytes:
		"""写入有符号 64 位整数"""
		format_str = '<q' if little_endian else '>q'
		return struct.pack(format_str, value)

	@staticmethod
	def ulong(value: 'int', little_endian: bool = True) -> bytes:
		"""写入无符号 64 位整数"""
		format_str = '<Q' if little_endian else '>Q'
		return struct.pack(format_str, value)

	@staticmethod
	def float(value: float, little_endian: bool = True) -> bytes:
		"""写入 32 位浮点数"""
		format_str = '<f' if little_endian else '>f'
		return struct.pack(format_str, value)

	@staticmethod
	def double(value: 'float', little_endian: bool = True) -> bytes:
		"""写入 64 位浮点数"""
		format_str = '<d' if little_endian else '>d'
		return struct.pack(format_str, value)

	@staticmethod
	def text(value: str) -> bytes:
		"""写入文本字符串"""
		return value.encode('utf-8')


class LengthType(Enum):
	"""长度类型枚举"""

	BYTE = 0
	UINT16 = 1
	UINT32 = 2


class GlobalLengthType:
	"""全局长度类型设置"""

	value = LengthType.BYTE


class BytesReader:
	"""字节数组读取器"""

	def __init__(
		self,
		data: bytes,
		length_type: LengthType = GlobalLengthType.value,
		little_endian: bool = True,
	) -> None:
		"""
		初始化字节读取器

		Args:
			data: 要读取的字节数据
			length_type: 字符串长度前缀类型，默认使用全局设置
			little_endian: 是否使用小端字节序，默认为 True

		"""
		self.data = data
		self.offset = 0
		self.length_type = length_type
		self.little_endian = little_endian

	def seek(self, length: int, tag: str = ''):
		"""移动读取位置"""
		self.offset += length

	def set_offset(self, offset: int = 0):
		"""设置读取位置"""
		self.offset = offset

	def read(self, length: int | None = None, tag: str = '') -> bytes:
		"""读取指定长度的字节"""
		if length is not None:
			slice_data = self.data[self.offset : self.offset + length]
			self.seek(length, tag)
		else:
			# 读取到末尾
			slice_data = self.data[self.offset :]
			self.offset = len(self.data)
		return slice_data

	def text(self) -> str:
		"""读取带长度前缀的文本字符串"""
		if self.length_type == LengthType.BYTE:
			length = self.byte()
		elif self.length_type == LengthType.UINT16:
			length = self.ushort()
		elif self.length_type == LengthType.UINT32:
			length = self.uint()
		else:
			raise ValueError(f'Invalid length type: {self.length_type}')

		if length > 0:
			return self.read(length).decode('utf-8')
		else:
			return ''

	def boolean(self) -> bool:
		"""读取布尔值"""
		return bool(self.byte())

	def byte(self) -> int:
		"""读取单字节"""
		value = self.data[self.offset]
		self.offset += 1
		return value

	def short(self, little_endian: bool | None = None) -> int:
		"""读取有符号 16 位整数"""
		if little_endian is None:
			little_endian = self.little_endian
		data = self.read(2)
		format_str = '<h' if little_endian else '>h'
		return struct.unpack(format_str, data)[0]

	def ushort(self, little_endian: bool | None = None) -> int:
		"""读取无符号 16 位整数"""
		if little_endian is None:
			little_endian = self.little_endian
		data = self.read(2)
		format_str = '<H' if little_endian else '>H'
		return struct.unpack(format_str, data)[0]

	def int(self, little_endian: bool | None = None) -> int:
		"""读取有符号 32 位整数"""
		if little_endian is None:
			little_endian = self.little_endian
		data = self.read(4)
		format_str = '<i' if little_endian else '>i'
		return struct.unpack(format_str, data)[0]

	def uint(self, little_endian: bool | None = None) -> 'int':
		"""读取无符号 32 位整数"""
		if little_endian is None:
			little_endian = self.little_endian
		data = self.read(4)
		format_str = '<I' if little_endian else '>I'
		return struct.unpack(format_str, data)[0]

	def long(self, little_endian: bool | None = None) -> 'int':
		"""读取有符号 64 位整数"""
		if little_endian is None:
			little_endian = self.little_endian
		data = self.read(8)
		format_str = '<q' if little_endian else '>q'
		return struct.unpack(format_str, data)[0]

	def ulong(self, little_endian: bool | None = None) -> 'int':
		"""读取无符号 64 位整数"""
		if little_endian is None:
			little_endian = self.little_endian
		data = self.read(8)
		format_str = '<Q' if little_endian else '>Q'
		return struct.unpack(format_str, data)[0]

	def float(self, little_endian: bool | None = None) -> float:
		"""读取 32 位浮点数"""
		if little_endian is None:
			little_endian = self.little_endian
		data = self.read(4)
		format_str = '<f' if little_endian else '>f'
		return struct.unpack(format_str, data)[0]

	def double(self, little_endian: bool | None = None) -> 'float':
		"""读取 64 位浮点数"""
		if little_endian is None:
			little_endian = self.little_endian
		data = self.read(8)
		format_str = '<d' if little_endian else '>d'
		return struct.unpack(format_str, data)[0]

	def text_list(self) -> list[str]:
		"""读取带长度前缀的文本列表"""
		length = self.ushort()
		return [self.text() for _ in range(length)]

	def int_list(self) -> list['int']:
		"""读取带长度前缀的有符号 32 位整数列表"""
		length = self.ushort()
		return [self.int() for _ in range(length)]


# 类型定义
BytesStructSchema = list[bool | int | str | tuple | bytes | None]


class BundleOptions:
	"""打包选项"""

	def __init__(
		self,
		with_length: bool = True,
		length_type: LengthType = GlobalLengthType.value,
		little_endian: bool = True,
	):
		self.with_length = with_length
		self.length_type = length_type
		self.little_endian = little_endian


def bundle_bytes_struct(
	writer: Writer, schema: BytesStructSchema, tag: str = ''
) -> bytes:
	"""
	将结构化数据打包成字节数组

	Args:
		writer: 写入器
		schema: 数据结构模式
		tag: 标签，用于调试输出

	Returns:
		打包后的字节数组
	"""
	# 过滤掉 None 和 undefined
	schema = [s for s in schema if s is not None]

	if tag:
		tag = f'bundle: {tag}'

	def bundle_string_with_length(value: str, length_type: LengthType) -> list[bytes]:
		"""打包带长度前缀的字符串"""
		text_bytes = writer.text(value)
		if length_type == LengthType.BYTE:
			return [writer.byte(len(text_bytes)), text_bytes]
		elif length_type == LengthType.UINT16:
			return [writer.ushort(len(text_bytes)), text_bytes]
		elif length_type == LengthType.UINT32:
			return [writer.uint(len(text_bytes)), text_bytes]

	bytes_list = []

	for v in schema:
		if isinstance(v, bool):
			bytes_list.append(writer.byte(1 if v else 0))
		elif isinstance(v, str):
			bytes_list.extend(bundle_string_with_length(v, GlobalLengthType.value))
		elif isinstance(v, int):
			bytes_list.append(writer.int(v))
		elif isinstance(v, bytes):
			bytes_list.append(v)
		elif isinstance(v, list | tuple) and len(v) >= 2 and isinstance(v[0], str):
			type_name = v[0]
			value = v[1]
			options = v[2] if len(v) > 2 else {}

			if type_name in [
				'byte',
				'short',
				'ushort',
				'int',
				'uint',
				'long',
				'ulong',
				'float',
				'double',
			]:
				little_endian = (
					options.get('littleEndian', True)
					if isinstance(options, dict)
					else True
				)
				writer_method = getattr(writer, type_name)
				if type_name == 'byte':
					bytes_list.append(writer_method(value))
				else:
					bytes_list.append(writer_method(value, little_endian))
			elif type_name == 'string':
				with_length = (
					options.get('withLength', True)
					if isinstance(options, dict)
					else True
				)
				if not with_length:
					bytes_list.append(writer.text(value))
				else:
					length_type = (
						options.get('lengthType', GlobalLengthType.value)
						if isinstance(options, dict)
						else GlobalLengthType.value
					)
					bytes_list.extend(bundle_string_with_length(value, length_type))

	# 计算总长度
	bundle_length = sum(len(b) for b in bytes_list)

	# 合并所有字节
	result = bytearray(bundle_length)
	offset = 0
	for b in bytes_list:
		result[offset : offset + len(b)] = b
		offset += len(b)

	return bytes(result)
