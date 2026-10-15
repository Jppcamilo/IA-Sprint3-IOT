from io import BytesIO
import warnings

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError


MIME_FORMATS = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}


def prepare_image(data: bytes, content_type: str | None) -> bytes:
    """Valida os pixels, reduz a foto e remove metadados antes do envio externo."""
    if content_type not in MIME_FORMATS:
        raise HTTPException(415, "Envie uma imagem JPEG, PNG ou WebP.")
    if not data:
        raise HTTPException(400, "O arquivo está vazio.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format != MIME_FORMATS[content_type]:
                    raise HTTPException(415, "O conteúdo não corresponde ao tipo informado.")
                if source.width * source.height > 20_000_000:
                    raise HTTPException(413, "A imagem deve ter no máximo 20 megapixels.")
                if getattr(source, "n_frames", 1) != 1:
                    raise HTTPException(415, "Envie uma foto estática, sem animação.")
                source.verify()
            with Image.open(BytesIO(data)) as source:
                source.load()
                photo = ImageOps.exif_transpose(source).convert("RGB")
                photo.thumbnail((1600, 1600))
                # Uma imagem nova evita carregar EXIF/GPS/comentários do original.
                clean = Image.new("RGB", photo.size)
                clean.paste(photo)
                output = BytesIO()
                clean.save(output, format="JPEG", quality=85)
                return output.getvalue()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise HTTPException(413, "A resolução da imagem é muito grande.") from exc
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise HTTPException(400, "Imagem inválida ou corrompida.") from exc
