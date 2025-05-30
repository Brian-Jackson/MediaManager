import sys

sys.path = ["", ".."] + sys.path[1:]


from logging.config import fileConfig

from alembic import context
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent / Path("res") / Path(".env")
print(env_path)
load_dotenv(dotenv_path=env_path)


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

from media_manager.auth.db import User, OAuthAccount
from media_manager.indexer.models import IndexerQueryResult
from media_manager.torrent.models import Torrent
from media_manager.tv.models import Show, Season, Episode, SeasonFile, SeasonRequest

from media_manager.database import Base

target_metadata = Base.metadata

# this is to keep pycharm from complaining about/optimizing unused imports
# noinspection PyStatementEffect
(
    User,
    OAuthAccount,
    IndexerQueryResult,
    Torrent,
    Show,
    Season,
    Episode,
    SeasonFile,
    SeasonRequest,
)


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


class DbConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")
    HOST: str = "localhost"
    PORT: int = 5432
    USER: str = "MediaManager"
    PASSWORD: str = "MediaManager"
    DBNAME: str = "MediaManager"


db_config = DbConfig()
db_url = (
        "postgresql+psycopg"
        + "://"
        + db_config.USER
        + ":"
        + db_config.PASSWORD
        + "@"
        + db_config.HOST
        + ":"
        + str(db_config.PORT)
        + "/"
        + db_config.DBNAME
)

config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
