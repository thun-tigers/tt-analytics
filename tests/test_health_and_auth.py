def test_health_ok(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "tt-analytics"}


def test_index_requires_login(client):
    response = client.get('/')
    assert response.status_code in (302, 401, 403)


def test_login_redirects_to_auth(client):
    response = client.get('/login')
    assert response.status_code == 302
    assert 'localhost:8085' in response.headers['Location']
