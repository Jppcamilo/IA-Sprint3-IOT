# 🐾 CLYVO VET — IA de análise visual de pets

Serviço independente de **Python + FastAPI** que recebe uma foto e usa a **API Gemini** para sugerir a espécie e a raça provável de um cachorro ou gato. Este repositório contém a integração com um modelo multimodal, o prompt, a validação das imagens e o contrato HTTP. Não há treinamento de um modelo próprio.

A sugestão ajuda a preencher o cadastro; o tutor precisa confirmá-la. Uma foto não comprova raça, genética ou doenças. A confiança retornada é qualitativa e não representa uma acurácia medida.

## 👥 Equipe — FIAP

- João Pedro Pereira Camilo — RM 562005
- Lucas Matsubara — RM 565020
- Pamella Christiny — RM 565206
- Felipe Ribeiro Salles de Camargo — RM 565224

## 🔗 Como se conecta ao projeto

1. O app React Native/Expo envia a foto ao backend Java, usando a autenticação do app.
2. O Java envia a foto a este serviço com a chave interna `X-API-Key`.
3. Este serviço valida a imagem, chama o Gemini e devolve a análise visual.
4. O Java retorna a sugestão ao app; o tutor confirma ou corrige espécie e raça.
5. O Java cadastra o pet e consulta o catálogo preventivo no Oracle.

**Implementado aqui:** serviço de IA, autenticação interna, validações, Swagger e testes automatizados. **Próxima integração:** a chamada no Java, o envio no mobile e a consulta dos cuidados pela espécie e raça confirmadas. Este serviço não acessa o Oracle, não armazena fotos e não agenda cuidados.

