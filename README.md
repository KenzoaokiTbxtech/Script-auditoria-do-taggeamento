# GCP Tag Compliance Scanner 🕵️‍♂️

Script em Python para realizar a auditoria completa de labels e tags dos recursos do **Google Cloud Platform (GCP)** utilizando a API do **Cloud Asset Inventory**.

O script faz a descoberta automática dos recursos mapeados, avalia a presença das tags obrigatórias, classifica os recursos em níveis de conformidade e gera arquivos CSV formatados prontos para alimentar scripts de aplicação de tags.

## Funcionalidades

* Descoberta ativa de recursos sem depender de inventários manuais.
* Avaliação das tags obrigatórias:
* `team`
* `cost_center`
* `country`


* Classificação dos recursos em 3 listas:
* **Totalmente Taggeados**: Possuem todas as tags obrigatórias.
* **Taggeados Parciais**: Possuem alguma label, mas faltam obrigatórias ou estão fora do padrão.
* **Não Taggeados**: Não possuem nenhuma label.


* Extração do "nome curto" do recurso para facilitar a leitura e automação.
* Geração de um relatório executivo em Markdown (`relatorio_status_tags.md`).
* Geração de arquivos CSV de pendências específicos por serviço, apenas com os recursos parciais e não taggeados.
* Separação lógica de recursos com o mesmo Asset Type (ex: Forwarding Rules Regionais vs Globais).
* Autodetecção do Project ID autenticado no terminal.
* Suporte à execução de um único serviço ou de todos simultaneamente (`--all`).

## Estrutura esperada

Exemplo de organização após a execução do script:

```text
auditoria-tags/
├── audit_gcp_resources.py
├── auditoria_output/
│   ├── relatorio_status_tags.md
│   ├── app-engine_pendentes.csv
│   └── artifact-registry_pendentes.csv
└── README.md

```

## Formato dos arquivos CSV gerados

O script gera os arquivos CSV estritamente no formato exigido pelos seus scripts de aplicação (taggeamento). Os arquivos conterão apenas recursos que precisam de intervenção e pré-preencherão as colunas com as labels que o recurso já possuir.

```csv
recurso,team,cost_center,country
meu-banco-sql,,cc-12345,brasil
bucket-sem-tag,,,
api-gateway-global,financas,,

```

### Colunas

| Coluna | Descrição |
| --- | --- |
| `recurso` | Nome curto do recurso extraído da infraestrutura |
| `team` | Time responsável pelo recurso (vazio se faltante) |
| `cost_center` | Centro de custo associado (vazio se faltante) |
| `country` | País associado ao recurso (vazio se faltante) |

> Os CSVs não são gerados para serviços que já estão 100% em conformidade, mantendo o diretório de saída limpo.

## Particularidade do Cloud Asset Inventory

Este script não realiza chamadas individuais para cada serviço do GCP (Compute Engine, Cloud SQL, Storage, etc.). Em vez disso, ele utiliza o **Cloud Asset Inventory**, que permite consultar em lote os metadados de toda a organização ou projeto usando o método:

```python
client.search_all_resources()

```

Isso garante velocidade e evita a necessidade de habilitar dezenas de APIs separadas.

**Tratamento de Forwarding Rules:**
No Asset Inventory, não existe diferença de tipo entre regras globais e regionais (ambas são `[compute.googleapis.com/ForwardingRule](https://compute.googleapis.com/ForwardingRule)`). O script trata essa particularidade internamente, filtrando pela propriedade `location`, garantindo que os relatórios e CSVs de `global-forwarding-rules` e `forwarding-rules` não contenham recursos duplicados.

## Pré-requisitos

Antes de executar o script, é necessário possuir:

* Python 3.
* Google Cloud SDK (`gcloud`) instalado.
* Bibliotecas Python instaladas.
* API do Cloud Asset Inventory habilitada no projeto.
* Permissão para leitura de assets (`roles/cloudasset.viewer`).

### Instalação das dependências Python

```bash
pip install google-cloud-asset google-auth

```

### Habilitando a API

Caso a API ainda não esteja ativa no projeto alvo, execute:

```bash
gcloud services enable cloudasset.googleapis.com

```

> **Nota de Propagação:** Ao ativar esta API pela primeira vez em um projeto, aguarde cerca de 3 a 5 minutos antes de rodar o script para que a ativação se propague por todos os servidores do Google.

