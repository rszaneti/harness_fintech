#!/usr/bin/env python3
"""
workspaces.py — leitor ÚNICO de `.claude/workspaces.json` (spec 001, plan 2.8.1).

Até a spec 001 havia sete listas de workspaces fixas no código (gate, hook pós-edição, scaffold,
check-module, diff-classify, check-ui-v2-refs, block-shell-write-ts), e elas já divergiam: o gate
e o hook conheciam `portal`/`professional`, o scaffold não. Agora quem precisa saber quais
workspaces existem pergunta aqui — Python importa `load()`, Bash chama a CLI.

Uso:
  python3 .claude/scripts/workspaces.py --list                 chaves, uma por linha
  python3 .claude/scripts/workspaces.py --path <ws> [--root R] caminho absoluto do workspace
  python3 .claude/scripts/workspaces.py --kind <ws>            backend | frontend
  python3 .claude/scripts/workspaces.py --spec <ws>            spec prevista para criá-lo
  python3 .claude/scripts/workspaces.py --group <alvo>         workspaces de um alvo do gate
                                                               (backend, frontend, all ou a chave)
  python3 .claude/scripts/workspaces.py --which <arquivo>      chave do workspace que contém o
                                                               arquivo (vazio se nenhum)
  python3 .claude/scripts/workspaces.py --which-dir <arquivo>  diretório desse workspace, recortado
                                                               do caminho do arquivo
  python3 .claude/scripts/workspaces.py --self-test            consistência do JSON e das consultas
  python3 .claude/scripts/workspaces.py --scan                 executável do harness que cita
                                                               workspace fora do JSON (CA-06)

`--which` casa o caminho do workspace como SEGMENTO em qualquer ponto do caminho do arquivo
(`*/backend/api/*`), não como prefixo da raiz — é a semântica que o `post-edit-check.sh` sempre
teve, e é o que permite sondar o hook com um arquivo fora do checkout.

Exit: 0 ok · 1 workspace desconhecido · 2 self-test/scan reprovado · 64 uso
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
JSON_PATH = HERE.parent / "workspaces.json"
KINDS = {"backend", "frontend"}
FIXTURES_SEG = "/.claude/scripts/tests/"


def load() -> dict[str, dict[str, str]]:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def path_of(ws: str, root: Path = ROOT) -> Path:
    return root / load()[ws]["path"]


def paths(root: Path = ROOT) -> dict[str, Path]:
    """{chave: caminho absoluto} — é o `WS = {...}` que cada script tinha fixo."""
    return {k: root / v["path"] for k, v in load().items()}


def of_kind(kind: str) -> list[str]:
    return [k for k, v in load().items() if v["kind"] == kind]


def group(target: str) -> list[str]:
    data = load()
    if target == "all":
        return list(data)
    if target == "frontend":
        return of_kind("frontend")
    if target in data:
        return [target]
    raise KeyError(target)


def which_dir(file: str) -> str:
    """Diretório do workspace que contém o arquivo, recortado do PRÓPRIO caminho do arquivo — não
    da raiz do checkout. É o `${FILE%%/<path>/*}/<path>` que o hook pós-edição fazia por `case`."""
    k = which(file)
    if not k:
        return ""
    rel = load()[k]["path"].strip("/")
    f = file.replace("\\", "/")
    i = f.find(f"/{rel}/")
    return f[: i + 1 + len(rel)]


def which(file: str) -> str:
    f = "/" + file.replace("\\", "/").lstrip("/")
    # FIXTURE do harness nunca é de workspace: os hooks financeiros testam com mini-workspaces em
    # `.claude/scripts/tests/<hook>/backend/api/src/…`, e o hook pós-edição as reprovaria a cada
    # gravação pelo que elas existem para exibir (AG-013 aplicada a caminho). ⚠️ SÓ esse diretório:
    # a 1ª versão excluía qualquer `/.claude/`, e um worktree em `.claude/worktrees/<x>/backend/api/`
    # desligava em silêncio ESLint, lessons e os 4 hooks (achado MÉDIA da 1ª auditoria da spec 001).
    if FIXTURES_SEG in f:
        return ""
    # o caminho MAIS LONGO vence: um workspace aninhado em outro não pode ser engolido pelo pai
    for k, v in sorted(load().items(), key=lambda kv: -len(kv[1]["path"])):
        if f"/{v['path'].strip('/')}/" in f:
            return k
    return ""


# ----------------------------------------------------------------------------- self-test
# Caminho de workspace citado em arquivo EXECUTÁVEL do harness tem de estar no JSON (CA-06). A
# prosa (.md) não entra: ela pode citar o ERP de origem — as lessons citam, de propósito (RN-06).
WS_LIKE = re.compile(r"\b(backend|frontend|tools)/([a-z][a-z0-9_-]+)")
SCAN_SUFFIXES = {".py", ".sh", ".json"}
SCAN_SKIP = {"gate", "projects", "__pycache__", "specs"}


def scan_paths(base: Path = ROOT / ".claude") -> list[str]:
    known = {v["path"] for v in load().values()}
    found = []
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(base)
        if not p.is_file() or p.suffix not in SCAN_SUFFIXES:
            continue
        if any(part in SCAN_SKIP or part.startswith("_backup") for part in rel.parts):
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for cited in _scan_line(line, known):
                found.append(f".claude/{rel}:{n} cita '{cited}', que não está em workspaces.json")
    return found


def _scan_line(line: str, known: set[str] | None = None) -> list[str]:
    known = known if known is not None else {v["path"] for v in load().values()}
    groups = {"backend", "frontend", "tools"}  # `backend/frontend` em prosa não é caminho
    out = []
    for m in WS_LIKE.finditer(line):
        if m.group(2) in groups:
            continue
        # `templates/backend/migration.ts.tpl` é TEMPLATE, não workspace: caminho de workspace é
        # diretório — nunca vem seguido de extensão nem mora sob `templates/`.
        if line[m.end():m.end() + 1] == "." or line[:m.start()].endswith("templates/"):
            continue
        cited = f"{m.group(1)}/{m.group(2)}"
        if cited not in known:
            out.append(cited)
    return out


def self_test() -> int:
    fails: list[str] = []
    data = load()
    seen: set[str] = set()
    for k, v in data.items():
        if set(v) != {"path", "kind", "spec"}:
            fails.append(f"{k}: chaves {sorted(v)} — esperado path, kind, spec")
            continue
        if v["kind"] not in KINDS:
            fails.append(f"{k}: kind '{v['kind']}' fora de {sorted(KINDS)}")
        if not re.fullmatch(r"\d{3}", v["spec"]):
            fails.append(f"{k}: spec '{v['spec']}' não é NNN")
        if v["path"] in seen:
            fails.append(f"{k}: caminho repetido {v['path']}")
        seen.add(v["path"])
        probe = f"/qualquer/lugar/{v['path']}/src/a.ts"
        if which(probe) != k:
            fails.append(f"--which {probe} devolveu '{which(probe)}', esperado '{k}'")
        if which_dir(probe) != f"/qualquer/lugar/{v['path']}":
            fails.append(f"--which-dir {probe} devolveu '{which_dir(probe)}'")
        # sem a barra final, um irmão de nome mais longo (`<path>2/`) não pode casar `<path>`
        if which(f"/x/{v['path']}2/src/a.ts"):
            fails.append(f"--which casou prefixo de nome: {v['path']}2")
    # Os caminhos do ERP montados por partes: escritos inteiros, o `--scan` acusaria esta sonda.
    erp = ["/".join(("frontend", "admin")), "/".join(("backend", "admin"))]
    primeiro = data[next(iter(data))]["path"]
    harness_fixture = "/r/.claude/scripts/tests/h/" + primeiro + "/src/a.ts"
    for probe in [f"/x/{e}/src/a.ts" for e in erp] + ["/x/src/a.ts", harness_fixture]:
        if which(probe):
            fails.append(f"--which {probe} devolveu '{which(probe)}', esperado vazio")
    # O detector do --scan, contra caso conhecido e não-caso (AG-020):
    acusa = "/".join(("frontend", "admin")) + "/src"
    limpo = ["templates/" + "/".join(("backend", "migration")) + ".ts.tpl",
             "/".join(("backend", "migration")) + "-alter.ts.tpl", "backend/frontend"]
    if not _scan_line(acusa):
        fails.append(f"--scan não acusa '{acusa}'")
    for l in limpo:
        if _scan_line(l):
            fails.append(f"--scan acusa o não-caso '{l}'")
    # …mas worktree dentro de `.claude/` CONTINUA sendo workspace
    worktree = "/r/.claude/worktrees/w1/" + primeiro + "/src/a.ts"
    if which(worktree) != next(iter(data)):
        fails.append(f"--which {worktree} devolveu '{which(worktree)}' — worktree tem de ser workspace")
    if sorted(group("frontend")) != sorted(of_kind("frontend")):
        fails.append("--group frontend difere de kind=frontend")
    if group("all") != list(data):
        fails.append("--group all difere da lista do JSON")
    for f in fails:
        print("  ❌ " + f)
    if fails:
        print(f"\n❌ workspaces --self-test REPROVADO ({len(fails)} falha(s))")
        return 2
    print(f"✅ workspaces --self-test: {len(data)} workspaces, --which e --group consistentes")
    return 0


def scan() -> int:
    found = scan_paths()
    for f in found:
        print("  ❌ " + f)
    if found:
        print(f"\n❌ workspaces --scan: {len(found)} citação(ões) de workspace fora do JSON")
        return 2
    print("✅ workspaces --scan: nenhum executável do harness cita workspace fora do JSON")
    return 0


# ----------------------------------------------------------------------------- cli
def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 64
    root = ROOT
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            return 64
        root = Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    cmd, arg = argv[0], (argv[1] if len(argv) > 1 else None)
    data = load()
    if cmd == "--self-test":
        return self_test()
    if cmd == "--scan":
        return scan()
    if cmd == "--list":
        print("\n".join(data))
        return 0
    if cmd == "--which" and arg is not None:
        print(which(arg))
        return 0
    if cmd == "--which-dir" and arg is not None:
        print(which_dir(arg))
        return 0
    if cmd == "--group" and arg:
        try:
            print("\n".join(group(arg)))
        except KeyError:
            return 1
        return 0
    if cmd in ("--path", "--kind", "--spec") and arg:
        if arg not in data:
            return 1
        print(root / data[arg]["path"] if cmd == "--path" else data[arg][cmd[2:]])
        return 0
    print(__doc__, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
