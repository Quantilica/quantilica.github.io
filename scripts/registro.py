"""Carrega o registro público dos fetchers (formato 2) para os scripts do site.

Fonte: https://index.quantilica.com/registry.json. Variáveis de ambiente:
    REGISTRO_LOCAL   caminho de um registry.json local (sem rede).
    REGISTRO_URL     outra URL do registro.

Falha (RegistroError) se o registro não baixar, não for o formato 2 ou se o
`sha256` não bater com o conteúdo.
"""

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

URL_PADRAO = "https://index.quantilica.com/registry.json"
VERSAO_ESPERADA = 2


class RegistroError(RuntimeError):
    """O registro não carregou ou não é o esperado."""


def _sha256(doc: dict) -> str:
    """`{version, fetchers}` em JSON canônico, o mesmo cálculo do índice."""
    canon = json.dumps(
        {"version": doc["version"], "fetchers": doc["fetchers"]},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _baixa(url: str, tentativas: int = 4) -> bytes:
    ultimo: Exception | None = None
    for n in range(tentativas):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "quantilica-landing"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            ultimo = exc
            time.sleep(2**n)
    raise RegistroError(f"registro público indisponível em {url}: {ultimo}")


def carregar() -> list[dict]:
    """Lista de fetchers do registro, validada."""
    local = os.environ.get("REGISTRO_LOCAL")
    if local:
        origem, bruto = local, Path(local).read_bytes()
    else:
        origem = os.environ.get("REGISTRO_URL", URL_PADRAO)
        bruto = _baixa(origem)
    try:
        doc = json.loads(bruto)
    except ValueError as exc:
        raise RegistroError(f"registro de {origem} não é JSON: {exc}") from exc
    if doc.get("version") != VERSAO_ESPERADA:
        raise RegistroError(
            f"registro de {origem}: formato {doc.get('version')!r}, "
            f"esperado {VERSAO_ESPERADA}"
        )
    if doc.get("sha256") != _sha256(doc):
        raise RegistroError(f"registro de {origem}: sha256 não bate com o conteúdo")
    fetchers = doc.get("fetchers")
    if not isinstance(fetchers, list) or not fetchers:
        raise RegistroError(f"registro de {origem}: sem fetchers")
    return fetchers


def nome_do_repo(fetcher: dict) -> str:
    """Nome do repositório no GitHub (último trecho do campo `repo`)."""
    return fetcher["repo"].rstrip("/").rsplit("/", 1)[-1]
