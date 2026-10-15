import secrets
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers

from app.config import Settings, load_settings
from app.images import prepare_image
from app.provider import GeminiProvider, VisionProvider
from app.schemas import AnaliseResponse


class RequestGuard:
    """Autentica e limita o corpo antes de o parser multipart criar arquivos."""
    def __init__(self, app, settings: Settings):
        self.app, self.settings = app, settings

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in ("GET", "HEAD"):
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        if not self.settings.configured:
            return await JSONResponse(
                {"detail": "Configure GEMINI_API_KEY, GEMINI_MODEL e IA_SERVICE_API_KEY (mínimo 32 caracteres)."},
                status_code=503,
            )(scope, receive, send)
        supplied = headers.get("x-api-key", "")
        if not secrets.compare_digest(supplied.encode(), self.settings.service_api_key.encode()):
            return await JSONResponse({"detail": "Chave de serviço inválida."}, status_code=401)(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.settings.max_request_bytes:
                return await JSONResponse({"detail": "Requisição muito grande."}, status_code=413)(scope, receive, send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


def create_app(settings: Settings | None = None, provider: VisionProvider | None = None) -> FastAPI:
    settings = settings or load_settings()
    provider = provider or GeminiProvider(settings)
    api = FastAPI(title="CLYVO VET — Análise visual de pets", version="1.0.0")
    api.add_middleware(RequestGuard, settings=settings)
    key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

    @api.get("/health", tags=["Status"])
    async def health():
        return {"status": "ok", "configurado": settings.configured}

    @api.post("/api/ia/analisar-pet", response_model=AnaliseResponse, tags=["IA"],
              dependencies=[Depends(key_header)])
    async def analisar_pet(foto: UploadFile = File(description="Foto JPEG, PNG ou WebP de até 5 MiB.")):
        try:
            data = await foto.read(settings.max_image_bytes + 1)
            if len(data) > settings.max_image_bytes:
                raise HTTPException(413, "A foto deve ter no máximo 5 MiB.")
            image = await run_in_threadpool(prepare_image, data, foto.content_type)
        finally:
            await foto.close()
        result = await provider.analyze(image)
        # Defesa adicional: uma sugestão de baixa confiança nunca preenche raça.
        if result.status == "IDENTIFICADO" and result.confiancaVisual == "BAIXA":
            result = result.model_copy(update={"status": "INCONCLUSIVO", "racaProvavel": None})
        return AnaliseResponse(**result.model_dump(), idAnalise=str(uuid4()), modelo=settings.model)

    return api


app = create_app()
