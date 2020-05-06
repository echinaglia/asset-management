import pytest
from pymongo import MongoClient
import os

from api.run import make_app


@pytest.fixture(autouse=True, scope="session")
def session(worker_id):
    yield type("", (), {"worker_id": worker_id})


@pytest.fixture(autouse=True)
def tst(session):
    os.environ["APPLICATION_ENV"] = "testing"
    application = make_app()
    session.client = application.test_client()
    client = MongoClient(application.config["MONGO_URL"], connect=False)
    database = client[application.config["MONGO_DB"]]
    session.db = database
    with application.app_context():
        yield session
    client.drop_database(application.config["MONGO_DB"])
