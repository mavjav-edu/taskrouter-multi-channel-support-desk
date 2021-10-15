# just pass all tests

import app

@pytest.fixture(scope="module")
def test_client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client