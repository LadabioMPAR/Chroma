"""Leitura do config.toml central e resolução de caminhos.

Todos os caminhos relativos do config são resolvidos a partir da raiz do
repositório, para que os scripts funcionem independentemente do diretório
de onde forem executados.
"""

import os
import json
import tomllib

# Raiz do repositório = pasta que contém este pacote.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def repo_root():
    return _ROOT


def load_config(path=None):
    """Carrega o config.toml. Se `path` for None, usa <raiz>/config.toml."""
    if path is None:
        path = os.path.join(_ROOT, "config.toml")
    with open(path, "rb") as f:
        return tomllib.load(f)


def resolve(path):
    """Resolve um caminho relativo em relação à raiz do repositório.

    Caminhos já absolutos são devolvidos sem alteração.
    """
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(_ROOT, path))


def ensure_dir(path):
    """Cria o diretório (resolvido) se não existir e devolve o caminho absoluto."""
    abs_path = resolve(path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def save_ktheta(path, k, theta, extra=None):
    """Grava k e theta (e metadados opcionais) em JSON, para o passo 04 consumir."""
    abs_path = resolve(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    data = {"k": float(k), "theta": float(theta)}
    if extra:
        data.update(extra)
    with open(abs_path, "w") as f:
        json.dump(data, f, indent=2)
    return abs_path


def load_ktheta(path):
    """Lê k e theta de um JSON gravado pelo passo 03. Devolve (k, theta)."""
    abs_path = resolve(path)
    with open(abs_path, "r") as f:
        data = json.load(f)
    return float(data["k"]), float(data["theta"])
