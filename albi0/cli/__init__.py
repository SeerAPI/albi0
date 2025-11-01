import importlib
from pathlib import Path

from asyncer import syncify
import click

from albi0.request import client as httpx_client


@click.group(invoke_without_command=True)
@click.version_option(
	None,
	'-V',
	'--version',
	prog_name='albi0',
)
@click.option(
	'-d',
	'--cwd',
	default=None,
	help='The working directory.',
	type=Path,
	is_eager=True,
	expose_value=False,
)
@click.pass_context
@syncify
async def cli(ctx: click.Context):
	# CLI 自动加载所有插件
	importlib.import_module('albi0.plugins.newseer')
	importlib.import_module('albi0.plugins.seerproject')

	ctx.call_on_close(on_close)
	if ctx.invoked_subcommand is not None:
		return


@syncify
async def on_close():
	await httpx_client.aclose()


from .commands import extract, list_, update

cli.add_command(update)
cli.add_command(extract)
cli.add_command(list_)
