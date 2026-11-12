#!/usr/bin/env python3
"""
Verifica e atualiza as dependências reais dos Helm charts deste repositório.

A versão "atual" de cada dependência vem do Chart.lock (versão realmente
travada/baixada), não do campo `version` do Chart.yaml do chart wrapper
(que é a versão do wrapper, não da dependência).
"""

import json
import os
import subprocess
import sys
from urllib.parse import urlparse

import yaml
from packaging.version import InvalidVersion, Version

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
HELM_DIR = os.path.join(REPO_ROOT, "charts")

IGNORE_DIRS = {".git", ".github", ".gitlab", "node_modules", ".terraform", ".idea", ".vscode"}


def run(command, cwd=None):
    return subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def find_chart_dirs(base):
    chart_dirs = []

    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        if "Chart.yaml" in files:
            chart_dirs.append(root)

    return sorted(chart_dirs)


def read_lock_dependencies(chart_dir):
    """Lê as dependências travadas (nome, repositório, versão real) do Chart.lock."""

    lock_path = os.path.join(chart_dir, "Chart.lock")

    if not os.path.isfile(lock_path):
        return []

    with open(lock_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data.get("dependencies") or []


def collect_items():
    items = []
    dep_urls = set()

    for chart_dir in find_chart_dirs(HELM_DIR):
        rel_chart_dir = os.path.relpath(chart_dir, REPO_ROOT)
        deps = read_lock_dependencies(chart_dir)

        if not deps:
            print(
                f"AVISO: sem Chart.lock em {rel_chart_dir} "
                f"— rode 'helm dependency update {rel_chart_dir}' primeiro."
            )
            continue

        for dep in deps:
            name = dep.get("name")
            url = (dep.get("repository") or "").rstrip("/")
            current = dep.get("version")

            if not name or not url or not current:
                continue

            dep_urls.add(url)
            items.append(
                {
                    "chart_dir": rel_chart_dir,
                    "name": name,
                    "repository": url,
                    "current": current,
                    "latest": None,
                    "status": None,
                }
            )

    return items, dep_urls


def alias_for_url(url, alias_map):
    netloc = urlparse(url).netloc or url
    base_alias = netloc.replace(".", "-")

    alias = base_alias
    existing_aliases = set(alias_map.values())
    suffix = 2

    while alias in existing_aliases:
        alias = f"{base_alias}-{suffix}"
        suffix += 1

    return alias


def list_repos():
    result = run(["helm", "repo", "list", "-o", "json"])

    if result.returncode != 0 or not result.stdout.strip():
        return {}

    try:
        repos = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

    return {item["url"].rstrip("/"): item["name"] for item in repos}


def ensure_repos(dep_urls):
    """Garante que todos os repositórios usados pelas dependências estejam
    adicionados localmente e com o índice atualizado."""

    alias_map = list_repos()

    for url in sorted(dep_urls):
        if url in alias_map:
            continue

        alias = alias_for_url(url, alias_map)
        print(f"Adicionando repositório: {alias} -> {url}")

        add_result = run(["helm", "repo", "add", alias, url])
        if add_result.returncode != 0:
            print(f"  AVISO: falha ao adicionar {url}: {add_result.stderr.strip()}")
            continue

        alias_map[url] = alias

    print("Atualizando índices dos repositórios (helm repo update)...")
    update_result = run(["helm", "repo", "update"])
    if update_result.returncode != 0:
        print(f"AVISO: helm repo update falhou: {update_result.stderr.strip()}")

    return alias_map


def get_latest_version(alias, chart_name):
    result = run(["helm", "search", "repo", f"{alias}/{chart_name}", "--versions", "-o", "json"])

    if result.returncode != 0 or not result.stdout.strip():
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    versions = []

    for entry in data:
        # helm search repo faz match por substring; garante que é o chart exato
        if entry.get("name", "").split("/")[-1] != chart_name:
            continue

        version = entry.get("version")
        if not version:
            continue

        try:
            versions.append(Version(version))
        except InvalidVersion:
            continue

    if not versions:
        return None

    return str(max(versions))


def compare(current, latest):
    try:
        if Version(latest) > Version(current):
            return "UPDATE"
        if Version(latest) == Version(current):
            return "OK"
        return "AHEAD"
    except InvalidVersion:
        return "INVALID VERSION"


def fetch_latest_versions(items, alias_map):
    print("\nConsultando versões mais recentes...")

    for item in items:
        alias = alias_map.get(item["repository"])

        if not alias:
            item["status"] = "REPO NAO ENCONTRADO"
            continue

        latest = get_latest_version(alias, item["name"])
        item["latest"] = latest

        if not latest:
            item["status"] = "NAO ENCONTRADO"
        else:
            item["status"] = compare(item["current"], latest)


def print_menu(items):
    print()
    print("=" * 100)
    print("DEPENDÊNCIAS DOS HELM CHARTS")
    print("=" * 100)
    print(f"{'#':>3}  {'CHART':38} {'DEPENDÊNCIA':26} {'ATUAL':12} {'MAIS RECENTE':14} STATUS")
    print("-" * 100)

    for i, item in enumerate(items, start=1):
        print(
            f"{i:>3}  {item['chart_dir'][:38]:38} {item['name'][:26]:26} "
            f"{str(item['current'])[:12]:12} {str(item['latest'])[:14]:14} {item['status']}"
        )

    print("-" * 100)


def parse_selection(raw, items):
    raw = raw.strip().lower()

    if raw in ("", "q", "sair"):
        return None

    if raw == "a":
        return [i for i, item in enumerate(items) if item["status"] == "UPDATE"]

    indices = []
    for token in raw.replace(" ", "").split(","):
        if not token:
            continue
        if not token.isdigit():
            print(f"  Ignorando entrada inválida: {token}")
            continue

        idx = int(token) - 1
        if 0 <= idx < len(items):
            indices.append(idx)
        else:
            print(f"  Ignorando número fora do intervalo: {token}")

    return indices


def apply_updates(items, indices):
    chart_dirs = sorted({items[i]["chart_dir"] for i in indices})

    print("\nVocê selecionou atualizar as dependências de:")
    for chart_dir in chart_dirs:
        print(f"  - {chart_dir}")

    confirm = input("Confirmar? (s/N): ").strip().lower()
    if confirm != "s":
        print("Atualização cancelada.")
        return set()

    updated_dirs = set()

    for chart_dir in chart_dirs:
        print(f"\nRodando: helm dependency update {chart_dir}")
        result = run(["helm", "dependency", "update", chart_dir], cwd=REPO_ROOT)

        if result.stdout:
            print(result.stdout.strip())

        if result.returncode != 0:
            print(f"ERRO ao atualizar {chart_dir}:\n{result.stderr.strip()}")
            continue

        updated_dirs.add(chart_dir)

    return updated_dirs


def refresh_after_update(items, updated_dirs):
    for item in items:
        if item["chart_dir"] not in updated_dirs:
            continue

        deps = read_lock_dependencies(os.path.join(REPO_ROOT, item["chart_dir"]))
        for dep in deps:
            if dep.get("name") == item["name"]:
                item["current"] = dep.get("version")

        if item["latest"]:
            item["status"] = compare(item["current"], item["latest"])


def main():
    print("=" * 100)
    print("VERIFICAÇÃO E ATUALIZAÇÃO DE DEPENDÊNCIAS DOS HELM CHARTS")
    print("=" * 100)

    items, dep_urls = collect_items()

    if not items:
        print("\nNenhuma dependência travada (Chart.lock) encontrada.")
        sys.exit(0)

    alias_map = ensure_repos(dep_urls)
    fetch_latest_versions(items, alias_map)

    while True:
        print_menu(items)
        raw = input(
            "\nDigite os números (separados por vírgula) para atualizar, "
            "'a' = todas com UPDATE, ou Enter/'q' para sair: "
        )

        selection = parse_selection(raw, items)
        if selection is None:
            break

        if not selection:
            print("Nenhuma seleção válida.")
            continue

        updated_dirs = apply_updates(items, selection)
        if updated_dirs:
            refresh_after_update(items, updated_dirs)

    print("\nFinalizado.")


if __name__ == "__main__":
    main()
