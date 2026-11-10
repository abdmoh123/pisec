"""File for connecting the server to the database."""

from collections.abc import Generator
from typing import Any, Protocol

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from pisec_server.core.config import DBType, settings
from pisec_server.db.db_models import Base


class DBConnectorProtocol(Protocol):
    """Protocol for all database connectors used to connect the API to the database."""

    def get_engine(self) -> Engine:
        """Returns the Engine of the database.

        Used to get the sqlalchemy ORM to work.
        """
        ...

    def get_session(self) -> Session:
        """Returns the database session.

        Used when querying the database.
        """
        ...


class GeneralDBConnector:
    """Generalised database connector used to connect the API to the database."""

    def __init__(self, database_url: str, **engine_kwargs: Any):  # pyright: ignore[reportExplicitAny, reportAny]
        """Initialises and sets up the engine and session so the API can interact with the database."""
        self._engine: Engine = create_engine(database_url, **engine_kwargs)  # pyright: ignore[reportAny]
        self._session_maker: sessionmaker[Session] = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

    def get_engine(self) -> Engine:
        """Returns the Engine of the database.

        Used to get the sqlalchemy ORM to work.
        """
        return self._engine

    def get_session(self) -> Session:
        """Returns the database session.

        Used when querying the database.
        """
        return self._session_maker()


def create_postgres_connector(database_url: str) -> DBConnectorProtocol:
    """Creates a postgres database connector."""
    return GeneralDBConnector(database_url)


def create_sqlite_connector(database_url: str) -> DBConnectorProtocol:
    """Creates a sqlite database connector with some default arguments."""
    return GeneralDBConnector(database_url, connect_args={"check_same_thread": False})


def create_db_connector(db_type: DBType) -> DBConnectorProtocol:
    """Creates a database connector based on environment variable values."""
    match db_type:
        case DBType.SQLITE:
            return create_sqlite_connector(settings.DB_URL)
        case DBType.POSTGRES:
            return create_postgres_connector(settings.DB_URL)


def get_db() -> Generator[Session]:
    """Returns an instance of the database that you can query against."""
    session = db_connector.get_session()
    try:
        yield session
        session.commit()
    except:
        # Undo any changes if an error occured
        session.rollback()
        raise
    finally:
        session.close()


db_connector: DBConnectorProtocol = create_db_connector(settings.DB_TYPE)
Base.metadata.create_all(bind=db_connector.get_engine())
