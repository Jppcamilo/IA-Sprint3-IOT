# Integração futura com o backend Java

Referência inspecionada: `LucasMatsubara/clyvopawsJavaChallenge`, commit `aadacd66b5abce93ff0ffd024e46fc110c48d78a`, Spring Boot 3.2.6 / Java 21. Nenhuma alteração foi aplicada nesse repositório pelo serviço de IA.

## Compatibilidade encontrada

| Backend existente | Serviço de IA / ação necessária |
| --- | --- |
| `Especie`: `CACHORRO`, `GATO` | Mesmos valores; resultado inconclusivo pode retornar `null` |
| `PetRequestDTO.raca`: obrigatório, máximo 50 caracteres | `racaProvavel`: até 50 caracteres; copiar para `raca` somente depois da confirmação |
| `PetRequestDTO`: nome, peso, sexo, nascimento, descrição, fotoUrl, tutorId | Permanecem no cadastro; não são inferidos pela IA |
| `PetService.cadastrar`: valida o tutor e persiste o pet | Continuar usando esse fluxo após a confirmação |
| `CatalogoPreventivo`: espécie, raça, doença, idade de alerta e cuidados | Fonte dos cuidados, sem gerar recomendações médicas no modelo |
| `buscarPlanoPreventivo(String especieRecebida)` | Atualmente filtra apenas por espécie, não por raça |

## Chamada interna

Configure no servidor Java:

```properties
ia.base-url=${IA_BASE_URL:http://127.0.0.1:8000}
ia.api-key=${IA_SERVICE_API_KEY}
```

O `.env` do Python não é automaticamente carregado pelo Java. Configure as variáveis na execução do IntelliJ, no terminal ou no ambiente de hospedagem do Java.

O Java deve enviar:

```http
POST /api/ia/analisar-pet
X-API-Key: <chave interna compartilhada>
Content-Type: multipart/form-data; boundary=<gerado pelo cliente HTTP>
```

Uma única parte de arquivo chamada `foto`, com `Content-Type` JPEG, PNG ou WebP. Ao usar uma biblioteca HTTP, deixe que ela gere o boundary. Use timeout de conexão de 5 segundos e de leitura de 60 segundos (maior que os 45 segundos da chamada Gemini). Trate os códigos de erro documentados no README; não transforme erro em sugestão de raça.

Exemplo de chamada com `RestClient` do Spring, para adaptar em um serviço do Java. Este trecho é orientação de integração, ainda não foi inserido ou compilado no backend:

```java
var factory = new org.springframework.http.client.SimpleClientHttpRequestFactory();
factory.setConnectTimeout(5_000);
factory.setReadTimeout(60_000);

var client = org.springframework.web.client.RestClient.builder()
        .baseUrl(iaBaseUrl) // recebido da configuração do servidor
        .requestFactory(factory)
        .defaultHeader("X-API-Key", iaApiKey)
        .build();

var arquivo = new org.springframework.core.io.ByteArrayResource(foto.getBytes()) {
    @Override
    public String getFilename() {
        return "pet"; // não reutiliza o nome enviado pelo usuário
    }
};
var headers = new org.springframework.http.HttpHeaders();
headers.setContentType(org.springframework.http.MediaType.parseMediaType(foto.getContentType()));
var body = new org.springframework.util.LinkedMultiValueMap<String, Object>();
body.add("foto", new org.springframework.http.HttpEntity<>(arquivo, headers));

var analise = client.post()
        .uri("/api/ia/analisar-pet")
        .contentType(org.springframework.http.MediaType.MULTIPART_FORM_DATA)
        .body(body)
        .retrieve()
        .body(com.fasterxml.jackson.databind.JsonNode.class);
```

Valide tamanho e tipo antes desse trecho. O endpoint Java precisa exigir o JWT do tutor e respeitar as regras de autorização existentes. Ao analisar uma foto de um pet já cadastrado, confira a posse do pet. A chave interna não deve ser recebida do mobile nem devolvida a ele.

## Confirmar antes de cadastrar

1. Mobile recebe o JSON da análise por meio do Java.
2. Se `status=IDENTIFICADO`, mostra espécie e raça editáveis.
3. Tutor confirma/corrige e informa os demais campos obrigatórios.
4. Mobile chama o cadastro existente com `raca` e `especie` confirmadas.
5. Java consulta o catálogo pela espécie **e** pela raça confirmadas.

`INCONCLUSIVO` e `NAO_SUPORTADO` não impedem o cadastro manual. Não enviar `null` como raça ao cadastro atual, pois o DTO o rejeita. O nome de raça gerado pode variar em maiúsculas, acentos e sinônimos: normalize contra um catálogo controlado, com aliases, e permita seleção manual. Não associe cuidados apenas com comparação aproximada de texto.

O filtro por raça deve ser acrescentado no backend existente (por exemplo, um método de repository para espécie e raça normalizadas). A consulta atual apenas por espécie pode devolver cuidados de outras raças. Ausência de correspondência deve produzir uma lista vazia ou orientações gerais previamente cadastradas e revisadas, nunca cuidados inventados pela IA.

Para idade dos alertas, use a data de nascimento confirmada; para peso, use o valor informado pelo tutor. A foto não fornece esses dados de forma confiável.

## Endereços

Quando os dois serviços rodam no mesmo computador, o Java chama `http://127.0.0.1:8000`. Em servidores ou containers distintos, configure `IA_BASE_URL` com o endereço interno do serviço de IA; `localhost` se refere ao próprio servidor/container.

O celular continua chamando somente o Java. Não existe motivo para incluir a chave Gemini ou a chave interna no bundle Expo. Configure autenticação, cotas por tutor, HTTPS e limites de upload também na camada Java/gateway antes de publicar.
