"""
Command Line Interface для приложения.
"""

import click
import json
from core.app import KemonoParserApp


@click.group()
@click.option("--config", default="config/config.yaml", help="Путь к конфигу")
@click.pass_context
def cli(ctx, config):
    """Kemono Parser CLI"""
    ctx.ensure_object(dict)
    ctx.obj["app"] = KemonoParserApp(config)
    ctx.obj["app"].initialize()


@cli.command()
@click.argument("artist_name")
@click.option("--service", default="patreon", help="Сервис")
@click.pass_context
def download(ctx, artist_name, service):
    """Скачать контент артиста"""
    app = ctx.obj["app"]
    result = app.run_artist_download(artist_name, service)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@cli.command()
@click.pass_context
def modules(ctx):
    """Список модулей"""
    app = ctx.obj["app"]
    for module in app.registry.get_all_modules():
        info = module.get_info()
        click.echo(f"{info['name']} v{info['version']} - {info['state']}")


@cli.command()
@click.pass_context
def shutdown(ctx):
    """Остановка приложения"""
    app = ctx.obj["app"]
    app.shutdown()


if __name__ == "__main__":
    cli(obj={})