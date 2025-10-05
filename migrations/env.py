import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# --- Load Environment Variables ---
# This will look for the .env.app file in the project's root directory
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.app'))


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- Set the DATABASE_URL from the environment ---
# This ensures that Alembic uses the same database as your main application
database_url = os.getenv("MIGRATION_DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
else:
    raise ValueError("MIGRATION_DATABASE_URL is not set in the environment.")


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# --- Configure target_metadata for Autogenerate ---
# Add your model's MetaData object here for 'autogenerate' support.
# Import your Base model from where it is defined.
# ADJUST THE IMPORT PATH AS NEEDED.
from app.models.base import Base
target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# --- ASYNCHRONOUS MIGRATION SETUP ---

def do_run_migrations(connection):
    """Helper function to run the migrations."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Main async function to set up the engine and run migrations."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Use connection.begin() to create a transaction block that will
        # automatically commit on successful completion.
        async with connection.begin():
            # The SET ROLE command must be inside this transaction
            await connection.execute(text("SET ROLE app_owner"))
            await connection.run_sync(do_run_migrations)

    # Dispose of the engine connection
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode by wrapping the async function."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()