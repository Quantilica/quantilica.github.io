"""Gera os cartões de fontes da landing (`index.html`) a partir do registro público.

O bloco entre os marcadores

    <!-- registro:inicio cartoes -->
    <!-- registro:fim cartoes -->

lista os fetchers com `vitrine`: o link vai direto à página do coletor no site de
documentação (`docs_pasta` e `distribution`) e o código da CLI vem de
`entry_point`. Os textos curados ficam em scripts/destaques.toml, fora do bloco.

Uso:
    python3 scripts/gerar_cartoes.py            reescreve o bloco no index.html
    python3 scripts/gerar_cartoes.py --check    falha se o bloco estiver desatualizado

REGISTRO_LOCAL aponta um registro local (sem rede); ver scripts/registro.py.
"""

import html
import re
import sys
import tomllib
from pathlib import Path

from registro import RegistroError, carregar

RAIZ = Path(__file__).resolve().parents[1]
INDEX = RAIZ / "index.html"
DESTAQUES = Path(__file__).with_name("destaques.toml")
DOCS = "https://docs.quantilica.com"
BLOCO = re.compile(
    r"(?P<ini>[ \t]*<!-- registro:inicio cartoes -->\n)"
    r"(?P<corpo>.*?)"
    r"(?P<fim>[ \t]*<!-- registro:fim cartoes -->\n)",
    re.S,
)


def _esc(texto: str) -> str:
    return html.escape(texto, quote=False)


def link_docs(fetcher: dict) -> str:
    """Página do coletor no site de documentação, sem passar por redirect."""
    pasta = fetcher.get("docs_pasta")
    if not pasta:
        return fetcher["repo"]
    return f"{DOCS}/fontes/{pasta}/{fetcher['distribution']}/"


def cartao(fetcher: dict, destaque: dict, recuo: str) -> str:
    titulo = destaque.get("titulo") or fetcher["nome"]
    texto = destaque.get("texto") or fetcher.get("orgao") or ""
    breve = " <small>em breve na CLI</small>" if destaque.get("em_breve_cli") else ""
    return (
        f'{recuo}<a class="fonte" href="{link_docs(fetcher)}">'
        f"<b>{_esc(titulo)} <code>{_esc(fetcher['entry_point'])}</code>{breve}</b>"
        f"<span>{_esc(texto)}</span></a>\n"
    )


def gera(fetchers: list[dict], destaques: dict, recuo: str) -> str:
    vitrine = {f["id"]: f for f in fetchers if f.get("vitrine")}
    ordem = [i for i in destaques if i in vitrine]
    ordem += sorted(set(vitrine) - set(ordem))
    for i in destaques:
        if i not in vitrine:
            print(
                f"aviso: destaques.toml cita `{i}`, que não é vitrine", file=sys.stderr
            )
    return "".join(cartao(vitrine[i], destaques.get(i, {}), recuo) for i in ordem)


def aplica(texto: str, fetchers: list[dict], destaques: dict) -> str:
    m = BLOCO.search(texto)
    if not m:
        raise SystemExit(
            "index.html: marcadores `registro:inicio cartoes` não encontrados"
        )
    recuo = re.match(r"[ \t]*", m["ini"]).group()
    return (
        texto[: m.start("corpo")]
        + gera(fetchers, destaques, recuo)
        + texto[m.end("corpo") :]
    )


def main(argv: list[str]) -> int:
    destaques = tomllib.loads(DESTAQUES.read_text(encoding="utf-8"))
    try:
        fetchers = carregar()
    except RegistroError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1
    atual = INDEX.read_text(encoding="utf-8")
    novo = aplica(atual, fetchers, destaques)
    if "--check" in argv:
        if novo != atual:
            print(
                "index.html: cartões desatualizados (python3 scripts/gerar_cartoes.py)"
            )
            return 1
        print("cartões em dia")
        return 0
    if novo != atual:
        INDEX.write_text(novo, encoding="utf-8")
    print(f"cartões gerados ({'alterado' if novo != atual else 'sem mudança'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
