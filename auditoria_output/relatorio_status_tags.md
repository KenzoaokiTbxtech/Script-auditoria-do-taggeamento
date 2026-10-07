# Relatório de Auditoria de Governança de Tags/Labels

**Padrão obrigatório avaliado:** `team`, `cost_center`, `country`

## 1. Resumo Executivo

| Serviço | Total | 1. Taggeados (100%) | 2. Parciais (Incompletos) | 3. Não Taggeados |
|---|---|---|---|---|
| `app-engine` | 2 | 0 | 0 | **2** |
| `artifact-registry` | 3 | 2 | 0 | **1** |
| `buckets-storage` | 0 | 0 | 0 | **0** |
| `cloud-dns` | 0 | 0 | 0 | **0** |
| `cloud-run` | 0 | 0 | 0 | **0** |
| `cloud-sql` | 0 | 0 | 0 | **0** |
| `forwarding-rules` | 0 | 0 | 0 | **0** |
| `gke` | 0 | 0 | 0 | **0** |
| `global-forwarding-rules` | 0 | 0 | 0 | **0** |
| `memory-store` | 0 | 0 | 0 | **0** |
| `pubsub-subscriptions` | 0 | 0 | 0 | **0** |
| `pubsub-topics` | 0 | 0 | 0 | **0** |
| `secret-manager` | 0 | 0 | 0 | **0** |
| `virtual-machine(vm)` | 0 | 0 | 0 | **0** |
| **TOTAL GERAL** | **5** | **2** | **0** | **3** |

---

## 2. Recursos Parciais (Necessitam de Adequação)

## 3. Recursos Não Taggeados (Críticos)

### `app-engine`
| Recurso | Região | Caminho Completo |
|---|---|---|
| `tbx-kenzo-aoki-495513` | us-central1 | `//appengine.googleapis.com/projects/tbx-kenzo-aoki-495513/locations/us-central1/applications/tbx-kenzo-aoki-495513` |
| `tbx-kenzo-aoki-495513` | us-central | `//appengine.googleapis.com/apps/tbx-kenzo-aoki-495513` |

### `artifact-registry`
| Recurso | Região | Caminho Completo |
|---|---|---|
| `gae-standard` | us-central1 | `//artifactregistry.googleapis.com/projects/tbx-kenzo-aoki-495513/locations/us-central1/repositories/gae-standard` |

## 4. Recursos Totalmente Taggeados (Conformes)

### `artifact-registry`
| Recurso | Team | Cost_Center | Country | Tags Extras |
|---|---|---|---|---|
| `teste-labels2` | eng | cc001 | br | - |
| `teste-labels1` | devops | cc002 | br | - |

