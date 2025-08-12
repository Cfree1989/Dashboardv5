# type: ignore


def test_public_health_ok(client):
    resp = client.get('/api/v1/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] in ('ok', 'error')
    assert 'components' in data
    assert 'database' in data['components']


