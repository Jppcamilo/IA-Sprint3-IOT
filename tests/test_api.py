from io import BytesIO
import asyncio
import base64
import json

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.main import create_app
from app.provider import GeminiProvider
from app.schemas import AnaliseVisual


KEY = "chave-de-teste-" + "x" * 32
SETTINGS = Settings(gemini_api_key="fake-gemini-key", service_api_key=KEY)
RESULT = {
    "status": "IDENTIFICADO", "especie": "CACHORRO", "racaProvavel": "Pug",
    "confiancaVisual": "MEDIA", "caracteristicas": ["Pelagem curta"],
    "motivo": "Características visuais compatíveis, sujeitas à confirmação.",
}


def photo(fmt="PNG", size=(40, 40)):
    buffer = BytesIO()
    Image.new("RGB", size, "brown").save(buffer, format=fmt)
    return buffer.getvalue()


class FakeVision:
    def __init__(self, result=None):
        self.calls = 0
        self.image = None
        self.result = result or RESULT

    async def analyze(self, image):
        self.calls += 1
        self.image = image
        return AnaliseVisual.model_validate(self.result)


@pytest.fixture
def setup():
    vision = FakeVision()
    with TestClient(create_app(SETTINGS, vision)) as client:
        yield client, vision


def post(client, data=None, mime="image/png", headers=None):
    return client.post("/api/ia/analisar-pet", headers=headers or {"X-API-Key": KEY},
                       files={"foto": ("pet.png", photo() if data is None else data, mime)})


def test_success_and_java_contract(setup):
    client, vision = setup
    response = post(client)
    assert response.status_code == 200
    data = response.json()
    assert data["especie"] == "CACHORRO"
    assert data["racaProvavel"] == "Pug"
    assert data["requerConfirmacaoTutor"] is True
    assert data["idAnalise"]
    assert "probabilidade calibrada" in data["aviso"]
    with Image.open(BytesIO(vision.image)) as image:
        assert image.format == "JPEG"
        assert not image.getexif()


@pytest.mark.parametrize("mime,fmt", [("image/jpeg", "JPEG"), ("image/webp", "WEBP")])
def test_other_supported_formats(setup, mime, fmt):
    assert post(setup[0], photo(fmt), mime).status_code == 200


@pytest.mark.parametrize("headers", [{"X-API-Key": "wrong"}, {"Other": "missing"}])
def test_auth_before_provider(setup, headers):
    client, vision = setup
    assert post(client, headers=headers).status_code == 401
    assert vision.calls == 0


def test_missing_configuration():
    with TestClient(create_app(Settings(), FakeVision())) as client:
        assert client.get("/health").json() == {"status": "ok", "configurado": False}
        assert post(client).status_code == 503


@pytest.mark.parametrize("data,mime,status", [
    (b"", "image/png", 400), (b"not an image", "image/png", 400),
    (b"fake pdf", "application/pdf", 415), (photo(), "image/jpeg", 415),
    (b"x" * (5 * 1024 * 1024 + 1), "image/png", 413),
    (b"x" * (6 * 1024 * 1024 + 1), "image/png", 413),
])
def test_bad_upload_never_calls_provider(setup, data, mime, status):
    client, vision = setup
    assert post(client, data, mime).status_code == status
    assert vision.calls == 0


def test_pixel_limit_before_provider(setup):
    assert post(setup[0], photo(size=(5000, 4001))).status_code == 413
    assert setup[1].calls == 0


def test_chunked_body_limit_without_content_length(setup):
    response = setup[0].post("/api/ia/analisar-pet", headers={"X-API-Key": KEY},
                             content=iter([b"x" * 3_500_000, b"x" * 3_500_000]))
    assert response.status_code == 413
    assert setup[1].calls == 0


def test_missing_file(setup):
    assert setup[0].post("/api/ia/analisar-pet", headers={"X-API-Key": KEY}).status_code == 422


@pytest.mark.parametrize("status,especie", [("INCONCLUSIVO", "GATO"), ("NAO_SUPORTADO", None)])
def test_no_breed_when_not_identified(status, especie):
    result = dict(RESULT, status=status, especie=especie, racaProvavel=None)
    with TestClient(create_app(SETTINGS, FakeVision(result))) as client:
        assert post(client).json()["racaProvavel"] is None


def test_low_confidence_does_not_autofill():
    with TestClient(create_app(SETTINGS, FakeVision(dict(RESULT, confiancaVisual="BAIXA")))) as client:
        data = post(client).json()
        assert data["status"] == "INCONCLUSIVO"
        assert data["racaProvavel"] is None


def provider_response(result=RESULT, finish="STOP"):
    return {"candidates": [{"finishReason": finish, "content": {"parts": [
        {"text": "internal thought", "thought": True}, {"text": json.dumps(result)},
    ]}}]}


def test_real_adapter_request_and_response_with_http_mock():
    def handler(request):
        payload = json.loads(request.content)
        assert request.url.path.endswith(f"/{SETTINGS.model}:generateContent")
        assert "fake-gemini-key" not in str(request.url)
        assert request.headers["x-goog-api-key"] == "fake-gemini-key"
        part = payload["contents"][0]["parts"][0]["inlineData"]
        assert part["mimeType"] == "image/jpeg"
        assert base64.b64decode(part["data"]) == b"jpeg-test"
        assert "responseJsonSchema" in payload["generationConfig"]
        return httpx.Response(200, json=provider_response())

    provider = GeminiProvider(SETTINGS, httpx.MockTransport(handler))
    assert asyncio.run(provider.analyze(b"jpeg-test")).racaProvavel == "Pug"


@pytest.mark.parametrize("upstream,expected", [(400, 503), (401, 503), (403, 503), (404, 503), (429, 503), (500, 502)])
def test_upstream_errors_are_sanitized(upstream, expected):
    provider = GeminiProvider(SETTINGS, httpx.MockTransport(
        lambda request: httpx.Response(upstream, text="SECRET upstream error")))
    with pytest.raises(HTTPException) as error:
        asyncio.run(provider.analyze(b"image"))
    assert error.value.status_code == expected
    assert "SECRET" not in error.value.detail


@pytest.mark.parametrize("body", [
    {}, {"candidates": []}, {"candidates": [None]},
    {"candidates": [{"finishReason": "STOP", "content": {"parts": ["text"]}}]},
    provider_response(finish="MAX_TOKENS"),
    provider_response(dict(RESULT, especie="PASSARO")),
    provider_response(dict(RESULT, racaProvavel="x" * 51)),
    provider_response(dict(RESULT, status="INCONCLUSIVO")),
    provider_response(dict(RESULT, racaProvavel=None)),
])
def test_malformed_or_inconsistent_result(body):
    provider = GeminiProvider(SETTINGS, httpx.MockTransport(lambda request: httpx.Response(200, json=body)))
    with pytest.raises(HTTPException) as error:
        asyncio.run(provider.analyze(b"image"))
    assert error.value.status_code == 502


@pytest.mark.parametrize("exception,status", [(httpx.ReadTimeout, 504), (httpx.ConnectError, 503)])
def test_network_failure(exception, status):
    def handler(request):
        raise exception("sensitive detail", request=request)

    provider = GeminiProvider(SETTINGS, httpx.MockTransport(handler))
    with pytest.raises(HTTPException) as error:
        asyncio.run(provider.analyze(b"image"))
    assert error.value.status_code == status
