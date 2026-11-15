"""Chaves do destaques.toml resolvidas pelo registro (id, apelido e historico)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import gerar_cartoes as gc  # noqa: E402


def f(fid, *, vitrine=True, aliases=(), historico=()):
    return {
        "id": fid,
        "nome": fid.upper(),
        "orgao": "Órgão",
        "vitrine": vitrine,
        "entry_point": fid,
        "distribution": f"{fid}-fetcher",
        "docs_pasta": "x",
        "repo": f"https://github.com/Quantilica/{fid}-fetcher",
        "aliases": list(aliases),
        "historico": [{"id": h, "distribution": f"{h}-fetcher"} for h in historico],
    }


DESTAQUES = {
    "bcb-sgs": {"titulo": "Banco Central", "texto": "Séries"},
    "sidra": {"titulo": "IBGE SIDRA", "texto": "Macro", "em_breve_cli": True},
    "comex": {"titulo": "Comex Stat", "texto": "Comércio"},
}


def titulos(html: str) -> list[str]:
    return [ln.split("<b>")[1].split(" <code>")[0] for ln in html.splitlines()]


def test_chave_por_id_continua_valendo():
    fs = [f("bcb-sgs"), f("comex")]
    out = gc.gera(fs, {"comex": {"titulo": "Comex Stat"}}, "")
    assert titulos(out)[0] == "Comex Stat"


def test_fetcher_de_vitrine_renomeado_mantem_o_destaque_pelo_historico():
    # `sidra` (chave antiga do destaques.toml) virou `ibge-sidra`
    fs = [f("bcb-sgs"), f("ibge-sidra", historico=["sidra"]), f("comex")]
    out = gc.gera(fs, DESTAQUES, "    ")
    assert titulos(out) == ["Banco Central", "IBGE SIDRA", "Comex Stat"]
    assert "em breve na CLI" in out
    assert "Macro" in out


def test_chave_por_apelido():
    fs = [f("ibge-sidra", aliases=["sidra"])]
    out = gc.gera(fs, {"sidra": {"titulo": "IBGE SIDRA"}}, "")
    assert titulos(out) == ["IBGE SIDRA"]


def test_ordem_do_arquivo_e_mantida_com_chave_renomeada():
    fs = [f("a-x"), f("novo-y", historico=["b-y"]), f("c-z")]
    d = {"a-x": {}, "b-y": {"titulo": "B"}, "c-z": {}}
    assert list(gc.resolve_destaques(fs, d)) == ["a-x", "novo-y", "c-z"]


def test_id_novo_e_antigo_juntos_e_erro():
    fs = [f("ibge-sidra", historico=["sidra"])]
    with pytest.raises(SystemExit, match="mesmo fetcher"):
        gc.resolve_destaques(fs, {"sidra": {}, "ibge-sidra": {}})


def test_chave_que_nao_e_vitrine_avisa_e_nao_gera(capsys):
    fs = [f("a-x"), f("b-y", vitrine=False, historico=["velho"])]
    out = gc.gera(fs, {"velho": {"titulo": "Velho"}}, "")
    assert "Velho" not in out
    assert "`b-y`, que não é vitrine" in capsys.readouterr().err


def test_apelido_de_um_fetcher_nao_rouba_o_id_de_outro():
    fs = [f("a-x", aliases=["b-y"]), f("b-y")]
    assert list(gc.resolve_destaques(fs, {"b-y": {"titulo": "B"}})) == ["b-y"]
