import pytest
from starlette.testclient import TestClient
from src.urllookup import urlapp

#
# python3 -s test.py
#

@pytest.fixture(scope="module")
def test_app():
    client = TestClient(urlapp)
    yield client 

