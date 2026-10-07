#!/usr/bin/env python3
"""
audit_gcp_resources.py

Audita todos os recursos do GCP com base nos serviços mapeados.
Classifica em 3 listas:
  1. TOTALMENTE TAGGEADOS (Possui todas as tags obrigatórias)
  2. TAGGEADOS PARCIAIS (Faltam tags obrigatórias ou tem chaves diferentes)
  3. NÃO TAGGEADOS (Sem nenhum rótulo)
"""

import argparse
import csv
import os
import subprocess
import sys
from google.cloud import asset_v1
import google.auth

# CORREÇÃO: Usando cost_center (com underline) para refletir a tag real da sua infraestrutura
REQUIRED_TAGS = {"team", "cost_center", "country"}

SERVICES_MAP = {
    "app-engine": ["appengine.googleapis.com/Application"],
    "artifact-registry": ["artifactregistry.googleapis.com/Repository"],
    "buckets-storage": ["storage.googleapis.com/Bucket"],
    "cloud-dns": ["dns.googleapis.com/ManagedZone"],
    "cloud-run": ["run.googleapis.com/Service"],
    "cloud-sql": ["sqladmin.googleapis.com/Instance"],
    "forwarding-rules": ["compute.googleapis.com/ForwardingRule"],
    "gke": ["container.googleapis.com/Cluster"],
    "global-forwarding-rules": ["compute.googleapis.com/ForwardingRule"],
    "memory-store": ["redis.googleapis.com/Instance"],
    "pubsub-subscriptions": ["pubsub.googleapis.com/Subscription"],
    "pubsub-topics": ["pubsub.googleapis.com/Topic"],
    "secret-manager": ["secretmanager.googleapis.com/Secret"],
    "virtual-machine(vm)": ["compute.googleapis.com/Instance"]
}

def obter_projeto_padrao():
    try:
        _, project = google.auth.default()
        if project: return project
    except Exception:
        pass
    try:
        resultado = subprocess.run(
            ["gcloud", "config", "get-value", "project"], 
            capture_output=True, text=True, check=True
        )
        project = resultado.stdout.strip()
        if project: return project
    except Exception:
        pass
    return None

def classificar_recurso(labels_dict: dict):
    if not labels_dict:
        return "UNTAGGED", list(REQUIRED_TAGS), []

    chaves_presentes = set(labels_dict.keys())
    faltantes = list(REQUIRED_TAGS - chaves_presentes)
    extras = list(chaves_presentes - REQUIRED_TAGS)

    if not faltantes:
        return "TAGGED", [], extras
    else:
        return "PARTIAL", faltantes, extras

def extrair_nome_recurso(full_name: str) -> str:
    # CORREÇÃO: Força sempre pegar a última parte do caminho ignorando o nome longo do GCP
    return full_name.split("/")[-1]

def auditar_servico(client, scope: str, service_name: str, asset_types: list):
    print(f"[*] Buscando recursos de '{service_name}'...")
    
    request = asset_v1.SearchAllResourcesRequest(
        scope=scope,
        asset_types=asset_types,
        read_mask="name,displayName,labels,location,assetType"
    )

    results = client.search_all_resources(request=request)

    tagged = []
    partial = []
    untagged = []

    for item in results:
        if service_name == "global-forwarding-rules" and item.location != "global":
            continue
        if service_name == "forwarding-rules" and item.location == "global":
            continue

        labels = dict(item.labels) if item.labels else {}
        recurso_nome = extrair_nome_recurso(item.name)
        categoria, faltantes, extras = classificar_recurso(labels)

        item_info = {
            "recurso": recurso_nome,
            "team": labels.get("team", ""),
            "cost_center": labels.get("cost_center", ""), # Atualizado para cost_center
            "country": labels.get("country", ""),
            "todas_labels": "; ".join([f"{k}={v}" for k, v in labels.items()]) if labels else "NENHUMA",
            "faltantes": ", ".join(faltantes) if faltantes else "-",
            "extras": ", ".join(extras) if extras else "-",
            "location": item.location,
            "full_name": item.name
        }

        if categoria == "TAGGED":
            tagged.append(item_info)
        elif categoria == "PARTIAL":
            partial.append(item_info)
        else:
            untagged.append(item_info)

    return tagged, partial, untagged

