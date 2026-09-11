# Documentação de Integração de IA - CLYVO VET

## 👥 Equipe de Desenvolvimento (FIAP)

* **João Pedro Pereira Camilo** (RM 562005)
* **Lucas Matsubara** (RM 565020)
* **Pamella Christiny** (RM 565206)
* **Felipe Ribeiro Salles de Camargo** (RM565224)

---

## 1. Definição do Problema de Negócio
O momento do cadastro de um pet em aplicativos de saúde veterinária costuma gerar atritos, pois muitos tutores desconhecem a raça exata do animal, suas variações ou as predisposições genéticas atreladas a ela. O problema de negócio que nossa Inteligência Artificial resolverá é a falta de personalização inicial e a fricção no onboarding da plataforma CLYVO VET.

| Stakeholder | Valor Agregado pela Solução |
| :--- | :--- |
| **Tutor** | Facilita o uso do aplicativo (basta tirar uma foto do pet) e fornece segurança, pois o tutor passa a receber informações de saúde realmente direcionadas às necessidades do seu animal. |
| **Clínica e Sistema** | Garante uma base de dados mais limpa e padronizada, permitindo priorizar ações preventivas e otimizar o atendimento na CLYVO VET. |
| **Paciente (Pet)** | Inicia uma jornada contínua de cuidado, onde exames e vacinas preventivas são recomendados precocemente com base na genética identificada da raça. |

---

## 2. Abordagem de IA Adotada e Justificativa
A abordagem escolhida é a de IA Generativa Multimodal (Visão Computacional) integrada a um Motor de Regras Inteligentes.

**Justificativa Técnica:** Utilizaremos um modelo de Visão capaz de processar imagens capturadas diretamente da câmera do dispositivo via aplicativo mobile em React Native. Essa abordagem foi escolhida porque não apenas resolve a classificação da raça com alta precisão, mas permite extrair características físicas em tempo real. O Motor de Regras no backend (Java Spring Boot) correlaciona a raça identificada com o nosso banco de dados (Oracle), gerando a trilha de cuidados personalizada, atendendo à exigência do Challenge de apoiar a tomada de decisão no cuidado contínuo do animal.

---

## 3. Dados Necessários e Estrutura
Para alimentar a Inteligência Artificial e o sistema como um todo, utilizaremos os seguintes conjuntos de dados:

* **Origem dos Dados (Input):** Imagens do pet capturadas pela câmera ou selecionadas na galeria do smartphone do tutor durante o processo de cadastro no aplicativo.
* **Dados de Perfil Contextuais:** Idade estimada e peso (inseridos manualmente pelo tutor para complementar a análise da IA e refinar as recomendações de saúde).
* **Estrutura de Domínio (Banco de Dados Oracle):**
  * **Tabela Racas_Predisposicoes:** Contém o mapeamento de raças para doenças comuns (exemplo: Pug com alta incidência de problemas respiratórios).
  * **Tabela Trilha_Cuidados:** Cronograma base de vacinas e exames padrão recomendados para cada raça mapeada.
* **Utilização e Processamento:** A imagem alimenta o modelo de IA. O retorno estruturado do modelo é cruzado com as tabelas de predisposições para gerar alertas e agendamentos sugeridos de forma automática no perfil recém-criado do pet.[

---

## 4. Fluxo de Dados e Arquitetura de Integração
O fluxo de comunicação entre os atores do sistema (usuário, front-end, back-end e nuvem) ocorrerá na seguinte ordem lógica:

1. O tutor acessa o aplicativo mobile e inicia o processo de adição de um novo pet.
2. O componente de câmera da interface captura a foto do animal e a envia via requisição HTTP POST para a API REST no servidor.
3. O servidor backend atua como um orquestrador central: ele recebe a imagem e dispara uma chamada autenticada e segura para a API externa do modelo de Inteligência Artificial.
4. A Inteligência Artificial processa os pixels da imagem, identifica os padrões fenotípicos e devolve ao backend uma resposta JSON contendo a raça provável e o grau de confiança da análise.
5. O backend extrai essa informação e realiza uma consulta no banco de dados para buscar a trilha de cuidados preventiva atrelada àquela raça específica.
6. Os dados combinados (Raça Identificada + Alertas de Cuidados) são persistidos no banco e empacotados em uma resposta enviada de volta para o cliente mobile.
7. A tela do aplicativo é atualizada de forma reativa, exibindo a raça identificada para validação do tutor, juntamente com os primeiros cards de recomendação de saúde na dashboard do pet.

---

### Diagrama Arquitetural da Solução
*(Nota: Lembre-se de colocar o arquivo de imagem exportado do Draw.io dentro da pasta do repositório no GitHub e alterar o nome do arquivo na linha abaixo)*

![Fluxo da Arquitetura](https://drive.google.com/file/d/1RC9h_607KHfErIiyqU3kk77gZ631Q5vh/view?usp=drive_link)

## Demonstração do Projeto

**[Assista ao nosso vídeo de apresentação clicando aqui](https://youtu.be/0Srws2ukES0)**
