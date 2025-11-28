import os
import importlib.util
from pathlib import Path
from unittest.mock import patch


def test_skips_when_no_api_key(monkeypatch):
    monkeypatch.delenv('OLLAMA_API_KEY', raising=False)
    # Load module directly from repo root
    module_path = Path(__file__).resolve().parents[1] / 'test_cloud_models.py'
    spec = importlib.util.spec_from_file_location('test_cloud_models', str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.API_KEY is None
    res = module.test_model('gpt-oss:20b', 'Hello')
    assert res is None  # None => skipped


def test_calls_requests_when_api_key_set(monkeypatch):
    monkeypatch.setenv('OLLAMA_API_KEY', 'fakekey')
    monkeypatch.setenv('OLLAMA_BASE_URL', 'https://ollama.com')
    # Import module
    module_path = Path(__file__).resolve().parents[1] / 'test_cloud_models.py'
    spec = importlib.util.spec_from_file_location('test_cloud_models', str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class DummyResponse:
        status_code = 200

        def json(self):
            return {'message': {'content': 'hi'}}

        text = '{"message":{"content":"hi"}}'

    with patch('requests.post') as fake_post:
        fake_post.return_value = DummyResponse()
        res = module.test_model('gpt-oss:20b', 'Hello')
        assert res is True
        fake_post.assert_called()