def salvar_csv_para_taggeamento(caminho_csv: str, lista_recursos: list):
    cabecalho = ["recurso", "team", "cost_center", "country"] # Atualizado para cost_center
    with open(caminho_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cabecalho, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(lista_recursos)

def gerar_relatorio_md(dados_completos: list, caminho_md: str):
    with open(caminho_md, mode="w", encoding="utf-8") as f:
        f.write("# Relatório de Auditoria de Governança de Tags/Labels\n\n")
        f.write("**Padrão obrigatório avaliado:** `team`, `cost_center`, `country`\n\n")
        
        f.write("## 1. Resumo Executivo\n\n")
        f.write("| Serviço | Total | 1. Taggeados (100%) | 2. Parciais (Incompletos) | 3. Não Taggeados |\n")
        f.write("|---|---|---|---|---|\n")

        total_geral = total_tag = total_part = total_untag = 0

        for d in dados_completos:
            t = len(d["tagged"])
            p = len(d["partial"])
            u = len(d["untagged"])
            tot = t + p + u
            
            total_geral += tot
            total_tag += t
            total_part += p
            total_untag += u
            
            f.write(f"| `{d['service']}` | {tot} | {t} | {p} | **{u}** |\n")

        f.write(f"| **TOTAL GERAL** | **{total_geral}** | **{total_tag}** | **{total_part}** | **{total_untag}** |\n\n")
        f.write("---\n\n")

        f.write("## 2. Recursos Parciais (Necessitam de Adequação)\n\n")
        for d in dados_completos:
            if d["partial"]:
                f.write(f"### `{d['service']}`\n")
                f.write("| Recurso | Labels Atuais | Tags Faltantes | Tags Extras/Diferentes |\n")
                f.write("|---|---|---|---|\n")
                for r in d["partial"]:
                    # Agora imprime o nome curto
                    f.write(f"| `{r['recurso']}` | {r['todas_labels']} | **{r['faltantes']}** | {r['extras']} |\n")
                f.write("\n")

        f.write("## 3. Recursos Não Taggeados (Críticos)\n\n")
        for d in dados_completos:
            if d["untagged"]:
                f.write(f"### `{d['service']}`\n")
                f.write("| Recurso | Região | Caminho Completo |\n")
                f.write("|---|---|---|\n")
                for r in d["untagged"]:
                    # Nome curto na primeira coluna
                    f.write(f"| `{r['recurso']}` | {r['location']} | `{r['full_name']}` |\n")
                f.write("\n")

        f.write("## 4. Recursos Totalmente Taggeados (Conformes)\n\n")
        for d in dados_completos:
            if d["tagged"]:
                f.write(f"### `{d['service']}`\n")
                f.write("| Recurso | Team | Cost_Center | Country | Tags Extras |\n")
                f.write("|---|---|---|---|---|\n")
                for r in d["tagged"]:
                    # Nome curto
                    f.write(f"| `{r['recurso']}` | {r['team']} | {r['cost_center']} | {r['country']} | {r['extras']} |\n")
                f.write("\n")

def main():
    parser = argparse.ArgumentParser(description="Auditoria Completa de Tags GCP.")
    parser.add_argument("--project", help="ID do projeto GCP (Opcional se já autenticado no gcloud)")
    parser.add_argument("--service", choices=list(SERVICES_MAP.keys()), help="Auditar um serviço específico")
    parser.add_argument("--all", action="store_true", help="Auditar TODOS os serviços de uma vez")
    parser.add_argument("--output-dir", default="auditoria_output", help="Diretório onde os CSVs serão salvos")
    args = parser.parse_args()

    if not args.service and not args.all:
        print("Erro: Defina --service <nome_do_servico> ou --all para rodar em todos.")
        sys.exit(1)

    project_id = args.project or obter_projeto_padrao()
    
    if not project_id:
        print("Erro: Não foi possível determinar o Project ID automaticamente.")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    scope = f"projects/{project_id}"
    client = asset_v1.AssetServiceClient()

    servicos_para_auditar = list(SERVICES_MAP.keys()) if args.all else [args.service]
    dados_consolidados = []

    print(f"Iniciando auditoria no projeto: {project_id}\n")

    for s_name in servicos_para_auditar:
        tagged, partial, untagged = auditar_servico(client, scope, s_name, SERVICES_MAP[s_name])
        
        pendencias = partial + untagged
        if pendencias:
            csv_path = os.path.join(args.output_dir, f"{s_name}_pendentes.csv")
            salvar_csv_para_taggeamento(csv_path, pendencias)
            print(f" -> {len(pendencias)} pendências encontradas. CSV criado: {csv_path}")
        else:
            print(f" -> 100% Conforme! Nenhum CSV gerado para {s_name}.")

        dados_consolidados.append({
            "service": s_name,
            "tagged": tagged,
            "partial": partial,
            "untagged": untagged
        })

    relatorio_md_path = os.path.join(args.output_dir, "relatorio_status_tags.md")
    gerar_relatorio_md(dados_consolidados, relatorio_md_path)
    
    print(f"\n[✓] Auditoria concluída com sucesso!")
    print(f"[✓] Relatório consolidado e arquivos CSV salvos na pasta: ./{args.output_dir}/")

if __name__ == "__main__":
    main()