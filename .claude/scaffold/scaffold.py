#!/usr/bin/env python3
"""
scaffold.py — gera módulo backend, módulo frontend e migrations a partir dos templates
de `.claude/scaffold/templates/` (harness v2, spec 085 / HARNESS.md §F2).

Uso:
  python3 .claude/scaffold/scaffold.py backend  <contexto> <modulo> <Entity>
          [--plural Entities] [--tabela t] [--endpoint e] [--enum Tipo]
          [--no-table] [--sem-migration] [--append-only] [--timestamp ms] [--dry-run]
  python3 .claude/scaffold/scaffold.py frontend <contexto> <modulo> <Modulo> --ws <operador|cliente>
          --label "Rótulo" [--plural Modulos] [--label-plural "Rótulos"] [--endpoint e]
          [--filho Filho --filho-label "Rótulo"] [--constants] [--dry-run]
  python3 .claude/scaffold/scaffold.py migration create <Tabela> [--timestamp ms]
  python3 .claude/scaffold/scaffold.py migration alter  <Tabela> --mudanca <PascalCase>
          [--coluna c] [--ref tabela_referenciada] [--timestamp ms]
  python3 .claude/scaffold/scaffold.py --list-placeholders
  python3 .claude/scaffold/scaffold.py --self-test [backend|frontend|static]

Perfil --append-only (spec 001, RN-09): registro que nunca muda nem some (ledger, audit, eventos do
BTG, execuções de split). Gera só Create/Show/List/ListTotal, controller de 3 métodos, rotas
GET / · GET /show/:id · POST /, entity sem campos de atualização, repositório que INSERE (nunca
save) e migration com a trigger `reject_mutation()`. É OBRIGATÓRIO para os módulos de
`financial_rules.APPEND_ONLY_MODULES` e incompatível com --no-table.

--self-test static (spec 001, RN-10): gera todas as variações num diretório temporário, sem
workspace, sem toolchain e sem prettier, e confere as invariantes do gerado — inclusive que os 4
hooks financeiros não acusam nada no módulo append-only. É a prova que existe antes do workspace.

Regra central: placeholders de IDENTIDADE (__Entity__, __tabela__, __Modulo__…) são derivados
dos argumentos e substituídos do mais longo para o mais curto — concatenações como
`__permissao___view` e `CreateTable__Entities____timestamp__` resolvem porque o placeholder é o
prefixo e o resto é literal. MARCADORES DE BLOCO (lista fechada abaixo) ficam no arquivo gerado,
sempre em linha de comentário, para o agente preencher. Qualquer outro `__X__` → exit 2.

Diretivas de template (linha inteira, removidas na saída):
  // @if filho      ...      // @endif      mantém o trecho só quando há --filho
  // @if constants  ...      // @endif      idem para --constants
  // @if enum       ...      // @endif      idem para --enum
  // @if append_only / // @if !append_only  perfil --append-only (e o padrão)

Códigos de saída: 0 ok · 1 prettier falhou (o gerado é removido) · 2 placeholder/diretiva
desconhecidos ou template fora da tabela · 3 destino já existe · 4 migration duplicada
· 5 self-test reprovado · 64 uso.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TPL = HERE / "templates"
# Workspaces de `.claude/workspaces.json` (spec 001). Backend é um só (`backend`); frontend são
# vários, e por isso o subcomando `frontend` exige `--ws`.
sys.path.insert(0, str(ROOT / ".claude/scripts"))
sys.path.insert(0, str(ROOT / ".claude/hooks"))
import workspaces  # noqa: E402

WS_PATHS = workspaces.paths(ROOT)
BACKEND_WS = "backend"


def ws_for(kind: str, ws_key: str | None = None) -> Path:
    if kind == "backend":
        return WS_PATHS[BACKEND_WS]
    if ws_key not in workspaces.of_kind("frontend"):
        die(f"frontend exige --ws entre: {', '.join(workspaces.of_kind('frontend'))}", 64)
    return WS_PATHS[ws_key]


def cond_ok(cond: str, flags: dict[str, bool]) -> bool:
    """Condição de destino em `BACKEND_DEST`/`FRONTEND_DEST`: "" sempre, "x" se a flag, "!x" se não.
    UM avaliador para gerador, inventário e completude do `check-module.py` — a 1ª forma
    (`cond and not flags.get(cond)`) trataria "!x" como flag desconhecida e sempre falsa."""
    if not cond:
        return True
    if cond.startswith("!"):
        return not flags.get(cond[1:], False)
    return flags.get(cond, False)

BLOCK_MARKERS = {
    "__CAMPOS__", "__FILTROS__", "__COLUNAS__", "__REGRAS__", "__TESTES_DE_ERRO__",
    "__WHERES__", "__FKS__", "__VALORES__", "__IMPORTS_RELACIONAMENTOS__",
    "__ATRIBUICOES__", "__CAMPOS_FILHO__",
}
PLACEHOLDER_RE = re.compile(r"__[A-Za-z][A-Za-z_]*__")
DIRECTIVE_IF = re.compile(r"^\s*//\s*@if\s+(!?)(\w+)\s*$")
DIRECTIVE_END = re.compile(r"^\s*//\s*@endif\s*$")
# Flags aceitas nas diretivas — lista fechada: `// @if filhos` (typo) tem de falhar, não apagar o bloco.
DIRECTIVE_FLAGS = {"filho", "constants", "enum", "table", "migration", "append_only"}

BACKEND_IDENTITY = [
    "__Entity__", "__Entities__", "__entity__", "__entities__", "__contexto__", "__modulo__",
    "__tabela__", "__registro_id__", "__endpoint__", "__permissao__", "__timestamp__",
    "__Mudanca__", "__coluna__", "__tabela_referenciada__",
]
FRONTEND_IDENTITY = [
    "__Modulo__", "__Modulos__", "__modulo__", "__modulos__", "__MODULO__", "__contexto__",
    "__endpoint__", "__MODULO_LABEL__", "__TITULO_PT_BR__", "__registro_id__", "__Filho__",
    "__filho__", "__Filhos__", "__filhos__", "__ModuloFilho__",
    "__FILHO_LABEL__", "__registro_filho_id__",
]

# template → destino (relativo a <workspace>/src). Chaves de condição: table, enum.
BACKEND_DEST = [
    ("migration.ts.tpl", "shared/infra/typeorm/migrations/__timestamp__-CreateTable__Entities__.ts", "migration"),
    ("enum.ts.tpl", "modules/__contexto__/__modulo__/enums/__Entity__<Tipo>.ts", "enum"),
    ("entity.ts.tpl", "modules/__contexto__/__modulo__/infra/typeorm/entities/__Entity__.ts", "table"),
    ("dto-create.ts.tpl", "modules/__contexto__/__modulo__/dtos/ICreate__Entity__DTO.ts", ""),
    ("dto-update.ts.tpl", "modules/__contexto__/__modulo__/dtos/IUpdate__Entity__DTO.ts", "!append_only"),
    ("dto-find.ts.tpl", "modules/__contexto__/__modulo__/dtos/IFind__Entity__DTO.ts", ""),
    ("repository-interface.ts.tpl", "modules/__contexto__/__modulo__/repositories/I__Entity__Repository.ts", ""),
    ("repository.ts.tpl", "modules/__contexto__/__modulo__/infra/typeorm/repositories/__Entity__Repository.ts", ""),
    ("providers-index.ts.tpl", "modules/__contexto__/__modulo__/providers/index.ts", ""),
    ("service-create.ts.tpl", "modules/__contexto__/__modulo__/services/Create__Entity__Service.ts", ""),
    ("service-update.ts.tpl", "modules/__contexto__/__modulo__/services/Update__Entity__Service.ts", "!append_only"),
    ("service-show.ts.tpl", "modules/__contexto__/__modulo__/services/Show__Entity__Service.ts", ""),
    ("service-list.ts.tpl", "modules/__contexto__/__modulo__/services/List__Entities__Service.ts", ""),
    ("service-listtotal.ts.tpl", "modules/__contexto__/__modulo__/services/ListTotal__Entities__Service.ts", ""),
    ("service-delete.ts.tpl", "modules/__contexto__/__modulo__/services/Delete__Entity__Service.ts", "!append_only"),
    ("controller.ts.tpl", "modules/__contexto__/__modulo__/infra/http/controllers/__Entities__Controller.ts", "table"),
    ("routes.ts.tpl", "modules/__contexto__/__modulo__/infra/http/routes/__entities__.routes.ts", "table"),
    ("test-create.spec.ts.tpl", "modules/__contexto__/__modulo__/tests/Create__Entity__Service.spec.ts", ""),
    ("test-update.spec.ts.tpl", "modules/__contexto__/__modulo__/tests/Update__Entity__Service.spec.ts", "!append_only"),
    ("test-show.spec.ts.tpl", "modules/__contexto__/__modulo__/tests/Show__Entity__Service.spec.ts", ""),
    ("test-list.spec.ts.tpl", "modules/__contexto__/__modulo__/tests/List__Entities__Service.spec.ts", ""),
    ("test-listtotal.spec.ts.tpl", "modules/__contexto__/__modulo__/tests/ListTotal__Entities__Service.spec.ts", ""),
    ("test-delete.spec.ts.tpl", "modules/__contexto__/__modulo__/tests/Delete__Entity__Service.spec.ts", "!append_only"),
]
FRONTEND_DEST = [
    ("types.ts.tpl", "types/__modulos__.types.ts", ""),
    ("service.ts.tpl", "services/__modulos__.service.ts", ""),
    ("constants.ts.tpl", "constants/__Modulo__Type.ts", "constants"),
    ("context-modal.tsx.tpl", "context/__Modulo__ModalContext.tsx", "filho"),
    ("list-index.tsx.tpl", "pages/__contexto__/__Modulos__List/index.tsx", ""),
    ("form-index.tsx.tpl", "pages/__contexto__/__Modulo__Form/index.tsx", ""),
    ("form-register-data-index.tsx.tpl", "pages/__contexto__/__Modulo__FormRegisterData/index.tsx", ""),
    ("child-list-index.tsx.tpl", "pages/__contexto__/__Modulo__Form__Filho__/__Modulo__Form__Filhos__List/index.tsx", "filho"),
    ("child-register-index.tsx.tpl", "pages/__contexto__/__Modulo__Form__Filho__/__Modulo__Form__Filho__Register/index.tsx", "filho"),
]


# ----------------------------------------------------------------------------- utilidades
def die(msg: str, code: int) -> "NoReturn":  # type: ignore[name-defined]
    print(f"scaffold: {msg}", file=sys.stderr)
    sys.exit(code)


def plural(word: str) -> str:
    if re.search(r"[^aeiou]y$", word):
        return word[:-1] + "ies"
    if re.search(r"(s|x|z|ch|sh)$", word):
        return word + "es"
    return word + "s"


def snake(pascal: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", pascal).lower()


def lower_camel(pascal: str) -> str:
    return pascal[:1].lower() + pascal[1:] if pascal else pascal


def now_ms() -> str:
    return str(int(time.time() * 1000))


def apply_directives(text: str, flags: dict[str, bool]) -> str:
    out, keep, depth = [], [True], 0
    for line in text.splitlines(keepends=True):
        m = DIRECTIVE_IF.match(line)
        if m:
            if m.group(2) not in DIRECTIVE_FLAGS:
                raise ValueError(f"diretiva com flag desconhecida: @if {m.group(1)}{m.group(2)} "
                                 f"(aceitas: {', '.join(sorted(DIRECTIVE_FLAGS))})")
            depth += 1
            cond = flags.get(m.group(2), False)
            if m.group(1) == "!":
                cond = not cond
            keep.append(keep[-1] and cond)
            continue
        if DIRECTIVE_END.match(line):
            if depth == 0:
                raise ValueError("@endif sem @if")
            depth -= 1
            keep.pop()
            continue
        if keep[-1]:
            out.append(line)
    if depth != 0:
        raise ValueError("@if sem @endif")
    return "".join(out)


def substitute(text: str, values: dict[str, str]) -> str:
    for key in sorted(values, key=len, reverse=True):
        text = text.replace(key, values[key])
    return text


def leftovers(text: str) -> list[tuple[int, str]]:
    """Placeholders que sobraram DEPOIS da substituição, fora da lista fechada, com nº da linha."""
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for tok in PLACEHOLDER_RE.findall(line):
            if tok not in BLOCK_MARKERS:
                found.append((n, tok))
    return found


def block_markers_in(text: str) -> list[tuple[int, str]]:
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for tok in PLACEHOLDER_RE.findall(line):
            if tok in BLOCK_MARKERS:
                found.append((n, tok))
    return found


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def prettier(ws: Path, files: list[Path]) -> str | None:
    """Formata os arquivos gerados. Devolve a mensagem de erro (ou None se ok)."""
    bin_ = ws / "node_modules/.bin/prettier"
    if not files:
        return None
    if not bin_.exists():
        print(f"⚠️ prettier ausente em {bin_} — arquivos gerados sem formatação", file=sys.stderr)
        return None
    r = run([str(bin_), "--write", *[str(f) for f in files]], cwd=ws, check=False)
    if r.returncode != 0:
        return f"prettier falhou:\n{r.stderr}"
    return None


def remove_files(files: list[Path], stop_at: Path) -> None:
    """Apaga arquivos e as pastas que ficaram vazias até `stop_at` (exclusive)."""
    for f in files:
        try:
            f.unlink()
        except FileNotFoundError:
            pass
    for f in files:
        d = f.parent
        while d != stop_at and d.exists() and not any(d.iterdir()):
            d.rmdir()
            d = d.parent


# ----------------------------------------------------------------------------- geração
class Generator:
    def __init__(self, kind: str, values: dict[str, str], flags: dict[str, bool], dry: bool,
                 ws: Path | None = None, fmt: bool = True):
        self.kind = kind
        self.fmt = fmt
        # `ws` alternativo: o `--self-test static` gera num diretório temporário, sem workspace.
        self.ws = ws if ws is not None else ws_for(kind, values.get("<ws>"))
        self.src = self.ws / "src"
        self.values = values
        self.flags = flags
        self.dry = dry
        self.created: list[Path] = []
        self.pending: list[tuple[Path, int, str]] = []

    def dests(self) -> list[tuple[Path, Path]]:
        table = BACKEND_DEST if self.kind == "backend" else FRONTEND_DEST
        out = []
        for tpl, dest, cond in table:
            if not cond_ok(cond, self.flags):
                continue
            path = substitute(dest, self.values)
            if self.kind == "backend" and "<Tipo>" in path:
                path = path.replace("<Tipo>", self.values.get("<Tipo>", "Type"))
            out.append((TPL / self.kind / tpl, self.src / path))
        return out

    def render(self, tpl: Path) -> str:
        text = tpl.read_text(encoding="utf-8")
        text = apply_directives(text, self.flags)
        text = substitute(text, self.values)
        if "<Tipo>" in self.values:
            text = text.replace("<Tipo>", self.values["<Tipo>"])
        return text

    def generate(self) -> None:
        plan = self.dests()
        # 1) nunca sobrescrever (no --dry-run, listar tudo e marcar o que já existe)
        exists = [d for _, d in plan if d.exists()]
        if exists and self.dry:
            print("scaffold --dry-run — destinos:")
            for _, dest in plan:
                mark = "  (JÁ EXISTE)" if dest.exists() else ""
                print("  " + str(dest.relative_to(self.ws)) + mark)
            die(f"{len(exists)} destino(s) já existe(m) — o scaffold nunca sobrescreve", 3)
        if exists:
            die("destino já existe (o scaffold nunca sobrescreve):\n  " +
                "\n  ".join(str(p.relative_to(ROOT)) for p in exists), 3)
        # 2) renderizar tudo antes de escrever qualquer coisa
        rendered = []
        unknown = []
        for tpl, dest in plan:
            if not tpl.exists():
                die(f"template ausente: {tpl}", 64)
            text = self.render(tpl)
            for n, tok in leftovers(text):
                unknown.append(f"{tpl.name}:{n} {tok}")
            if "__" in dest.name:
                unknown.append(f"{tpl.name} → nome de destino com placeholder: {dest.name}")
            rendered.append((tpl, dest, text))
        if unknown:
            die("placeholder desconhecido (não é identidade nem marcador de bloco):\n  " +
                "\n  ".join(unknown), 2)
        # 3) dry-run
        if self.dry:
            print("scaffold --dry-run — destinos:")
            for _, dest, _ in rendered:
                print("  " + str(dest.relative_to(self.ws)))
            return
        # 4) escrever
        for tpl, dest, text in rendered:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
            self.created.append(dest)
            for n, tok in block_markers_in(text):
                self.pending.append((dest, n, tok))
        err = prettier(self.ws, self.created) if self.fmt else None
        if err:
            # Não deixar meia geração para trás: a próxima execução bateria no exit 3.
            remove_files(self.created, self.src)
            self.created = []
            die(err + "\n(arquivos gerados removidos; nada ficou no workspace)", 1)
        # 5) relatório
        try:
            onde = self.ws.relative_to(ROOT)
        except ValueError:
            onde = self.ws
        print(f"scaffold {self.kind}: {len(self.created)} arquivo(s) criado(s) em {onde}/src")
        for f in self.created:
            print("  + " + str(f.relative_to(self.src)))
        if self.pending:
            print("\nBlocos para preencher (arquivo:linha marcador):")
            # linhas podem ter mudado com o prettier — recalcular
            self.pending = []
            for f in self.created:
                for n, tok in block_markers_in(f.read_text(encoding="utf-8")):
                    self.pending.append((f, n, tok))
            for f, n, tok in self.pending:
                print(f"  {f.relative_to(self.src)}:{n} {tok}")


# ----------------------------------------------------------------------------- backend
def backend_values(a: argparse.Namespace) -> tuple[dict[str, str], dict[str, bool]]:
    entity = a.Entity
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", entity):
        die("Entity tem de ser PascalCase (ex.: DonorPreparation)", 64)
    entities = a.plural or plural(entity)
    tabela = a.tabela or snake(entities)
    values = {
        "__Entity__": entity,
        "__Entities__": entities,
        "__entity__": entity.lower(),
        "__entities__": entities.lower(),
        "__contexto__": a.contexto,
        "__modulo__": a.modulo,
        "__tabela__": tabela,
        "__registro_id__": f"{tabela}_id",
        "__endpoint__": a.endpoint or tabela.replace("_", "-"),
        "__permissao__": tabela,
        "__timestamp__": a.timestamp or now_ms(),
    }
    if a.enum:
        values["<Tipo>"] = a.enum
    flags = {
        "table": not a.no_table,
        "migration": not a.no_table and not a.sem_migration,
        # --no-table pula os passos 1, 2, 3, 9 e 10 da skill — o enum (2) inclusive.
        "enum": bool(a.enum) and not a.no_table,
        # `getattr`: o `check-module.py` monta o Namespace sem esta flag e decide por conta própria.
        "append_only": bool(getattr(a, "append_only", False)),
    }
    return values, flags


def append_only_guard(a: argparse.Namespace) -> None:
    """Prevenir na GERAÇÃO o que o hook `ledger-immutable` reprovaria logo depois (spec 001)."""
    import financial_rules  # tardio: financial_rules importa este arquivo
    ao = bool(getattr(a, "append_only", False))
    if ao and a.no_table:
        die("--append-only é incompatível com --no-table: registro imutável sem tabela não tem o que proteger", 64)
    if not ao and financial_rules.is_append_only(a.contexto, a.modulo):
        die(f"{a.contexto}/{a.modulo} é append-only (financial_rules.APPEND_ONLY_MODULES) — "
            "gere com --append-only", 64)


def check_migration_duplicate(entities: str) -> None:
    mig = WS_PATHS[BACKEND_WS] / "src/shared/infra/typeorm/migrations"
    dup = sorted(mig.glob(f"*-CreateTable{entities}.ts"))
    if dup:
        die(f"já existe migration de criação para {entities}: {dup[0].name}\n"
            f"  use `migration alter <Tabela> --mudanca <X>` para alterar a tabela, "
            f"ou `--sem-migration` para gerar o módulo sem ela", 4)


def cmd_backend(a: argparse.Namespace) -> None:
    append_only_guard(a)
    values, flags = backend_values(a)
    if flags["migration"]:
        check_migration_duplicate(values["__Entities__"])
        print("ℹ️ timestamp da migration: escolha ACIMA da última aplicada (`yarn migration:show`), "
              "não pelo `ls` da pasta — use --timestamp se o gerado não servir.")
    g = Generator("backend", values, flags, a.dry_run)
    g.generate()
    if not a.dry_run:
        print("\nChecklist manual (SKILL backend-module): registrar rota em "
              "src/shared/infra/http/routes/index.ts, importar providers em "
              "src/shared/container/index.ts, cadastrar permissões "
              f"{values['__permissao__']}_" + ("view/create" if flags["append_only"] else "view/create/update/delete")
              + ", rodar a migration.")


# ----------------------------------------------------------------------------- migration
def cmd_migration(a: argparse.Namespace) -> None:
    tabela_pascal = a.Tabela
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", tabela_pascal):
        die("Tabela em PascalCase plural (ex.: DonorPreparations)", 64)
    tabela = snake(tabela_pascal)
    values = {
        "__Entities__": tabela_pascal,
        "__tabela__": tabela,
        "__timestamp__": a.timestamp or now_ms(),
        "__Mudanca__": a.mudanca or "",
        "__coluna__": a.coluna or "nova_coluna",
        "__tabela_referenciada__": a.ref or "tabela_referenciada",
    }
    mig = WS_PATHS[BACKEND_WS] / "src/shared/infra/typeorm/migrations"
    if a.op == "create":
        check_migration_duplicate(tabela_pascal)
        tpl = TPL / "backend/migration.ts.tpl"
        dest = mig / f"{values['__timestamp__']}-CreateTable{tabela_pascal}.ts"
    else:
        if not a.mudanca:
            die("migration alter exige --mudanca <PascalCase> (ex.: AddFiscalCode)", 64)
        tpl = TPL / "backend/migration-alter.ts.tpl"
        dest = mig / f"{values['__timestamp__']}-AlterTable{tabela_pascal}{a.mudanca}.ts"
    text = substitute(tpl.read_text(encoding="utf-8"), values)
    bad = leftovers(text)
    if bad:
        die("placeholder desconhecido:\n  " + "\n  ".join(f"{tpl.name}:{n} {t}" for n, t in bad), 2)
    if dest.exists():
        die(f"destino já existe: {dest.relative_to(ROOT)}", 3)
    if a.dry_run:
        print("scaffold --dry-run — destino: " + str(dest.relative_to(ROOT)))
        return
    dest.write_text(text, encoding="utf-8")
    err = prettier(WS_PATHS[BACKEND_WS], [dest])
    if err:
        dest.unlink()
        die(err + "\n(arquivo removido)", 1)
    print(f"scaffold migration: + {dest.relative_to(ROOT)}")
    for n, tok in block_markers_in(dest.read_text(encoding="utf-8")):
        print(f"  {dest.name}:{n} {tok}")
    print("ℹ️ timestamp: confira com `yarn migration:show` que está acima da última aplicada; "
          "depois `yarn migration:run`.")


# ----------------------------------------------------------------------------- frontend
def frontend_values(a: argparse.Namespace) -> tuple[dict[str, str], dict[str, bool]]:
    modulo_pascal = a.Modulo
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", modulo_pascal):
        die("Modulo tem de ser PascalCase (ex.: Clinic)", 64)
    modulos_pascal = a.plural or plural(modulo_pascal)
    label = a.label
    values = {
        "__Modulo__": modulo_pascal,
        "__Modulos__": modulos_pascal,
        "__modulo__": modulo_pascal.lower(),
        "__modulos__": modulos_pascal.lower(),
        "__MODULO__": snake(modulo_pascal).upper(),
        "__contexto__": a.contexto,
        "__endpoint__": a.endpoint or a.modulo,
        "__MODULO_LABEL__": label,
        "__TITULO_PT_BR__": a.label_plural or (label + "s"),
        # FK do filho e id do update: snake_case do plural (clinics_id, donor_preparations_id)
        "__registro_id__": f"{snake(modulos_pascal)}_id",
    }
    values["<ws>"] = a.ws
    flags = {"filho": bool(a.filho), "constants": bool(a.constants)}
    if a.filho:
        filho = a.filho
        if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", filho):
            die("--filho em PascalCase (ex.: Contact)", 64)
        filhos = plural(filho)
        values.update({
            "__Filho__": filho,
            "__filho__": filho.lower(),
            "__Filhos__": filhos,
            "__filhos__": filhos.lower(),
            "__ModuloFilho__": modulo_pascal + filho,
            "__FILHO_LABEL__": a.filho_label or filho,
            "__registro_filho_id__": f"{snake(modulos_pascal)}_{snake(filhos)}_id",
        })
    return values, flags


def cmd_frontend(a: argparse.Namespace) -> None:
    values, flags = frontend_values(a)
    g = Generator("frontend", values, flags, a.dry_run)
    g.generate()
    if not a.dry_run:
        print("\nAvisos manuais (SKILL frontend-module): rotas em src/routes/index.tsx "
              f"(`/{values['__modulos__']}` e `/{values['__modulo__']}/:register/:id?`), menu em "
              "src/components/Header/menuItens.tsx" +
              (", provider do modal em src/App.tsx" if flags["filho"] else "") + ".")


# ----------------------------------------------------------------------------- inventário
def cmd_list_placeholders() -> int:
    """Lê todos os .tpl, classifica cada token e devolve 2 se houver desconhecido."""
    rc = 0
    in_tables = {
        "backend": {t for t, _, _ in BACKEND_DEST} | {"migration-alter.ts.tpl"},
        "frontend": {t for t, _, _ in FRONTEND_DEST},
    }
    for kind, identity in (("backend", BACKEND_IDENTITY), ("frontend", FRONTEND_IDENTITY)):
        print(f"== {kind} ==")
        ident, blocks, unknown = {}, {}, {}
        # Template fora da tabela de destinos é template MORTO: nunca é gerado, e um placeholder
        # errado nele só apareceria aqui — por isso o inventário também acusa a ausência.
        dead = sorted(p.name for p in (TPL / kind).glob("*.tpl") if p.name not in in_tables[kind])
        missing = sorted(t for t in in_tables[kind] if not (TPL / kind / t).exists())
        if dead or missing:
            rc = 2
            for name in dead:
                print(f"  ❌ template fora da tabela de destinos (morto): {name}")
            for name in missing:
                print(f"  ❌ template da tabela de destinos ausente: {name}")
        for tpl in sorted((TPL / kind).glob("*.tpl")):
            text = tpl.read_text(encoding="utf-8")
            tokens = set(PLACEHOLDER_RE.findall(text)) | set(PLACEHOLDER_RE.findall(tpl.name))
            for tok in tokens:
                if tok in BLOCK_MARKERS:
                    blocks.setdefault(tok, set()).add(tpl.name)
                    continue
                base = next((p for p in sorted(identity, key=len, reverse=True) if tok.startswith(p)), None)
                if base:
                    ident.setdefault(base, set()).add(tpl.name)
                else:
                    unknown.setdefault(tok, set()).add(tpl.name)
        print(f"  identidade ({len(ident)}): " + ", ".join(sorted(ident)))
        print(f"  blocos ({len(blocks)}): " + ", ".join(sorted(blocks)))
        if unknown:
            rc = 2
            print("  ❌ DESCONHECIDOS:")
            for tok, files in sorted(unknown.items()):
                print(f"     {tok} em " + ", ".join(sorted(files)))
        else:
            print("  desconhecidos: 0")
    return rc


# ----------------------------------------------------------------------------- self-test
V1_IMPORT_RE = re.compile(r"styles/(global|globalMaterialUi)'")


def strip_comments_keep_lines(text: str) -> str:
    """Igual ao `strip_comments`, mas devolve UMA LINHA PARA CADA linha do original.

    Existe porque quem acusa precisa citar `arquivo:linha`, e o `strip_comments` colapsa o bloco
    `/* … */` multilinha. A primeira versão disto era um `while "/*" in ln` textual, linha a linha —
    e um `/*` DENTRO DE STRING (`accept="image/*"`) abria bloco fantasma e engolia o resto do
    arquivo: 26 linhas de código somiam num `.tsx` real. Aqui o autômato é um só e rastreia estado
    de string, então `"image/*"` é string, não comentário (achado da auditoria da spec 087)."""
    out, i, n = [], 0, len(text)
    quote = None
    while i < n:
        c = text[i]
        if quote:
            out.append(c)
            # ⚠️ `'` e `"` NÃO atravessam linha em JS/TS — só a crase. Sem esta guarda, uma aspa
            # dentro de literal de regex (`/[a-z]'/`) abria string que nunca fechava, e daquele
            # ponto em diante o comentário deixava de ser filtrado: 7 arquivos de teste deste repo
            # (justamente os que citam padrões em string) ficavam a um comentário de distância de
            # um falso positivo. Achado da 2ª auditoria da 087.
            if c == "\n" and quote in ("'", '"'):
                quote = None
                i += 1; continue
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if c == quote:
                quote = None
            i += 1; continue
        if c in ("'", '"', "`"):
            quote = c; out.append(c); i += 1; continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            fim = n if j < 0 else j + 2
            out.append("\n" * text.count("\n", i, fim))  # preserva a numeração
            i = fim
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        out.append(c); i += 1
    return "".join(out)


def strip_comments(text: str) -> str:
    """Remove /* … */ (inclusive {/* … */} do JSX) e // até o fim da linha. Autômato simples que
    respeita strings/templates para não cortar um `//` dentro de 'http://'."""
    out, i, n = [], 0, len(text)
    quote = None
    while i < n:
        c = text[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if c == quote:
                quote = None
            i += 1; continue
        if c in ("'", '"', "`"):
            quote = c; out.append(c); i += 1; continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        out.append(c); i += 1
    return "".join(out)


def exports_of(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    names = set(re.findall(r"^export (?:const|function|interface|type|class) ([A-Za-z0-9_]+)", text, re.M))
    for m in re.finditer(r"^export \{([^}]*)\}", text, re.M):
        names |= {n.strip().split(" as ")[-1] for n in m.group(1).split(",") if n.strip()}
    return names


def imported_from(text: str, module_suffix: str) -> set[str]:
    names: set[str] = set()
    for m in re.finditer(r"import\s*\{([^}]*)\}\s*from\s*'([^']*)'", text):
        if m.group(2).endswith(module_suffix):
            names |= {n.strip().split(" as ")[0] for n in m.group(1).split(",") if n.strip()}
    return names


def git_dirty(ws: Path) -> str:
    return run(["git", "status", "--short"], cwd=ws, check=False).stdout.strip()


def self_test(kind: str) -> list[str]:
    if kind == "backend":
        ws = WS_PATHS[BACKEND_WS]
    else:
        # O primeiro frontend que existe no checkout; nenhum → o primeiro do JSON, e o teste de
        # toolchain abaixo diz que não rodou.
        fes = workspaces.of_kind("frontend")
        fe_ws = next((w for w in fes if WS_PATHS[w].is_dir()), fes[0])
        ws = WS_PATHS[fe_ws]
    failures: list[str] = []
    # Workspace ausente = o self-test completo NÃO RODOU (AG-019) — não é traceback nem aprovação.
    # Sem workspace, a prova possível é o `--self-test static` (spec 001, RN-10).
    if not ws.is_dir():
        return [f"{kind}: workspace {ws.relative_to(ROOT)} não existe neste checkout — o self-test "
                "completo não rodou; use `--self-test static`"]
    # O workspace pode ter alterações legítimas em curso (ex.: tsconfig ainda não commitado).
    # A exigência é que o self-test não DEIXE nada: o `git status` do fim tem de ser igual ao do início.
    baseline = git_dirty(ws)
    for bin_ in ("tsc", "eslint") + (("jest",) if kind == "backend" else ()):
        if not (ws / "node_modules/.bin" / bin_).exists():
            return [f"{kind}: toolchain ausente ({bin_}) — rode yarn install"]

    created: list[Path] = []
    try:
        if kind == "backend":
            guard = ws / "src/modules/zz_scaffold"
            if guard.exists():
                return [f"{kind}: {guard.relative_to(ws)} já existe — remova antes"]
            ns = argparse.Namespace(contexto="zz_scaffold", modulo="zz_items", Entity="ZzScaffoldItem",
                                    plural=None, tabela=None, endpoint=None, enum="Status",
                                    no_table=False, sem_migration=False,
                                    timestamp="1000000000000", dry_run=False)
            values, flags = backend_values(ns)
            g = Generator("backend", values, flags, False)
            g.generate()
            created = list(g.created)
            gen_dir = guard
        else:
            guard = ws / "src/pages/zz_scaffold"
            if guard.exists():
                return [f"{kind}: {guard.relative_to(ws)} já existe — remova antes"]
            ns = argparse.Namespace(contexto="zz_scaffold", modulo="zzscaffold", Modulo="ZzScaffold",
                                    plural=None, label="Zz", label_plural=None, endpoint=None,
                                    filho="Zzchild", filho_label="Zz filho", constants=True, dry_run=False,
                                    ws=fe_ws)
            values, flags = frontend_values(ns)
            g = Generator("frontend", values, flags, False, ws=ws)
            g.generate()
            created = list(g.created)
            gen_dir = guard

        # invariantes sobre o gerado
        for f in created:
            if "__" in f.name:
                failures.append(f"nome com placeholder: {f.relative_to(ws)}")
            text = f.read_text(encoding="utf-8")
            for tok in set(PLACEHOLDER_RE.findall(text)):
                if tok not in BLOCK_MARKERS:
                    failures.append(f"placeholder sobrou em {f.relative_to(ws)}: {tok}")
            if kind == "frontend":
                # [AG-013] As checagens abaixo olham o CÓDIGO, não o arquivo cru: o template cita o
                # canônico ("modelo: pages/clinics/…") e o antipadrão da FE-024 em COMENTÁRIOS, e o
                # comentário que ensina a evitar o padrão não pode ser acusado por exibi-lo.
                code = strip_comments(text)
                if V1_IMPORT_RE.search(code):
                    failures.append(f"import v1 em {f.relative_to(ws)}")
                if re.search(r"linic", code, re.I):
                    failures.append(f"vazamento do módulo canônico (Clinic) em {f.relative_to(ws)}")
                if re.search(r"slots=\{\{\s*backdrop", code):
                    failures.append(f"FE-024: slots backdrop em {f.relative_to(ws)}")
        if kind == "frontend":
            mui = exports_of(ws / "src/styles/globalMaterialUi_v2.tsx")
            glob_ = exports_of(ws / "src/styles/global_v2.tsx")
            for f in created:
                text = f.read_text(encoding="utf-8")
                for name in imported_from(text, "globalMaterialUi_v2") - mui:
                    failures.append(f"{f.relative_to(ws)} importa {name}, que não existe em globalMaterialUi_v2")
                for name in imported_from(text, "global_v2") - glob_:
                    failures.append(f"{f.relative_to(ws)} importa {name}, que não existe em global_v2")
        # toolchain
        r = run([str(ws / "node_modules/.bin/tsc"), "--noEmit"], cwd=ws, check=False)
        if r.returncode != 0:
            failures.append("tsc reprovou:\n" + (r.stdout + r.stderr).strip()[:4000])
        flags_es = []
        help_ = run([str(ws / "node_modules/.bin/eslint"), "--help"], cwd=ws, check=False).stdout
        if "--no-warn-ignored" in help_:
            flags_es.append("--no-warn-ignored")
        r = run([str(ws / "node_modules/.bin/eslint"), *flags_es, *[str(f) for f in created]], cwd=ws, check=False)
        if r.returncode != 0:
            failures.append("eslint reprovou:\n" + (r.stdout + r.stderr).strip()[:4000])
        if kind == "backend":
            r = run([str(ws / "node_modules/.bin/jest"), "--passWithNoTests", "src/modules/zz_scaffold"], cwd=ws, check=False)
            summary = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if l.startswith(("Tests:", "Test Suites:")))
            print("  jest: " + summary.replace("\n", " · "))
            if r.returncode != 0:
                failures.append("jest reprovou:\n" + (r.stdout + r.stderr).strip()[-4000:])
        print(f"  {kind}: tsc {'ok' if not any(f.startswith('tsc') for f in failures) else 'FALHOU'}, "
              f"eslint {'ok' if not any(f.startswith('eslint') for f in failures) else 'FALHOU'}")
    finally:
        # apagar tudo o que foi criado, inclusive pastas vazias que sobraram
        remove_files(created, ws / "src")
        if kind == "backend":
            for stray in (ws / "src/shared/infra/typeorm/migrations").glob("1000000000000-*.ts"):
                stray.unlink()
        for d in (ws / "src/modules/zz_scaffold", ws / "src/pages/zz_scaffold"):
            if d.exists():
                shutil.rmtree(d)
        after = git_dirty(ws)
        if after != baseline:
            failures.append(f"{kind}: o self-test deixou o workspace diferente do que encontrou:\n"
                            f"--- antes ---\n{baseline}\n--- depois ---\n{after}")
    return failures


# Invariantes do perfil append-only (plan 2.8.3). Ficam aqui, perto do gerador, e não num teste à
# parte: quem muda o template roda este self-test, e o `verify.sh harness` também.
APPEND_ONLY_EXPECTED_FILES = 17  # os 22 do padrão sem --enum, menos dto-update e Update/Delete × service/teste
APPEND_ONLY_FORBIDDEN = re.compile(r"save\(|\.update\(|\.delete\(|\buser_updated\b|\bupdated_at\b|\bUpdateDateColumn\b")
ROUTE_REG_RE = re.compile(r"\w+Router\.(get|post|put|patch|delete)\(")


def self_test_static() -> int:
    """`--self-test static` (spec 001, RN-10): sem workspace, sem toolchain, sem prettier."""
    import contextlib
    import io
    import tempfile
    import financial_rules  # tardio: financial_rules importa este arquivo

    failures: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="scaffold-static-"))

    def bns(**kw) -> argparse.Namespace:
        base = dict(contexto="zz_scaffold", modulo="zz_items", Entity="ZzScaffoldItem", plural=None,
                    tabela=None, endpoint=None, enum=None, no_table=False, sem_migration=False,
                    append_only=False, timestamp="1000000000000", dry_run=False)
        base.update(kw)
        return argparse.Namespace(**base)

    variants = [
        ("backend-padrao", "backend", bns(enum="Status")),
        ("backend-no-table", "backend", bns(no_table=True)),
        ("backend-append-only", "backend", bns(contexto="ledger", Entity="ZzLedgerItem", append_only=True)),
        ("frontend", "frontend", argparse.Namespace(
            contexto="zz_scaffold", modulo="zzscaffold", Modulo="ZzScaffold", plural=None, label="Zz",
            label_plural=None, endpoint=None, filho="Zzchild", filho_label="Zz filho", constants=True,
            dry_run=False, ws=workspaces.of_kind("frontend")[0])),
    ]
    generated: dict[str, list[Path]] = {}
    try:
        for label, kind, ns in variants:
            ws_key = BACKEND_WS if kind == "backend" else ns.ws
            ws = tmp / label / workspaces.load()[ws_key]["path"]
            try:
                values, flags = backend_values(ns) if kind == "backend" else frontend_values(ns)
                g = Generator(kind, values, flags, False, ws=ws, fmt=False)
                with contextlib.redirect_stdout(io.StringIO()):
                    g.generate()
            except (SystemExit, ValueError) as e:
                failures.append(f"{label}: geração falhou ({e})")
                continue
            generated[label] = list(g.created)
            for f in g.created:
                if "__" in f.name:
                    failures.append(f"{label}: nome com placeholder: {f.name}")
                for tok in set(PLACEHOLDER_RE.findall(f.read_text(encoding="utf-8"))):
                    if tok not in BLOCK_MARKERS:
                        failures.append(f"{label}: placeholder sobrou em {f.name}: {tok}")
            print(f"  {label}: {len(g.created)} arquivo(s)")

        # migrations avulsas, em dry-run (só renderização + placeholders)
        for op, extra in (("create", {}), ("alter", {"mudanca": "AddZzCode"})):
            ns = argparse.Namespace(op=op, Tabela="ZzItems", mudanca=extra.get("mudanca"), coluna=None,
                                    ref=None, timestamp="1000000000000", dry_run=True)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    cmd_migration(ns)
            except SystemExit as e:
                failures.append(f"migration {op}: falhou (exit {e.code})")

        # guarda do append-only
        for desc, ns, esperado in (
            ("ledger sem --append-only", bns(contexto="ledger"), 64),
            ("--append-only + --no-table", bns(contexto="ledger", append_only=True, no_table=True), 64),
            ("btg/btg_events sem --append-only", bns(contexto="btg", modulo="btg_events"), 64),
            ("splits/split_rules sem --append-only", bns(contexto="splits", modulo="split_rules"), 0),
            ("ledger com --append-only", bns(contexto="ledger", append_only=True), 0),
        ):
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    append_only_guard(ns)
                obtido = 0
            except SystemExit as e:
                obtido = e.code
            if obtido != esperado:
                failures.append(f"guarda: {desc} → exit {obtido}, esperado {esperado}")

        ao = generated.get("backend-append-only", [])
        if ao:
            if len(ao) != APPEND_ONLY_EXPECTED_FILES:
                failures.append(f"append-only: {len(ao)} arquivos, esperado {APPEND_ONLY_EXPECTED_FILES}")
            for f in ao:
                if re.search(r"^(Update|Delete)|IUpdate", f.name):
                    failures.append(f"append-only: gerou {f.name}")
            # (b) código sem comentário — o template CITA o proibido em comentário (AG-013)
            for f in ao:
                for n, line in enumerate(strip_comments_keep_lines(f.read_text(encoding="utf-8")).split("\n"), 1):
                    m = APPEND_ONLY_FORBIDDEN.search(line)
                    if m:
                        failures.append(f"append-only: `{m.group(0)}` em {f.name}:{n}")
            mig = [f for f in ao if "/migrations/" in str(f)]
            mig_txt = mig[0].read_text(encoding="utf-8") if mig else ""
            for need in ("reject_mutation", "BEFORE UPDATE OR DELETE", "BEFORE TRUNCATE"):
                if need not in mig_txt:
                    failures.append(f"append-only: migration sem `{need}`")
            rotas = [f for f in ao if f.name.endswith(".routes.ts")]
            regs = ROUTE_REG_RE.findall(strip_comments(rotas[0].read_text(encoding="utf-8"))) if rotas else []
            if regs != ["get", "get", "post"]:
                failures.append(f"append-only: rotas {regs}, esperado ['get', 'get', 'post']")
            specs = [f for f in ao if f.name.endswith(".spec.ts")]
            if len(specs) != 4:
                failures.append(f"append-only: {len(specs)} testes, esperado 4")
            ctrl = [f for f in ao if f.name.endswith("Controller.ts")]
            metodos = re.findall(r"public async (\w+)\(", ctrl[0].read_text(encoding="utf-8")) if ctrl else []
            if metodos != ["index", "show", "create"]:
                failures.append(f"append-only: controller com {metodos}, esperado index/show/create")

        # (g) os 4 hooks financeiros concordam com o gerador: nada a acusar no que ele gera
        for label in ("backend-append-only", "backend-padrao"):
            for f in generated.get(label, []):
                # A (g) só prova algo se o arquivo cair NO ESCOPO das regras: com TMPDIR dentro de
                # um diretório de fixtures, `locate` devolvia "" e a (g) passava vazia (achado MÉDIA da
                # 1ª auditoria da spec 001).
                if financial_rules.locate(str(f))[0] != BACKEND_WS:
                    failures.append(f"{label}: {f.name} fora do escopo das regras (TMPDIR={tmp}) — (g) não provaria nada")
                    break
                for nome in financial_rules.RULES:
                    for n, msg in financial_rules.run_rule(nome, str(f), f.read_text(encoding="utf-8")):
                        failures.append(f"{label}: hook {nome} acusa {f.name}:{n} — {msg[:90]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for f in failures:
        print("  ❌ " + f)
    if failures:
        print(f"\n❌ self-test static REPROVADO ({len(failures)} falha(s))")
        return 5
    print("\n✅ self-test static aprovado — 4 variações + 2 migrations renderizadas, guarda do "
          "append-only, invariantes (a)–(f) e (g): os 4 hooks financeiros limpos sobre o gerado")
    return 0


def cmd_self_test(which: str | None) -> int:
    kinds = [which] if which else ["backend", "frontend"]
    all_failures = []
    for kind in kinds:
        print(f"== self-test {kind} ==")
        fails = self_test(kind)
        all_failures += fails
        for f in fails:
            print("  ❌ " + f)
    if all_failures:
        print(f"\n❌ self-test REPROVADO ({len(all_failures)} falha(s))")
        return 5
    print("\n✅ self-test aprovado — geração limpa, workspaces intactos")
    return 0


# ----------------------------------------------------------------------------- cli
def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="scaffold.py", add_help=True)
    p.add_argument("--list-placeholders", action="store_true")
    p.add_argument("--self-test", nargs="?", const="all", choices=["all", "backend", "frontend", "static"])
    sub = p.add_subparsers(dest="cmd")

    b = sub.add_parser("backend")
    b.add_argument("contexto"); b.add_argument("modulo"); b.add_argument("Entity")
    b.add_argument("--plural"); b.add_argument("--tabela"); b.add_argument("--endpoint"); b.add_argument("--enum")
    b.add_argument("--no-table", action="store_true"); b.add_argument("--sem-migration", action="store_true")
    b.add_argument("--append-only", action="store_true")
    b.add_argument("--timestamp"); b.add_argument("--dry-run", action="store_true")

    f = sub.add_parser("frontend")
    f.add_argument("contexto"); f.add_argument("modulo"); f.add_argument("Modulo")
    f.add_argument("--ws", required=True, choices=workspaces.of_kind("frontend"))
    f.add_argument("--label", required=True); f.add_argument("--label-plural"); f.add_argument("--plural")
    f.add_argument("--endpoint"); f.add_argument("--filho"); f.add_argument("--filho-label")
    f.add_argument("--constants", action="store_true"); f.add_argument("--dry-run", action="store_true")

    m = sub.add_parser("migration")
    m.add_argument("op", choices=["create", "alter"]); m.add_argument("Tabela")
    m.add_argument("--mudanca"); m.add_argument("--coluna"); m.add_argument("--ref")
    m.add_argument("--timestamp"); m.add_argument("--dry-run", action="store_true")

    a = p.parse_args(argv)
    if a.list_placeholders:
        return cmd_list_placeholders()
    if a.self_test == "static":
        return self_test_static()
    if a.self_test:
        return cmd_self_test(None if a.self_test == "all" else a.self_test)
    if a.cmd == "backend":
        cmd_backend(a)
    elif a.cmd == "frontend":
        cmd_frontend(a)
    elif a.cmd == "migration":
        cmd_migration(a)
    else:
        p.print_help(sys.stderr)
        return 64
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ValueError as e:
        die(str(e), 2)
