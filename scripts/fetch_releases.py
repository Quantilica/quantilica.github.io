"""Gera assets/releases.json com o release mais recente de cada pacote vitrine.

Uso: python3 scripts/fetch_releases.py [saida]
Executado em build-time no GitHub Actions (com GITHUB_TOKEN) e tolerante a
falhas individuais: se um repo não responder, ele é apenas omitido — o site
sempre compila.
"""

import json
import os
import sys
import urllib.error
import urllib.request

ORG = "Quantilica"
REPOS = [
    "quantilica-core",
    "quantilica-cli",
    "sidra-fetcher",
    "bcb-sgs-fetcher",
    "comex-fetcher",
    "datasus-fetcher",
]


def _get(path: str) -> dict:
    req = urllib.request.Request(f"https://api.github.com{path}")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "quantilica-landing")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def latest_release(repo: str) -> dict | None:
    try:
        data = _get(f"/repos/{ORG}/{repo}/releases/latest")
        if data.get("tag_name"):
            return {
                "repo": repo,
                "tag": data["tag_name"],
                "date": (data.get("published_at") or "")[:10],
                "url": data.get("html_url") or f"https://github.com/{ORG}/{repo}",
            }
    except urllib.error.HTTPError as exc:
        if exc.code != 404:  # 404 = repo sem GitHub Releases; tenta tags
            raise
    # Fallback: tag mais recente, datada pelo commit apontado por ela
    tags = _get(f"/repos/{ORG}/{repo}/tags")
    if not tags:
        return None
    tag = tags[0]
    url = f"https://github.com/{ORG}/{repo}/releases/tag/{tag['name']}"
    date = ""
    try:
        commit = _get(f"/repos/{ORG}/{repo}/commits/{tag['commit']['sha']}")
        date = (commit["commit"]["committer"]["date"] or "")[:10]
    except Exception:  # noqa: BLE001 — data é cosmética; não falhe por ela
        pass
    return {"repo": repo, "tag": tag["name"], "date": date, "url": url}


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/releases.json"
    items = []
    for repo in REPOS:
        try:
            rel = latest_release(repo)
        except Exception as exc:  # noqa: BLE001 — tolerância deliberada
            print(f"aviso: {repo}: {exc}", file=sys.stderr)
            continue
        if rel:
            items.append(rel)
    items.sort(key=lambda x: x["date"], reverse=True)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{len(items)} releases -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
