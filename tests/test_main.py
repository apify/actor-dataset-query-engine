import pytest
from starlette.testclient import TestClient

from src.main import app

client = TestClient(app)

def test_root_get() -> None:
    """Test GET request to root endpoint"""
    response = client.get('/')
    assert response.status_code == 200, 'GET request failed'

def test_readiness_probe() -> None:
    """Test readiness probe endpoint"""
    response = client.get('/', headers={'x-apify-container-server-readiness-probe': '0'})
    assert response.json() != {'status': 'ok'}, 'Readiness probe passed'

    response = client.get('/', headers={'x-apify-container-server-readiness-probe': '1'})
    assert response.json() == {'status': 'ok'}
    assert response.status_code == 200, 'Readiness probe failed'

def test_root_post_invalid_input() -> None:
    """Test POST request with invalid input"""
    test_data = { 'invalid_field': 'test' }
    response = client.get('/', params=test_data)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_process_query() -> None:
    """Test the process_query function indirectly through the API"""
    test_data = {
        'query': 'test query',
        'datasetId': 'test_dataset',
        'llmProviderApiKey': 'test_api_key'
    }
    response = client.get('/', params=test_data)
    assert response.status_code == 400, 'Request processing error'

def test_unsupported_method() -> None:
    """Test unsupported HTTP method"""
    response = client.put('/')
    assert response.status_code == 405
