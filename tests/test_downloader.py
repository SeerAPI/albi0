import asyncio
from contextlib import asynccontextmanager, suppress

import httpx
import pytest

from albi0.update.downloader import Downloader


@pytest.fixture
def anyio_backend():
	return 'asyncio'


@asynccontextmanager
async def serve(respond):
	async def handle(reader, writer):
		try:
			await reader.readuntil(b'\r\n\r\n')
			with suppress(ConnectionError):
				await respond(writer)
		finally:
			writer.close()
			with suppress(ConnectionError):
				await writer.wait_closed()

	async with await asyncio.start_server(handle, '127.0.0.1', 0) as server:
		port = server.sockets[0].getsockname()[1]
		yield f'http://127.0.0.1:{port}/bundle'


@pytest.mark.anyio
async def test_progressing_download_can_exceed_timeout(tmp_path):
	requests = 0

	async def respond(writer):
		nonlocal requests
		requests += 1
		writer.write(b'HTTP/1.1 200 OK\r\nContent-Length: 12\r\n\r\n')
		for _ in range(12):
			await asyncio.sleep(0.05)
			writer.write(b'x')
			await writer.drain()

	target = tmp_path / 'bundle'
	async with serve(respond) as url, httpx.AsyncClient(trust_env=False) as client:
		await Downloader(client, timeout=0.3).download(url, target)

	assert requests == 1
	assert target.read_bytes() == b'x' * 12


@pytest.mark.anyio
@pytest.mark.parametrize('stall_before_headers', [True, False])
async def test_stalled_download_retries(tmp_path, stall_before_headers):
	requests = 0

	async def respond(writer):
		nonlocal requests
		requests += 1
		headers = b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n'
		if requests > 1:
			writer.write(headers + b'ok')
			return

		if stall_before_headers:
			await asyncio.sleep(0.7)
		writer.write(headers + b'x')
		await writer.drain()
		if not stall_before_headers:
			await asyncio.sleep(0.7)
		writer.write(b'x')

	target = tmp_path / 'bundle'
	async with serve(respond) as url, httpx.AsyncClient(trust_env=False) as client:
		await Downloader(client).download(url, target, timeout=0.3)

	assert requests == 2
	assert target.read_bytes() == b'ok'
