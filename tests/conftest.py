import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment before any app imports
os.environ.setdefault("DATABASE_URL", "postgresql://outreach:outreach@localhost:5432/outreach_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")


@pytest.fixture(scope="session")
def db_engine():
    """Create a test database engine."""
    url = os.environ["DATABASE_URL"]
    engine = create_engine(url)
    from src.db.models import Base
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create a test database session with rollback."""
    Session = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = Session()
    yield session
    session.rollback()
    session.close()