## Autenticação

Antes da execução, é estritamente necessário realizar a dupla autenticação no Google Cloud (para a CLI e para as bibliotecas Python):

1. Autenticar seu usuário no terminal:
```bash
gcloud auth login

```


2. Gerar as credenciais locais para o script Python (Application Default Credentials):
```bash
gcloud auth application-default login

```


3. (Opcional) Configurar o projeto ativo para não precisar passá-lo como parâmetro:
```bash
gcloud config set project SEU_PROJECT_ID

```



## Como executar

### Execução Completa (Recomendado)

Para varrer **todos os 14 serviços** mapeados na infraestrutura de uma só vez:

```bash
python3 audit_gcp_resources.py --all

```

### Execução de um Serviço Específico

Para varrer apenas uma categoria específica (ex: Cloud SQL):

```bash
python3 audit_gcp_resources.py --service cloud-sql

```

### Execução com Project ID Manual

Caso você não tenha definido o projeto padrão via `gcloud config set project` ou queira rodar para um projeto diferente do atual:

```bash
python3 audit_gcp_resources.py --all --project MEU_OUTRO_PROJETO_ID

```

## Tratamento de erros

O script identifica e registra situações como:

* Falha de autenticação ou falta do Application Default Credentials.
* API do Cloud Asset desativada no projeto alvo (`PermissionDenied 403`).
* Projeto não especificado e não detectável pela CLI.
* Serviço especificado incorretamente no parâmetro `--service`.

Caso o erro de API desativada ocorra logo após o comando de habilitação, o script retornará uma exceção detalhando que o serviço não pôde ser acessado. Apenas aguarde alguns minutos e tente novamente.

## Resumo em Markdown

Além dos CSVs, o script consolida toda a visão do ambiente no arquivo `relatorio_status_tags.md`.
Ele exibe:

* **Resumo Executivo:** Tabela com os totais de cada serviço.
* **Recursos Parciais:** Exibe as labels atuais, destaca as **tags faltantes** em negrito e mostra se existem tags fora do padrão.
* **Recursos Não Taggeados:** Lista crítica dos recursos órfãos.
* **Recursos Totalmente Taggeados:** Exibe os recursos conformes com as chaves extraídas corretamente nas colunas do Markdown.

## Parâmetros disponíveis

| Parâmetro | Descrição |
| --- | --- |
| `--all` | Varre todos os serviços mapeados no catálogo interno. |
| `--service` | Nome do serviço específico a ser auditado (ex: `app-engine`, `cloud-run`). |
| `--project` | ID do projeto GCP. Opcional caso o terminal já esteja configurado no projeto. |
| `--output-dir` | Diretório onde os relatórios e CSVs serão salvos (Padrão: `auditoria_output`). |

> **Aviso:** É obrigatório fornecer `--all` ou `--service`.

## Fluxo de execução

```text
Autodetecção de Credenciais / Projeto
 │
 ▼
Consulta à API Cloud Asset Inventory
(search_all_resources)
 │
 ▼
Filtragem e Limpeza do Display Name
 │
 ▼
Verificação de Compliance
(team, cost_center, country)
 │
 ▼
Classificação (Listas 1, 2 e 3)
 │
 ├──► Totalmente Taggeados (100% Conformes)
 │
 ├──► Parciais (Fila para adequação) ─────┐
 │                                        │
 └──► Não Taggeados (Órfãos) ─────────────┘
                                          │
                                          ▼
                                Geração Automática dos
                                CSVs (Fila de Trabalho)
                                          │
                                          ▼
                             Geração do Relatório Gerencial
                                (Markdown Consolidado)

```

## Tecnologias utilizadas

* Python 3
* API Google Cloud Asset (`google-cloud-asset`)
* Autenticação Google (`google-auth`)
* Google Cloud SDK (CLI)

## Observações

* O script utiliza acesso estritamente de leitura (Read-Only) e não realiza nenhuma alteração ou deploy na sua infraestrutura.
* O nome das chaves de tags no código obedece estritamente ao seu padrão de governança (`team`, `cost_center`, `country`). Qualquer divergência nelas caracterizará o recurso como "Parcial".
* Em tipos de recursos cujos nomes longos contêm diretórios (ex: Artifact Registry), o script automaticamente isola o nome base do recurso final.