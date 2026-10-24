#!/usr/bin/env python3
"""
diff-classify.py — etiqueta o diff para o `verifier` carregar SÓ o que se aplica (spec 087 / §F4).

O `verifier.md` carregava as lessons condicionais inteiras em toda auditoria — FE-020 ("se trocar
modo de montagem"), AG-011 ("se corrigir bug"), FE-022 ("se tocar conversor numérico") — e o
agente lia todas para decidir que nenhuma se aplicava. Aqui o diff é classificado por uma regra
mecânica, e cada etiqueta aponta para UM arquivo de `.claude/verifier-checks/`.

Uso:
  python3 .claude/scripts/diff-classify.py --feature <nome> [--since <ref>] [--json]
  python3 .claude/scripts/diff-classify.py --list-tags     # falha se alguma etiqueta não tiver check

⚠️ `--feature` é OBRIGATÓRIO. Sem ele a etiqueta `bugfix` teria de varrer todas as specs de
`em_andamento/` — e alguma sempre fala em correção, então ela acenderia sempre. Etiqueta que
acende sempre não classifica nada (foi o que aconteceu no piloto V-Corp).

Exit: 0 ok · 2 etiqueta sem check (ou `--list-tags` com buraco) · 64 uso · 65 feature inexistente
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHECKS = ROOT / ".claude/verifier-checks"
# Workspaces de `.claude/workspaces.json` (spec 001); o nome que prefixa cada arquivo é a chave.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import workspaces  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
import financial_rules  # noqa: E402  (escopo financeiro num lugar só)

WS = workspaces.paths(ROOT)
SPECS = ROOT / ".claude/specs"

# etiqueta → (o que ela significa para quem audita)
TAGS = {
    "migration": "schema mudou — guarda por operação, PK uuid, entity × tabela",
    "routes": "rota ou controller mudou — ordem, permissão, filtro booleano",
    "mount-mode": "o modo de montagem de um componente mudou — estado que morre ou congela",
    "bugfix": "a feature CORRIGE um defeito — alcançabilidade e teste que prova",
    "number-field": "campo numérico ou conversor — o Formik coage antes do seu código ver",
    "enum": "enum novo ou alterado — espelho, travessia e o valor que diverge",
    "removal": "a feature REMOVE algo — conferir pelo termo VELHO, nas duas pontas",
    "contract": "a forma de uma resposta mudou — o tipo do frontend é afirmação, não verificação",
    "sensitive-field": "campo sensível — criptografia no Create E no Update",
    "tela": "tela nova ou alterada — padrão visual v2",
    "harness": "o diff muda o próprio verificador — quem audita a ferramenta?",
    "financeiro": "contexto financeiro ou isenção de idempotência — dinheiro, imutabilidade, Idempotency-Key",
}


def run(cmd: list[str], cwd: Path) -> str:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False).stdout


# ⚠️ SÓ CÓDIGO. Todas as etiquetas falam de código; deixar `.md`, `tsconfig.json` e `.gitignore`
# entrarem faz o classificador acender por texto de documentação — na primeira medição, `removal`
# acendeu com a palavra "Arquitetura" saindo de um CLAUDE.md e `sensitive-field` com "password"
# numa prosa. Detector que acusa markdown não classifica código (AG-020).
CODE_SPEC = ["*.ts", "*.tsx"]


def diff_of(ws: Path, base: str) -> tuple[list[str], str, str]:
    """(arquivos, diff completo, linhas removidas) do workspace — só `.ts/.tsx`."""
    if not ws.is_dir():
        return [], "", ""
    nomes = [l.strip() for l in run(["git", "diff", "--name-only", "--relative", base, "--", *CODE_SPEC], ws).splitlines() if l.strip()]
    nomes += [l.strip() for l in run(["git", "ls-files", "--others", "--exclude-standard", "--", *CODE_SPEC], ws).splitlines() if l.strip()]
    corpo = run(["git", "diff", "--no-ext-diff", base, "--", *CODE_SPEC], ws)
    for n in nomes:  # untracked não entra no `git diff`; o conteúdo conta como adição
        p = ws / n
        if p.is_file() and p.suffix in (".ts", ".tsx"):
            corpo += "\n" + "\n".join("+" + l for l in p.read_text(encoding="utf-8", errors="replace").splitlines())
    removidas = "\n".join(l[1:] for l in corpo.splitlines() if l.startswith("-") and not l.startswith("---"))
    return sorted(set(nomes)), corpo, removidas


def adicionadas(corpo: str) -> str:
    return "\n".join(l[1:] for l in corpo.splitlines() if l.startswith("+") and not l.startswith("+++"))


def spec_dir(feature: str) -> Path | None:
    for estado in ("em_andamento", "a_fazer", "concluido", "canceladas"):
        d = SPECS / estado / feature
        if d.is_dir():
            return d
    return None


def spec_head(feature: str) -> str:
    """Título + objetivo da `spec.md` — onde a feature diz o que é.

    ⚠️ A primeira versão concatenava `sorted(glob('*.md'))` e olhava as 60 primeiras linhas. Como
    `plan.md` vem antes de `spec.md` no alfabeto e os plans têm 300–500 linhas, a janela caía
    inteira no cabeçalho do plan e a etiqueta `bugfix` NUNCA acendia — nem nas specs 064 e 065,
    que têm "correção" duas vezes no cabeçalho da spec. As três perguntas da AG-011, que
    reprovaram três rodadas na spec 029, deixavam de ser carregadas justamente nas features de
    correção (achado da auditoria da 087)."""
    d = spec_dir(feature)
    if not d or not (d / "spec.md").is_file():
        return ""
    linhas = (d / "spec.md").read_text(encoding="utf-8", errors="replace").splitlines()
    fim = next((i for i, l in enumerate(linhas) if l.startswith("## 2.")), min(len(linhas), 40))
    return "\n".join(linhas[:fim])


def classify(feature: str, base: str) -> tuple[set[str], dict]:
    tags: set[str] = set()
    provas: dict[str, str] = {}
    arquivos_todos: list[str] = []
    add_todo = rem_todo = ""

    for nome, ws in WS.items():
        arqs, corpo, rem = diff_of(ws, base)
        arquivos_todos += [f"{nome}/{a}" for a in arqs]
        add, add_todo, rem_todo = adicionadas(corpo), add_todo + adicionadas(corpo), rem_todo + rem

        # `financeiro` (spec 001): diff em contexto financeiro do backend, ou qualquer linha
        # adicionada com o marcador de isenção — cada isenção é julgada pelo verifier (RN-15).
        if "idempotency-exempt" in add:
            tags.add("financeiro"); provas.setdefault("financeiro", f"{nome}: marcador `idempotency-exempt` adicionado")
        for a in arqs:
            _m = financial_rules.module_of(a)
            if nome in financial_rules.MONEY_WORKSPACES and _m and (
                    _m[0] in financial_rules.FINANCIAL_CONTEXTS or financial_rules.is_append_only(*_m)):
                tags.add("financeiro"); provas.setdefault("financeiro", f"{nome}/{a}")
            # migration mora fora do módulo: decide pela tabela (mesma regra do hook money-bigint)
            if nome in financial_rules.MONEY_WORKSPACES and a.startswith(financial_rules.MIGRATIONS_DIR):
                _p = ws / a
                if _p.is_file() and financial_rules._migration_is_financial(
                        financial_rules.strip_comments_keep_lines(_p.read_text(encoding="utf-8")), ws):
                    tags.add("financeiro"); provas.setdefault("financeiro", f"{nome}/{a} (migration de tabela financeira)")
            if "typeorm/migrations/" in a or "typeorm/entities/" in a:
                tags.add("migration"); provas.setdefault("migration", a)
            if a.endswith(".routes.ts") or "http/controllers/" in a:
                tags.add("routes"); provas.setdefault("routes", a)
            # `enum`: só `enums/` do backend. `constants/` acendia em toda feature de frontend
            # (T-11: 100%), e o espelho do frontend é conferido dentro do próprio check.
            if "/enums/" in a:
                tags.add("enum"); provas.setdefault("enum", a)
            if a.endswith(".tsx") and ("/pages/" in a or "/components/" in a):
                tags.add("tela"); provas.setdefault("tela", a)

        # `contract`: a FORMA da resposta mudou = campo REMOVIDO de DTO/tipo. Tocar em `.service.ts`
        # ou acrescentar campo é o dia a dia; o que a AG-022 pega é o campo que SUMIU (T-11: 100% → 36%).
        for bloco in re.split(r"^diff --git ", corpo, flags=re.M)[1:]:
            cab = bloco.split("\n", 1)[0]
            if not re.search(r"(/dtos/|\.types\.ts)", cab):
                continue
            if re.search(r"^-\s*\w+\??\s*:", bloco, re.M):
                tags.add("contract"); provas.setdefault("contract", f"{nome}: campo removido em {cab.split()[-1]}")

        # `mount-mode`: a MUDANÇA de modo, não a presença de render condicional (que é todo React).
        # Sinais: TabPanel entrando/saindo, `display:none`, ou render condicional REMOVIDO.
        if (re.search(r"TabPanel", add + rem)
                or re.search(r"display\s*[:=]\s*['\"]?none", add + rem)
                or re.search(r"(\?|&&)\s*<", rem)):
            tags.add("mount-mode"); provas.setdefault("mount-mode", f"{nome}: TabPanel / display:none / render condicional removido")
        # `number-field`: o campo é o sinal; `toNumber*` como CHAMADA aparece em toda tela. Só a
        # DECLARAÇÃO do conversor conta.
        if re.search(r'type="number"', add + rem) or re.search(
                r"(?:function|const)\s+\w*(?:[Nn]umber|[Dd]ecimal)\w*\s*[=(]", add + rem):
            tags.add("number-field"); provas.setdefault("number-field", f"{nome}: campo `type=\"number\"` ou declaração de conversor")
        # `sensitive-field`: nomes que são segredo de verdade. `_key` solto casava `rack_key`,
        # `stock_key`… (T-11: 100%).
        if re.search(r"\b(api_key|private_key|_secret|_pem|password|crypt)\w*", add, re.I):
            tags.add("sensitive-field"); provas.setdefault("sensitive-field", f"{nome}: campo com nome de segredo")

    # `removal`: identificador que SAIU do diff e não aparece mais em nenhum workspace.
    if rem_todo:
        candidatos = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]{5,})\b", rem_todo)) - set(
            re.findall(r"\b([A-Za-z_][A-Za-z0-9_]{5,})\b", add_todo))
        for ident in sorted(candidatos)[:40]:
            achou = any(run(["git", "grep", "-l", "--", ident], ws).strip() for ws in WS.values() if ws.is_dir())
            if not achou:
                tags.add("removal"); provas.setdefault("removal", f"`{ident}` saiu do diff e não existe mais no código")
                break

    # `harness`: o diff mexe no que verifica. Nasceu da 1ª auditoria com este procedimento — uma
    # feature de harness acende ZERO etiquetas (nenhum .ts/.tsx de produto), e o passo 2 devolve
    # "0 bloqueante" porque o script não se audita. Um nível 1 da hierarquia que ninguém audita é
    # exatamente o drift silencioso que esta linha de specs existe para matar.
    alterados = run(["git", "diff", "--name-only", base, "--", ".claude"], ROOT).split() + \
        run(["git", "ls-files", "--others", "--exclude-standard", "--", ".claude"], ROOT).split()
    verificadores = [a for a in alterados
                     if a.startswith((".claude/scripts/", ".claude/hooks/", ".claude/agents/",
                                      ".claude/scaffold/", ".claude/verifier-checks/",
                                      ".claude/commands/", ".claude/skills/", ".claude/workspaces.json"))]
    if verificadores:
        tags.add("harness"); provas.setdefault("harness", f"{len(verificadores)} arquivo(s), ex.: {verificadores[0]}")

    cabeca = spec_head(feature)
    if cabeca and re.search(r"corre[çc][ãa]o|corrigir|defeito|\bbug\b|regress[ãa]o", cabeca, re.I):
        tags.add("bugfix"); provas.setdefault("bugfix", "o título/objetivo da spec descreve correção de defeito")

    return tags, {"arquivos": len(arquivos_todos), "provas": provas}


def list_tags() -> int:
    faltam = [t for t in TAGS if not (CHECKS / f"{t}.md").is_file()]
    orfaos = [p.stem for p in CHECKS.glob("*.md") if p.stem not in TAGS] if CHECKS.is_dir() else []
    for t, desc in TAGS.items():
        marca = "✅" if (CHECKS / f"{t}.md").is_file() else "❌"
        print(f"  {marca} {t:<16} {desc}")
    for o in orfaos:
        print(f"  ⚠️  {o:<16} check sem etiqueta que o acenda")
    if faltam:
        print(f"\n❌ {len(faltam)} etiqueta(s) sem check: {', '.join(faltam)} — "
              f"toda etiqueta emitida tem de ter `.claude/verifier-checks/<etiqueta>.md`", file=sys.stderr)
        return 2
    print(f"\n✅ {len(TAGS)} etiquetas, todas com check")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="diff-classify.py")
    p.add_argument("--feature")
    p.add_argument("--since", default="HEAD")
    p.add_argument("--json", action="store_true")
    p.add_argument("--list-tags", action="store_true")
    a = p.parse_args(argv)

    if a.list_tags:
        return list_tags()
    if not a.feature:
        print("diff-classify: --feature <nome> é obrigatório (sem ele a etiqueta `bugfix` "
              "acenderia sempre — etiqueta que acende sempre não classifica nada)", file=sys.stderr)
        return 64
    if not spec_dir(a.feature):
        print(f"diff-classify: spec `{a.feature}` não encontrada em .claude/specs/*/", file=sys.stderr)
        return 65

    tags, meta = classify(a.feature, a.since)
    faltam = [t for t in tags if not (CHECKS / f"{t}.md").is_file()]

    if a.json:
        print(json.dumps({"feature": a.feature, "base": a.since, "arquivos": meta["arquivos"],
                          "etiquetas": sorted(tags), "provas": meta["provas"],
                          "checks": [f".claude/verifier-checks/{t}.md" for t in sorted(tags)],
                          "sem_check": faltam}, ensure_ascii=False, indent=2))
    else:
        print(f"diff-classify: {a.feature} — {meta['arquivos']} arquivo(s) no diff desde {a.since}")
        if not tags:
            print("  (nenhuma etiqueta — auditoria carrega só o núcleo)")
        for t in sorted(tags):
            print(f"  🏷️  {t:<16} {TAGS[t]}")
            print(f"      prova: {meta['provas'].get(t, '—')}")
            print(f"      check: .claude/verifier-checks/{t}.md")
    return 2 if faltam else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
