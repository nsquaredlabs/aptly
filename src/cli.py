"""CLI entry point for Aptly."""

import click


@click.group()
def main():
    """Aptly — compliance-as-a-service middleware for LLMs."""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="Bind host")
@click.option("--port", default=8000, help="Bind port")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the Aptly API server."""
    import uvicorn

    uvicorn.run("src.main:app", host=host, port=port, reload=reload)


@main.command("init-db")
def init_db():
    """Run database migrations (Alembic upgrade head)."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    click.echo("Database initialized successfully.")


@main.command()
def version():
    """Print the Aptly version."""
    from src.config import settings

    click.echo(f"aptly {settings.api_version}")


if __name__ == "__main__":
    main()
