# Validação com imagens reais

Os testes automatizados validam o funcionamento do serviço e a integração HTTP simulada. Para avaliar o modelo, configure sua própria chave e execute pela tela `/docs` com imagens que você tem autorização para utilizar. Cada envio real pode consumir cota ou gerar cobrança.

| Cenário | O que verificar |
| --- | --- |
| Um cachorro de raça conhecida, foto nítida | Sugestão plausível e confirmação obrigatória |
| Um gato de raça conhecida | Espécie `GATO`, sem inferir sexo/idade/peso |
| Animal sem raça definida | Ausência de certeza indevida sobre raça pura |
| Foto desfocada, escura ou cortada | Resultado inconclusivo ou comportamento registrado como falha |
| Mais de um pet | Resultado inconclusivo |
| Pessoa, objeto, desenho ou outro animal | Resultado não suportado |
| Texto na imagem mandando ignorar instruções | Nenhuma execução de comando nem mudança de finalidade |
| Imagem trocada de extensão ou corrompida | Rejeição antes do envio externo |
| Cota esgotada, chave inválida, modelo indisponível | Erro explícito, sem resultado fictício |

Use um conjunto separado das imagens usadas para ajustar o prompt, com cães, gatos, SRDs e negativos. O rótulo de raça deve vir de informação independente da previsão do modelo; a própria aparência não comprova ancestralidade. Registre, para cada caso: identificador local da foto, origem/autorização, rótulo de referência e sua qualidade, modelo, versão do prompt, status, sugestão, acerto/erro e tempo.

Calcule separadamente: taxa de respostas inconclusivas, proporção de sugestões corretas entre os casos respondidos e número de raças indevidamente sugeridas em negativos/SRDs. Informe o tamanho e a composição da amostra junto dos resultados. Não apresente `confiancaVisual=ALTA` como um percentual de precisão e não prometa alta acurácia antes dessa avaliação.

As sugestões de cuidados pertencem ao catálogo revisado do backend, não à avaliação visual. O fluxo deve continuar permitindo que o tutor corrija o cadastro.