Backend de referência: [clyvopawsJavaChallenge](https://github.com/LucasMatsubara/clyvopawsJavaChallenge). Ele usa `CACHORRO`/`GATO` e limita `raca` a 50 caracteres. Consulte o [guia de integração](docs/integracao-java.md) antes de conectar.

## 🚀 Rodar no Windows

Requisito: **Python 3.11 ou superior**. Os testes desta implementação foram executados com Python 3.12. Não precisa de Docker nem de Oracle para testar a IA.

No PowerShell, na pasta do projeto:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

O último comando gera a chave interna. Abra o `.env` e preencha:

```dotenv
GEMINI_API_KEY=sua_chave_do_google_ai_studio
GEMINI_MODEL=gemini-3.8-flash
IA_SERVICE_API_KEY=cole_a_chave_gerada_no_terminal
```

- Crie a chave Gemini no [Google AI Studio](https://aistudio.google.com/apikey). Confira a disponibilidade do modelo, as cotas e eventuais custos da sua conta.
- `GEMINI_MODEL` pode ser alterado sem editar código. Escolha um modelo com entrada de imagem, saída estruturada e suporte a `generateContent`.
- `IA_SERVICE_API_KEY` precisa de pelo menos 32 caracteres. Ela será compartilhada somente com o servidor Java; é diferente da chave Gemini.
- O arquivo `.env` está no `.gitignore`. Não coloque nenhuma das chaves no app mobile nem em variáveis `EXPO_PUBLIC_*`.

Inicie:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abra **http://127.0.0.1:8000/docs**. Clique em **Authorize**, informe a chave interna (`IA_SERVICE_API_KEY`), abra `POST /api/ia/analisar-pet`, clique em **Try it out**, escolha a foto no campo `foto` e execute.

Em Linux/macOS, use `python3 -m venv .venv`, `cp .env.example .env` e troque `.\.venv\Scripts\python.exe` por `.venv/bin/python` nos comandos.

## 📷 Contrato da API

| Rota | Objetivo | Autenticação |
| --- | --- | --- |
| `GET /health` | Informa se o processo está vivo e se a configuração local foi preenchida | Não |
| `POST /api/ia/analisar-pet` | Analisa uma única foto | `X-API-Key` |
| `GET /docs` | Swagger para teste manual | A análise exige a chave |

`/health` não faz chamadas pagas nem comprova que a chave Gemini ou a cota são válidas.

Envio: `multipart/form-data`, campo **foto** do tipo arquivo. Aceita JPEG, PNG e WebP estático, até **5 MiB** e **20 megapixels**. O corpo completo tem limite de **6 MiB**. O conteúdo é decodificado e validado; a extensão do nome não basta. Antes do envio ao Gemini, a foto é redimensionada para até 1600 × 1600, convertida para JPEG e tem os metadados removidos.

Exemplo de resposta **ilustrativa**, não resultado de uma avaliação real:

```json
{
  "status": "IDENTIFICADO",
  "especie": "CACHORRO",
  "racaProvavel": "Pug",
  "confiancaVisual": "MEDIA",
  "caracteristicas": ["Pelagem curta", "Focinho curto"],
  "motivo": "Aparência compatível com Pug; confirmar com o tutor.",
  "idAnalise": "eb49e89f-c731-47db-89ae-66cf7c5bb105",
  "modelo": "gemini-3.8-flash",
  "requerConfirmacaoTutor": true,
  "aviso": "Sugestão visual, não comprova raça, genética ou diagnóstico. Confiança visual é uma avaliação do modelo, não uma probabilidade calibrada. Confirme os dados antes de cadastrar o pet."
}
```

| Status | Comportamento esperado no app |
| --- | --- |
| `IDENTIFICADO` | Mostrar a sugestão editável e pedir confirmação |
| `INCONCLUSIVO` | Solicitar outra foto ou permitir cadastro manual; `racaProvavel` é `null` |
| `NAO_SUPORTADO` | Informar que a foto precisa conter um cachorro ou gato; espécie e raça são `null` |

`Sem raça definida` pode ser uma hipótese visual; não é usado automaticamente para encobrir uma análise inconclusiva. Respostas com confiança `BAIXA` nunca preenchem a raça. As instruções pedem que fotos com vários animais sejam inconclusivas, mas esse reconhecimento depende do modelo e deve ser avaliado com imagens reais.

O peso, a data de nascimento, o sexo e o nome continuam sendo informados pelo tutor. O `idAnalise` identifica a resposta, mas não cria um histórico persistido nem uma rota de consulta.

### Erros

| Código | Significado |
| --- | --- |
| 400 | Arquivo vazio, inválido ou corrompido |
| 401 | Chave interna ausente ou incorreta |
| 413 | Limite de bytes ou resolução excedido |
| 415 | Formato não suportado, animação ou tipo incompatível com o conteúdo |
| 422 | Campo `foto` ausente ou multipart inválido |
| 502 | Falha do provedor, resposta bloqueada, incompleta ou fora do contrato |
| 503 | Configuração ausente/inválida, problema de conexão, cota ou acesso ao provedor |
| 504 | O provedor ultrapassou o tempo limite de 45 segundos |

Erros usam `detail`; a validação do FastAPI pode retornar uma lista nesse campo. Não há substituição silenciosa por resultado fictício quando a IA falha.

## 🧪 Testes

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes usam fotos sintéticas para validar upload e um transporte HTTP simulado para validar a integração Gemini, autenticação, erros e schema. **Não medem a qualidade do reconhecimento de raças.** Não exigem chaves nem consomem a API.

Antes de apresentar a IA como validada, execute os [cenários com fotos reais](docs/validacao.md). A chamada real depende da chave e da cota do usuário; ela não foi executada durante a implementação.

## 📁 Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `app/main.py` | Rotas, autenticação e limite do corpo da requisição |
| `app/config.py` | Configurações lidas do `.env` |
| `app/images.py` | Validação, redução e remoção de metadados |
| `app/provider.py` | Prompt e chamada HTTP ao Gemini |
| `app/schemas.py` | Contrato JSON e validações de consistência |
| `tests/test_api.py` | Testes sem consumo da API externa |
| `docs/integracao-java.md` | Contrato de integração com o backend existente |
| `docs/validacao.md` | Roteiro para verificar o reconhecimento real |

Para hospedar, use HTTPS, mantenha este serviço acessível apenas ao backend e aplique limites de requisições e concorrência no gateway. Não use `--reload` em produção. A autenticação dos tutores permanece no Java. O processamento envia a foto ao Google; informe isso ao tutor antes do envio e verifique as condições de tratamento de dados da conta usada. O serviço não grava a imagem em seu banco, mas o parser HTTP pode usar arquivo temporário durante o upload, fechado ao fim da requisição.

## 📚 Referências e proposta acadêmica

- [Proposta acadêmica inicial, com observações sobre o escopo](docs/proposta-academica.md)
- [Fluxo original no Draw.io](https://drive.google.com/file/d/1RC9h_607KHfErIiyqU3kk77gZ631Q5vh/view?usp=sharing)
- [Vídeo da proposta](https://youtu.be/ZYf1s8ssiHQ)
- [Gemini: imagens](https://ai.google.dev/gemini-api/docs/image-understanding)
- [Gemini: saída estruturada](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini: referência generateContent](https://ai.google.dev/api/generate-content)
- [Modelos disponíveis](https://ai.google.dev/gemini-api/docs/models)
- [FastAPI: upload de arquivos](https://fastapi.tiangolo.com/tutorial/request-files/)
