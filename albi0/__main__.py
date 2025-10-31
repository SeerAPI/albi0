import sys

import anyio
from asyncer import asyncify

from albi0.cli import cli


async def cli_main(*args, **kwargs):
	return await asyncify(cli)(*args, **kwargs)


def main(*args):
	try:
		anyio.run(cli_main, *args)
	except KeyboardInterrupt:
		sys.exit(1)


if __name__ == '__main__':
	main()
