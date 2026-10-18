from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AnaliseVisual(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: Literal["IDENTIFICADO", "INCONCLUSIVO", "NAO_SUPORTADO"]
    especie: Literal["CACHORRO", "GATO"] | None
    racaProvavel: str | None = Field(max_length=50)
    confiancaVisual: Literal["BAIXA", "MEDIA", "ALTA"]
    caracteristicas: list[str] = Field(max_length=8)
    motivo: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validar_coerencia(self):
        if any(not c.strip() or len(c) > 150 for c in self.caracteristicas):
            raise ValueError("Características devem ter entre 1 e 150 caracteres.")
        if self.status == "IDENTIFICADO":
            if self.especie is None or not self.racaProvavel:
                raise ValueError("Identificação exige espécie e raça provável.")
        elif self.racaProvavel is not None:
            raise ValueError("Resultado sem identificação não pode sugerir raça.")
        if self.status == "NAO_SUPORTADO" and self.especie is not None:
            raise ValueError("Imagem não suportada não pode ter espécie suportada.")
        return self


class AnaliseResponse(AnaliseVisual):
    idAnalise: str
    modelo: str
    requerConfirmacaoTutor: Literal[True] = True
    aviso: str = (
        "Sugestão visual, não comprova raça, genética ou diagnóstico. "
        "Confiança visual é uma avaliação do modelo, não uma probabilidade calibrada. "
        "Confirme os dados antes de cadastrar o pet."
    )
