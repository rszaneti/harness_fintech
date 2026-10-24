#!/usr/bin/env python3
"""
check-module.py — a parte MECÂNICA da auditoria (harness v2, spec 087 / HARNESS.md §F4).

Tudo o que reprova **sem julgamento** mora aqui. O `verifier` roda este script antes de julgar
qualquer coisa: achado de severidade ALTA é REPROVADO, sem discussão. O que exige julgamento
(alcançabilidade, estado que sobrevive à troca de aba, cobertura de RN) fica com o agente.

Uso:
  python3 .claude/scripts/check-module.py <workspace> [pasta]   (chave de .claude/workspaces.json)
          [--diff] [--since <ref>] [--ref <modulo>]... [--contract] [--json] [--self-test]

  <pasta>      relativa ao workspace (ex.: src/modules/clinics/clinics). Varre a pasta inteira.
  --diff       arquivos do diff do workspace (git diff HEAD + untracked), só .ts/.tsx
  --since REF  idem, com outra base (tag de sprint, commit)
  --ref MOD    nome do módulo que serviu de molde ("espelhar X" do plan) — habilita a checagem
               de vazamento (AG-002). Repetível. SEM ele a checagem é PULADA, e o resumo diz isso.
  --contract   acrescenta as checagens de contrato (AG-022, FE-025) — sempre INFO
  --self-test  roda os casos de `.claude/scripts/tests/check-module/` e confere o esperado

Exit: 0 sem achado bloqueante · 1 achado ALTA · 2 self-test reprovado · 64 uso · 65 caminho/ref inválido

⚠️ A LISTA DE PADRÕES PROIBIDOS VIVE AQUI, num lugar só (spec 087, RN-03). Antes dela existir, a
mesma regra estava copiada em três markdowns e as cópias divergiram em silêncio. Markdown manda
rodar o script; não repete a lista.

⚠️ Toda checagem olha o CÓDIGO, não o arquivo cru (AG-013) — exceto `bloco-pendente`, cujo alvo
vive em comentário por construção. O filtro é o `strip_comments` do scaffold.py: um autômato que
rastreia estado de string, não um regex. Regex deixa passar `// styles/global' era o antigo`.
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
# Workspaces: `.claude/workspaces.json` (spec 001). O argumento da CLI é a CHAVE do workspace
# (`backend`, `operador`, `cliente`, `simulator`); as checagens decidem pelo `kind` dele.
sys.path.insert(0, str(HERE))
import workspaces  # noqa: E402

WS = workspaces.paths(ROOT)

# As regras financeiras moram em `hooks/financial_rules.py` — as MESMAS que os hooks pós-edição
# rodam (spec 001, RN-18). Este script não tem uma lista própria delas.
sys.path.insert(0, str(ROOT / ".claude/hooks"))
PRUNE = {"node_modules", "build", "dist", "coverage", ".git"}

# O scaffold é a fonte única do que um módulo deve ter e de como se ignora comentário (RN-03).
sys.path.insert(0, str(ROOT / ".claude/scaffold"))
import scaffold  # noqa: E402
import financial_rules  # noqa: E402


# ----------------------------------------------------------------------------- achados
class Finding:
    def __init__(self, check: str, path: Path, line: int, code: str, msg: str, alta: bool = True):
        self.check, self.path, self.line, self.code, self.msg, self.alta = check, path, line, code, msg, alta

    def rel(self) -> str:
        try:
            return str(self.path.relative_to(ROOT))
        except ValueError:
            return str(self.path)

    def __str__(self) -> str:
        where = f"{self.rel()}:{self.line}" if self.line else self.rel()
        return f"[{'ALTA' if self.alta else 'INFO'}] {where} — [{self.code}] {self.msg}"

    def as_dict(self) -> dict:
        return {"check": self.check, "file": self.rel(), "line": self.line,
                "code": self.code, "severity": "ALTA" if self.alta else "INFO", "message": self.msg}


class Report:
    def __init__(self) -> None:
        self.findings: list[Finding] = []
        self.notes: list[str] = []

    def add(self, *a, **k) -> None:
        self.findings.append(Finding(*a, **k))

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    @property
    def blocking(self) -> list[Finding]:
        return [f for f in self.findings if f.alta]


def run(cmd: list[str], cwd: Path) -> str:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False).stdout


def code_of(path: Path) -> str:
    """Conteúdo sem comentários, uma linha para cada linha do original (para citar `arquivo:linha`).

    Um autômato só, em `scaffold.py` (RN-03). A versão anterior tinha um fallback textual aqui
    para o bloco `/* */` multilinha, e a auditoria da 087 provou o estrago: `accept="image/*"` num
    `.tsx` real abria bloco fantasma e apagava 26 linhas de código da varredura."""
    return scaffold.strip_comments_keep_lines(path.read_text(encoding="utf-8", errors="replace"))


def lines_of_code(path: Path) -> list[tuple[int, str]]:
    return list(enumerate(code_of(path).splitlines(), 1))


# ----------------------------------------------------------------------------- conjunto de arquivos
def files_from_folder(base: Path) -> list[Path]:
    out = []
    for p in sorted(base.rglob("*")):
        if any(part in PRUNE for part in p.parts):
            continue
        if p.is_file() and p.suffix in (".ts", ".tsx"):
            out.append(p)
    return out


def files_from_diff(ws: Path, base: str) -> list[Path]:
    names = set()
    for line in run(["git", "diff", "--name-only", "--relative", "--diff-filter=ACMR", base, "--", "."], ws).splitlines():
        names.add(line.strip())
    for line in run(["git", "ls-files", "--others", "--exclude-standard", "--", "src"], ws).splitlines():
        names.add(line.strip())
    out = []
    for n in sorted(x for x in names if x):
        p = ws / n
        if p.is_file() and p.suffix in (".ts", ".tsx") and not any(part in PRUNE for part in p.parts):
            out.append(p)
    return out


# ----------------------------------------------------------------------------- checagens
def check_bloco_pendente(files: list[Path], rep: Report) -> None:
    """[spec 085] Marcador de bloco ainda no arquivo = módulo gerado e NÃO preenchido.

    Olha o arquivo CRU de propósito: o marcador vive em comentário por construção. Durante a
    edição o hook só avisa (senão preencher o 2º marcador reprovaria a edição legítima do 1º);
    na ENTREGA, marcador restante é trabalho que não foi feito."""
    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for tok in scaffold.PLACEHOLDER_RE.findall(line):
                if tok in scaffold.BLOCK_MARKERS:
                    rep.add("bloco-pendente", f, n, "085",
                            f"marcador `{tok}` não preenchido — o módulo foi gerado, não terminado")


# Só os placeholders que o scaffold REALMENTE emite. Acusar qualquer `__x__` reprovava
# `'__ungrouped__'` — sentinela legítima de agrupamento em 2 telas de produção (achado da auditoria
# da 087). Com "qualquer achado ALTA = REPROVADO", isso reprovaria por código correto toda feature
# que tocasse aquelas telas.
PLACEHOLDERS_DO_SCAFFOLD = set(scaffold.BACKEND_IDENTITY) | set(scaffold.FRONTEND_IDENTITY)


def check_placeholder(files: list[Path], rep: Report) -> None:
    """[spec 085] Placeholder de identidade vazado em linha de CÓDIGO. Passa em lint e typecheck."""
    for f in files:
        for n, line in lines_of_code(f):
            for tok in scaffold.PLACEHOLDER_RE.findall(line):
                if tok in scaffold.BLOCK_MARKERS:
                    continue
                # `__permissao___view` é concatenação: casa por prefixo conhecido.
                if not any(tok.startswith(p) for p in PLACEHOLDERS_DO_SCAFFOLD):
                    continue
                rep.add("placeholder", f, n, "085",
                        f"placeholder `{tok}` vazado em código — lint e typecheck não pegam")


# ⚠️ O PAPEL VEM DO TEMPLATE, não do nome da entidade. Comparar nome derivado reprovava 150 dos
# 176 módulos: `exams_protocols` tem `ExamsProtocolsController` e `ListExamProtocolsService` (não
# existe um plural que sirva aos dois), e casar o plural sem caso comia o `S` de `Service` em
# `DeleteXCollectionService`. A AG-009 pergunta "o módulo tem um service de List? um teste para
# cada?", não "o arquivo se chama exatamente assim" — e ruído nessa escala treina a ignorar o
# achado (AG-013), justo no achado que ninguém confere à mão.
PAPEL = {
    "enum.ts.tpl": ("enums", re.compile(r".+\.ts$")),
    "entity.ts.tpl": ("infra/typeorm/entities", re.compile(r".+\.ts$")),
    "dto-create.ts.tpl": ("dtos", re.compile(r"ICreate.+DTO\.ts$")),
    "dto-update.ts.tpl": ("dtos", re.compile(r"IUpdate.+DTO\.ts$")),
    "dto-find.ts.tpl": ("dtos", re.compile(r"IFind.+DTO\.ts$")),
    "repository-interface.ts.tpl": ("repositories", re.compile(r"I.+Repository\.ts$")),
    "repository.ts.tpl": ("infra/typeorm/repositories", re.compile(r".+Repository\.ts$")),
    "providers-index.ts.tpl": ("providers", re.compile(r"index\.ts$")),
    "service-create.ts.tpl": ("services", re.compile(r"Create.+Service\.ts$")),
    "service-update.ts.tpl": ("services", re.compile(r"Update.+Service\.ts$")),
    "service-show.ts.tpl": ("services", re.compile(r"Show.+Service\.ts$")),
    "service-list.ts.tpl": ("services", re.compile(r"List(?!Total).+Service\.ts$")),
    "service-listtotal.ts.tpl": ("services", re.compile(r"ListTotal.+Service\.ts$")),
    "service-delete.ts.tpl": ("services", re.compile(r"Delete.+Service\.ts$")),
    "controller.ts.tpl": ("infra/http/controllers", re.compile(r".+Controller\.ts$")),
    "routes.ts.tpl": ("infra/http/routes", re.compile(r".+\.routes\.ts$")),
    "test-create.spec.ts.tpl": ("tests", re.compile(r"Create.+\.spec\.ts$")),
    "test-update.spec.ts.tpl": ("tests", re.compile(r"Update.+\.spec\.ts$")),
    "test-show.spec.ts.tpl": ("tests", re.compile(r"Show.+\.spec\.ts$")),
    "test-list.spec.ts.tpl": ("tests", re.compile(r"List(?!Total).+\.spec\.ts$")),
    "test-listtotal.spec.ts.tpl": ("tests", re.compile(r"ListTotal.+\.spec\.ts$")),
    "test-delete.spec.ts.tpl": ("tests", re.compile(r"Delete.+\.spec\.ts$")),
}
DESCRICAO_PAPEL = {
    "enum.ts.tpl": "enum", "entity.ts.tpl": "entity",
    "dto-create.ts.tpl": "DTO de criação", "dto-update.ts.tpl": "DTO de atualização",
    "dto-find.ts.tpl": "DTO de busca", "repository-interface.ts.tpl": "interface do repositório",
    "repository.ts.tpl": "repositório TypeORM", "providers-index.ts.tpl": "registro no IoC",
    "service-create.ts.tpl": "service Create", "service-update.ts.tpl": "service Update",
    "service-show.ts.tpl": "service Show", "service-list.ts.tpl": "service List",
    "service-listtotal.ts.tpl": "service ListTotal", "service-delete.ts.tpl": "service Delete",
    "controller.ts.tpl": "controller", "routes.ts.tpl": "rotas",
    "test-create.spec.ts.tpl": "teste do Create", "test-update.spec.ts.tpl": "teste do Update",
    "test-show.spec.ts.tpl": "teste do Show", "test-list.spec.ts.tpl": "teste do List",
    "test-listtotal.spec.ts.tpl": "teste do ListTotal", "test-delete.spec.ts.tpl": "teste do Delete",
}


def check_completude(kind: str, base: Path, ws: Path, rep: Report) -> None:
    """[AG-009] O módulo tem todos os arquivos que o scaffold geraria?

    A lista de destinos vem do `scaffold.py` (BACKEND_DEST) — template novo muda o que o auditor
    exige, sem editar o auditor."""
    if kind != "backend":
        rep.note("completude: pulada (só vale para pasta de módulo do backend)")
        return
    try:
        rel = base.relative_to(ws / "src/modules")
        contexto, modulo = rel.parts[0], rel.parts[1]
    except (ValueError, IndexError):
        rep.note(f"completude: pulada ({base} não é src/modules/<contexto>/<modulo>)")
        return

    ents = sorted((base / "infra/typeorm/entities").glob("*.ts")) if (base / "infra/typeorm/entities").is_dir() else []
    if not ents:
        dtos = sorted(base.glob("dtos/ICreate*DTO.ts"))
        if not dtos:
            rep.note("completude: pulada (não achei entity nem ICreate…DTO para derivar o nome)")
            return
        entity = dtos[0].name[len("ICreate"):-len("DTO.ts")]
    else:
        entity = ents[0].stem

    # ⚠️ O plural vem do PRÓPRIO módulo quando ele já diz qual é — o controller existente é a
    # verdade dele. Derivar sempre de `plural(Entity)` cobrava `ExamProtocolsController` de um
    # módulo gerado com `--plural ExamsProtocols`, e três módulos recebiam falta falsa (achado da
    # auditoria da 087). Sem controller, cai na derivação padrão.
    # O controller PRINCIPAL é o de nome mais curto: os extras são `<Entities><Caso>Controller`
    # (padrão da skill para quando passa de 5 métodos). Ordenar por alfabeto pegava
    # `ExamsProtocolsActiveController` e o módulo inteiro era medido contra o plural errado.
    ctrls = sorted((base / "infra/http/controllers").glob("*Controller.ts"), key=lambda p: len(p.stem)) \
        if (base / "infra/http/controllers").is_dir() else []
    plural_real = ctrls[0].stem[:-len("Controller")] if ctrls else None
    rotas = sorted((base / "infra/http/routes").glob("*.routes.ts")) \
        if (base / "infra/http/routes").is_dir() else []
    append_only = financial_rules.is_append_only(contexto, modulo)
    ns = argparse.Namespace(contexto=contexto, modulo=modulo, Entity=entity, plural=plural_real,
                            tabela=None, endpoint=None, enum=None, no_table=False,
                            sem_migration=True, timestamp="0", dry_run=True, append_only=append_only)
    values, flags = scaffold.backend_values(ns)
    prefix = f"modules/{contexto}/{modulo}/"
    expected = set()
    for _tpl, dest, cond in scaffold.BACKEND_DEST:
        if not scaffold.cond_ok(cond, flags):
            continue
        d = scaffold.substitute(dest, values)
        if d.startswith(prefix):
            expected.add(d)

    actual = {str(p.relative_to(ws / "src")) for p in files_from_folder(base)}

    # ⚠️ COMPARAÇÃO POR PAPEL, NÃO POR NOME EXATO. A AG-009 pergunta "o módulo tem um service de
    # List? um teste para cada service?", não "o arquivo se chama exatamente assim". Exigir o nome
    # derivado reprovava 150 dos 176 módulos: `exams_protocols` chama o controller de
    # `ExamsProtocolsController` e os services de `ListExamProtocolsService` — não existe um plural
    # que satisfaça os dois, e o módulo está completo. Ruído nessa escala treina a ignorar o achado
    # verdadeiro (AG-013), e completude é justamente o achado que ninguém confere à mão.
    faltando = []
    for tpl, dest, cond in scaffold.BACKEND_DEST:
        if not scaffold.cond_ok(cond, flags):
            continue
        d = scaffold.substitute(dest, values)
        if not d.startswith(prefix):
            continue  # migration mora fora da pasta do módulo
        subdir, rx = PAPEL.get(tpl, (None, None))
        if not subdir:
            continue
        pasta = base / subdir
        achou = pasta.is_dir() and any(rx.match(p.name) for p in pasta.iterdir() if p.is_file())
        if not achou:
            faltando.append(f"{subdir}/ — {DESCRICAO_PAPEL.get(tpl, tpl)}")
    # ⚠️ ALTA só para módulo QUE A FEATURE CRIOU (nenhum arquivo ainda versionado). Num módulo que
    # já existia, "falta o teste do ListTotal" é inventário do legado — verdadeiro, mas não é
    # reprovação desta entrega: 140 dos 176 módulos têm alguma lacuna, e reprovar todos é o mesmo
    # que não reprovar nenhum.
    versionados = run(["git", "ls-files", "--", str(base.relative_to(ws))], ws).strip()
    novo = not versionados
    for miss in faltando:
        rep.add("completude", base, 0, "AG-009",
                f"nenhum arquivo no papel `{miss}` — o scaffold gera este para todo módulo"
                + ("" if novo else " (módulo PRÉ-EXISTENTE: lacuna do legado, não desta entrega)"),
                alta=novo)
    if append_only:
        check_append_only(base, ws, entity, rep, novo)
    if not faltando:
        rep.note("completude (AG-009): todos os papéis do scaffold estão cobertos"
                 + (" (perfil append-only)" if append_only else ""))
    elif not novo:
        rep.note(f"completude (AG-009): {len(faltando)} papel(éis) em falta, reportados como INFO — "
                 "o módulo já existia antes desta feature")


# Papéis que o perfil append-only NÃO tem (spec 001, RN-09): achá-los num módulo append-only é o
# registro imutável ganhando uma porta de mutação.
PAPEIS_PROIBIDOS_APPEND_ONLY = ("dto-update.ts.tpl", "service-update.ts.tpl", "service-delete.ts.tpl",
                                "test-update.spec.ts.tpl", "test-delete.spec.ts.tpl")


def module_table(base: Path) -> str | None:
    ent = next(iter(sorted((base / "infra/typeorm/entities").glob("*.ts"))), None)
    m = financial_rules.ENTITY_TABLE_RE.search(ent.read_text(encoding="utf-8")) if ent else None
    return m.group(1) if m else None


def module_migrations(base: Path, ws: Path) -> list[Path]:
    """Migrations que citam a tabela do módulo (create OU alter). Moram fora da pasta do módulo, e o
    modo pasta não as via: `numeric` numa migration de ledger passava com "0 achado(s)" (achado
    MÉDIA da 1ª auditoria da spec 001)."""
    tabela = module_table(base)
    if not tabela:
        return []
    rx = re.compile(r"(?:name\s*:\s*|queryRunner\.\w+\(\s*|(?i:\btable\s+(?:if\s+(?:not\s+)?exists\s+)?))['\"]?"
                    + re.escape(tabela) + r"\b")
    return [f for f in sorted((ws / financial_rules.MIGRATIONS_DIR).glob("*.ts"))
            if rx.search(f.read_text(encoding="utf-8"))]


def files_for_folder(base: Path, ws: Path) -> list[Path]:
    """O que o modo pasta audita: a pasta do módulo + as migrations da tabela dele."""
    proprios = files_from_folder(base)
    return proprios + [m for m in module_migrations(base, ws) if m not in proprios]


def check_append_only(base: Path, ws: Path, entity: str, rep: Report, novo: bool) -> None:
    for tpl in PAPEIS_PROIBIDOS_APPEND_ONLY:
        subdir, rx = PAPEL[tpl]
        pasta = base / subdir
        for f in (sorted(pasta.iterdir()) if pasta.is_dir() else []):
            if f.is_file() and rx.match(f.name):
                rep.add("completude-append-only", f, 0, "RN-09",
                        f"{DESCRICAO_PAPEL[tpl]} num módulo append-only — o registro não muda nem some; "
                        "estorno é lançamento novo")
    # A trigger mora na migration, fora da pasta do módulo: achar a migration pela tabela da entity.
    tabela = module_table(base)
    if not tabela:
        rep.note("append-only: não achei `@Entity('<tabela>')` para localizar a migration")
        return
    migs = [f for f in module_migrations(base, ws) if "createTable" in f.read_text(encoding="utf-8")]
    if not migs:
        rep.note(f"append-only: nenhuma migration cria `{tabela}` neste workspace — trigger não conferida")
        return
    if not any("reject_mutation" in scaffold.strip_comments(f.read_text(encoding="utf-8")) for f in migs):
        rep.add("completude-append-only", migs[0], 0, "RN-09",
                f"a migration de `{tabela}` não cria a trigger `reject_mutation()` — sem ela o banco "
                "aceita UPDATE/DELETE numa tabela append-only", alta=novo)


def check_financeiro(ws_key: str, files: list[Path], ws: Path, rep: Report) -> None:
    """[RN-11 a RN-14] As 4 regras dos hooks financeiros sobre os arquivos — cada regra decide o
    próprio escopo. Pega o que foi gravado por fora do hook (AG-025: shell não dispara o hook)."""
    n = 0
    for f in files:
        try:
            rel = str(f.relative_to(ws))
        except ValueError:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for nome, (rn, regra) in financial_rules.RULES.items():
            for linha, msg in regra(ws_key, rel, text, ws):
                rep.add("financeiro", f, linha, rn, f"{msg} [{nome}]")
                n += 1
    rep.note(f"financeiro (RN-11 a RN-14): {len(files)} arquivo(s), {n} achado(s)")


DEFAULT_EXPORT_RE = re.compile(r"^export default (?:function\s+)?(\w+)", re.M)
IMPORT_PATH_RE = re.compile(r"""from\s+['"]([^'"]+)['"]""")


def check_orfao(kind: str, files: list[Path], ws: Path, rep: Report) -> None:
    """[FE-013] Componente que ninguém monta é código morto: passa no ESLint e torna inatingível
    o critério de aceite `[humano]` correspondente.

    ⚠️ A pergunta é "quem importa este CAMINHO", não "quem menciona este identificador". A primeira
    versão procurava o nome exportado e errava nos dois sentidos (auditoria da 087):
    `export default function X()` capturava o token `function`, presente em todo arquivo do repo
    (nunca acusava — 11 telas usam esse idioma); e um default importado com outro nome
    (`import CustomerFormFile from '../CustomerFormFile'` para um `export default CustomerFormFiles`)
    era acusado sem ser órfão. O caminho é o que o import de verdade carrega."""
    if kind != "frontend":
        return
    alvos = [f for f in files if f.suffix == ".tsx"]
    if not alvos:
        return
    src_dir = ws / "src"
    universo = [p for p in src_dir.rglob("*.ts*") if not any(x in PRUNE for x in p.parts)]
    # Resolve cada `from '...'` para um arquivo real, uma vez só.
    importados: set[Path] = set()
    for p in universo:
        for alvo in IMPORT_PATH_RE.findall(code_of(p)):
            if not alvo.startswith("."):
                continue
            base = (p.parent / alvo).resolve()
            for cand in (base, base.with_suffix(".tsx"), base.with_suffix(".ts"),
                         base / "index.tsx", base / "index.ts"):
                if cand.is_file() and cand != p:
                    importados.add(cand)
    for f in alvos:
        if not DEFAULT_EXPORT_RE.search(code_of(f)):
            continue
        if f.resolve() not in importados:
            m = DEFAULT_EXPORT_RE.search(code_of(f))
            rep.add("orfao", f, 1, "FE-013",
                    f"nenhum arquivo importa este caminho — `{m.group(1)}` é componente órfão")


def check_vazamento(files: list[Path], refs: list[str], rep: Report) -> None:
    """[AG-002/FE-003] O módulo de referência vazou para o módulo novo (imports, nomes, campos).

    ⚠️ UM ACHADO POR ARQUIVO, com a contagem e a primeira linha — não um por ocorrência. Um módulo
    que depende legitimamente do `--ref` (FK, contexto pai) tem centenas de menções, e despejá-las
    uma a uma é ruído; ruído treina quem lê a ignorar o achado verdadeiro (AG-013)."""
    if not refs:
        rep.note("vazamento (AG-002): PULADA — passe `--ref <modulo_de_referencia>` "
                 "(o \"espelhar X\" do plan) para habilitar")
        return
    for f in files:
        linhas = lines_of_code(f)
        for ref in refs:
            rx = re.compile(rf"\b{re.escape(ref)}", re.I)
            hits = [n for n, line in linhas if rx.search(line)]
            if hits:
                rep.add("vazamento", f, hits[0], "AG-002",
                        f"cita `{ref}` {len(hits)}× (1ª na linha {hits[0]}) — vazamento do molde? "
                        "Dependência legítima (FK, contexto pai) NÃO é vazamento: conferir")


# ⚠️ A LISTA. Um lugar só (RN-03). Cada entrada: (código, regex sobre o CÓDIGO, sufixos, mensagem).
PROIBIDOS = [
    ("FE-009", re.compile(r"inputProps=\{"), (".tsx",),
     "`inputProps={…}` é deprecated no MUI v7 — usar `slotProps={{ htmlInput: … }}`"),
    ("FE-024", re.compile(r"slots=\{\{\s*backdrop:"), (".tsx",),
     "`slots={{ backdrop }}` com o Backdrop cru perde o `z-index: -1` do slot padrão — "
     "o escurecimento pinta NA FRENTE do cartão"),
    ("BE-023", re.compile(r"\bauditDelete\b"), (".ts",),
     "`auditDelete` NÃO EXISTE neste repositório — usar `await this.ormRepository.delete(ids)`"),
]


def check_proibidos(files: list[Path], rep: Report) -> None:
    for f in files:
        linhas = lines_of_code(f)
        for code, rx, sufixos, msg in PROIBIDOS:
            if f.suffix not in sufixos:
                continue
            for n, line in linhas:
                if rx.search(line):
                    rep.add("proibidos", f, n, code, msg)
        if f.name.endswith(".routes.ts"):
            for n, campo in joi_boolean_em_query(f):
                rep.add("proibidos", f, n, "BE-016",
                        f"`{campo}: Joi.boolean()` em `Segments.QUERY` — o celebrate converte e o "
                        "controller recebe BOOLEAN; comparar com `'true'` inverte o filtro. "
                        "Usar `Joi.string().valid('true','false')` + `parseOptionalBoolean`")


# Os DOIS idiomas de QUERY no repositório: objeto literal e `Joi.object().keys({` (10 rotas usam a
# segunda forma; a 1ª versão só cobria a primeira — achado da auditoria da 087).
QUERY_BLOCK_RE = re.compile(r"\[Segments\.QUERY\]\s*:\s*(?:Joi\.object\(\)\.keys\()?\s*\{")


def joi_boolean_em_query(path: Path) -> list[tuple[int, str]]:
    """[BE-016] Campos declarados `Joi.boolean()` DENTRO do bloco `[Segments.QUERY]`."""
    src = code_of(path)
    out = []
    for m in QUERY_BLOCK_RE.finditer(src):
        i, depth = m.end(), 1
        while i < len(src) and depth:
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
            i += 1
        bloco = src[m.end():i]
        base_line = src[:m.end()].count("\n")
        for f in re.finditer(r"(\w+)\s*:\s*Joi\.boolean\(\)", bloco):
            out.append((base_line + bloco[:f.start()].count("\n") + 1, f.group(1)))
    return out


V1_IMPORT_RE = re.compile(r"from '[^']*styles/(global|globalMaterialUi)'")
# Isentos, com o motivo — sem isso a checagem vira ruído e ruído treina a ignorar o achado (AG-013).
V1_ISENTOS = {
    "src/styles/global.tsx": "define o v1",
    "src/styles/globalMaterialUi.tsx": "define o v1",
    "src/App.tsx": "monta os dois estilos globais de propósito — é o que faz a migração conviver",
}
V1_ISENTOS_PREFIX = {
    "src/components/KanbanBoard/": "board permanece v1 por decisão do usuário",
}
V1_ISENTOS_SUBSTR = {
    "FormFile": "aba de Arquivos/Anexos permanece v1 por decisão do usuário",
    "FormAnexo": "aba de Arquivos/Anexos permanece v1 por decisão do usuário",
}


HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.M)


def hunk_ranges(ws: Path, rel: str, since: str) -> list[range] | None:
    """Faixas de linha (no arquivo NOVO) que o diff tocou. `None` = arquivo novo, sem base.

    Usa `--unified=0` para que cada faixa seja só o que mudou, sem contexto — contexto faria a
    acusação alcançar linhas vizinhas que a feature não escreveu, que é exatamente o defeito.
    """
    try:
        out = subprocess.run(["git", "diff", "--no-ext-diff", "--unified=0", since, "--", rel],
                             cwd=ws, capture_output=True, check=True).stdout.decode(errors="replace")
    except (subprocess.CalledProcessError, OSError):
        return None
    if not out.strip():
        # Sem diff contra a base: ou é untracked (arquivo novo), ou não mudou.
        try:
            r = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel],
                               cwd=ws, capture_output=True)
            return None if r.returncode != 0 else []
        except OSError:
            return None
    faixas = []
    for m in HUNK_RE.finditer(out):
        ini = int(m.group(1))
        n = int(m.group(2)) if m.group(2) is not None else 1
        if n:
            faixas.append(range(ini, ini + n))
    return faixas


def check_v1_import(kind: str, files: list[Path], ws: Path, rep: Report,
                    since: str | None = None) -> None:
    """[spec 086 + 090] Import do padrão visual v1.

    ⚠️ **Consciência de hunk (spec 090, RN-05/RN-06)**. Antes, esta checagem varria o arquivo
    INTEIRO: qualquer feature que tocasse uma linha de uma tela legada colhia a acusação sobre
    imports que ela não escreveu. Medido na spec 062: acusou `DonorFormRegisterData:85,92`, linhas
    **byte-idênticas ao HEAD**, num diff cujo único hunk começa 1.229 linhas abaixo — e gastou uma
    decisão do usuário para autorizar. **231 páginas importam v1**; com a regra assim, ela dispara
    em qualquer feature que encoste em qualquer uma, e a saída natural é engordar a lista de
    isenções até virar ruído — o que o próprio comentário de `V1_ISENTOS` adverte.

    A intenção da 086 ("legado que migra quando a feature as tocar") **não é revogada**: ela é
    tornada proporcional. Continua ALTA quando:
      - o arquivo é **novo** (tela nova nasce v2, sem exceção); ou
      - a linha do import está **dentro de um hunk** — quem escreveu aquela linha responde por ela.

    Sem `--diff`/`--since` não há base, e aí vale o comportamento antigo (arquivo inteiro), que é o
    certo para auditar um módulo pronto.
    """
    if kind != "frontend":
        return
    for f in files:
        rel = str(f.relative_to(ws))
        if rel in V1_ISENTOS or any(rel.startswith(p) for p in V1_ISENTOS_PREFIX):
            continue
        if any(s in rel for s in V1_ISENTOS_SUBSTR):
            continue
        faixas = None if since is None else hunk_ranges(ws, rel, since)
        for n, line in lines_of_code(f):
            if not V1_IMPORT_RE.search(line):
                continue
            if faixas is not None and not any(n in r for r in faixas):
                continue  # linha que esta feature não escreveu
            rep.add("v1-import", f, n, "086",
                    "importa o padrão visual v1 — tela nova usa `styles/global_v2` e "
                    "`styles/globalMaterialUi_v2` (skill `ui-v2`)")


# ----------------------------------------------------------------------------- contrato (INFO)
# Campos que o backend tem por natureza e a tela não declara. `status` SAIU desta lista: é campo
# de negócio legítimo em vários módulos, e excluí-lo escondia divergência real (auditoria da 087).
BACKEND_ONLY = re.compile(r"^(user_created|user_updated|created_at|updated_at)$|"
                          r"(_key|_secret|_pem|_payload|_hash)$|^password")
FIELD_RE = re.compile(r"^\s*(\w+)\??\s*:", re.M)


def iface_fields(text: str, nome: str) -> set[str]:
    m = re.search(rf"(?:export\s+)?(?:default\s+)?interface\s+{re.escape(nome)}\b[^{{]*\{{", text)
    if not m:
        return set()
    i, depth = m.end(), 1
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return set(FIELD_RE.findall(text[m.end():i - 1]))


def check_contrato(rep: Report) -> None:
    """[AG-022] O tipo do frontend é uma AFIRMAÇÃO sobre a resposta, não uma verificação: quando o
    backend muda a forma do DTO, nada quebra — a funcionalidade some em silêncio.

    Comparação por NOME, nunca por tipo, e sempre INFO: o julgamento de que lado corrige é do
    agente (no V-Corp, 12 divergências e a maioria era legítima)."""
    for fe_ws in workspaces.of_kind("frontend"):
        _check_contrato_um(rep, WS["backend"] / "src", WS[fe_ws] / "src")


def _check_contrato_um(rep: Report, be: Path, fe: Path) -> None:
    tipos = {}
    for p in (fe / "types").glob("*.types.ts"):
        tipos[p.stem.replace(".types", "")] = p.read_text(encoding="utf-8", errors="replace")
    for dto in sorted(be.rglob("dtos/ICreate*DTO.ts")):
        entity = dto.name[len("ICreate"):-len("DTO.ts")]
        campos = iface_fields(dto.read_text(encoding="utf-8", errors="replace"), f"ICreate{entity}DTO")
        campos = {c for c in campos if not BACKEND_ONLY.search(c)}
        if not campos:
            continue
        for arq, src in tipos.items():
            fields = iface_fields(src, f"I{entity}")
            if not fields:
                continue
            faltam = sorted(campos - fields)
            if faltam:
                rep.add("contrato", fe / "types" / f"{arq}.types.ts", 0, "AG-022",
                        f"`I{entity}` não declara {', '.join('`'+x+'`' for x in faltam)} — "
                        f"campos que o `ICreate{entity}DTO` tem (comparação por nome; conferir se é real)",
                        alta=False)


PAYLOAD_CALL_RE = re.compile(r"\b(?:create|update)\w+\(\s*\{")


def top_level_keys(src: str, start: int) -> tuple[set[str], int]:
    """Chaves de PRIMEIRO NÍVEL do objeto literal que começa em `start` (logo após o `{`).

    ⚠️ Casamento de chaves com profundidade, não regex. A primeira versão usava
    `\\{(.*?)\\n\\s*\\}\\s*\\)` e o `.*?` atravessava o fim do objeto: acusou `position` num
    payload que envia `products_id`, `title` e `sort_order`. Detector não validado não é detector
    (AG-020) — e falso positivo em INFO ainda treina quem lê a ignorar o achado verdadeiro."""
    chaves, i, depth, buf = set(), start, 1, []
    while i < len(src) and depth:
        c = src[i]
        if c in "{[(":
            depth += 1
        elif c in "}])":
            depth -= 1
            if depth == 0:
                break
        elif depth == 1:
            buf.append(c)
        i += 1
    for m in re.finditer(r"(?:^|,)\s*(\w+)\s*:", "".join(buf)):
        chaves.add(m.group(1))
    return chaves, i


def check_joi_payload(rep: Report) -> None:
    """[FE-025] Espelhar uma tela de outro módulo NÃO espelha o contrato da rota: o payload chega
    com campo que o Joi não aceita, e o 400 só aparece com o servidor de pé. INFO — a comparação é
    por nome e não conhece campo opcional.

    ⚠️ LIMITE DECLARADO: compara contra a UNIÃO de todos os `[Segments.BODY]` do backend, não
    contra a rota que aquela chamada de fato usa. Consequência: **acusa só o campo que não existe
    em rota nenhuma**; campo que existe noutra rota passa. É falso negativo por construção — o
    preço de não ter que resolver `create<X>()` → endpoint → arquivo de rota. Resultado limpo aqui
    não prova contrato certo; resultado sujo é forte indício."""
    for fe_ws in workspaces.of_kind("frontend"):
        _check_joi_payload_um(rep, WS["backend"] / "src", WS[fe_ws] / "src")


def _check_joi_payload_um(rep: Report, be: Path, fe: Path) -> None:
    rotas = {}
    for p in be.rglob("*.routes.ts"):
        src = code_of(p)
        for m in re.finditer(r"\[Segments\.BODY\]\s*:\s*(?:Joi\.object\(\)\.keys\()?\s*\{", src):
            i, depth = m.end(), 1
            while i < len(src) and depth:
                if src[i] == "{":
                    depth += 1
                elif src[i] == "}":
                    depth -= 1
                i += 1
            rotas.setdefault(p, set()).update(re.findall(r"(\w+)\s*:\s*Joi\.", src[m.end():i]))
    if not rotas:
        return
    todas = set().union(*rotas.values())
    for page in fe.rglob("pages/**/index.tsx"):
        src = code_of(page)
        for m in PAYLOAD_CALL_RE.finditer(src):
            chaves, _ = top_level_keys(src, m.end())
            desconhecidas = {k for k in chaves if k not in todas and not BACKEND_ONLY.search(k)}
            if desconhecidas and len(desconhecidas) < len(chaves):
                rep.add("joi-payload", page, src[:m.start()].count("\n") + 1, "FE-025",
                        f"payload envia {', '.join('`'+x+'`' for x in sorted(desconhecidas))}, que "
                        "nenhum `[Segments.BODY]` do backend declara (comparação por nome)",
                        alta=False)


# ----------------------------------------------------------------------------- self-test
def _self_test_hunk() -> list[str]:
    """Consciência de hunk (spec 090), num REPOSITÓRIO GIT DE VERDADE.

    ⚠️ A primeira versão deste bloco recalculava o predicado inline
    (`faixas is None or any(linha in r ...)`) — ou seja, **testava a própria expressão do teste**.
    A auditoria da T-17 provou por mutação: trocar `if faixas is not None and not any(...)` por
    `if faixas is not None:` **cega a regra** sob `--diff` e o self-test continuava **verde**.
    Conferido à mão aqui: mutante → self-test rc=0, e a regra deixava de acusar.

    Um self-test que sobrevive à mutação que cega o que ele cobre não é verificação — e como
    nenhum gate alcança `.py` (dívida da 087), **este self-test É a verificação**. Por isso agora
    ele chama `hunk_ranges()` e `check_v1_import()` de verdade.
    """
    import shutil
    import tempfile
    falhas: list[str] = []
    git = shutil.which("git")
    if not git:
        print("\n  consciência de hunk: PULADA (git ausente)")
        return falhas
    print("\n  consciência de hunk (repositório git de fixture):")
    V1 = "import { Paragraph } from '../../../styles/global'\n"
    with tempfile.TemporaryDirectory(prefix="check-module-hunk-") as tmp:
        ws = Path(tmp)
        run = lambda *a: subprocess.run([git, *a], cwd=ws, capture_output=True)
        run("init", "-q", "."); run("config", "user.email", "t@t"); run("config", "user.name", "t")
        # ⚠️ A ORDEM É PARTE DA FIXTURE, e errar nela dá caso falso — aconteceu duas vezes ao
        # escrever isto. Tudo que precisa estar COMMITADO vem primeiro; o que precisa estar
        # untracked ou modificado na árvore vem por último, depois do commit final.
        antigo = ws / "antigo.tsx"
        antigo.write_text("import React from 'react'\n" + V1 + ("const x = 1\n" * 40), encoding="utf-8")
        tocado = ws / "tocado.tsx"
        tocado.write_text("import React from 'react'\n" + ("const z = 0\n" * 3), encoding="utf-8")
        # Hunk MULTI-LINHA com o import no meio. Sem ele, `n = 1` fixo em vez de `int(m.group(2))`
        # sobrevive — todos os hunks de uma linha dão o mesmo resultado. Achado da reauditoria.
        multi = ws / "multi.tsx"
        multi.write_text("import React from 'react'\n" + ("const w = 0\n" * 6), encoding="utf-8")
        run("add", "-A"); run("commit", "-qm", "base")
        # `marco` é a base do caso `--since <tag>` — o caminho do /sprint-close, que a 1ª versão
        # desta fixture não cobria: só exercitava `HEAD`, e um mutante que ignorasse o `since`
        # passava verde.
        run("tag", "marco")
        multi.write_text("import React from 'react'\n"
                         + "const a = 1\n" + V1 + "const b = 2\n"
                         + ("const w = 0\n" * 6), encoding="utf-8")
        run("add", "-A"); run("commit", "-qm", "com-multi")

        # A partir daqui, NADA é commitado — é o estado que o gate encontra numa feature real.
        # (1) modifica LONGE do import — é o caso da spec 062
        antigo.write_text(antigo.read_text(encoding="utf-8").replace("const x = 1\n" * 40,
                          "const x = 1\n" * 39 + "const y = 2\n"), encoding="utf-8")
        # (2) modifica NA linha do import
        tocado.write_text("import React from 'react'\n" + V1 + ("const z = 0\n" * 3), encoding="utf-8")
        # (3) arquivo NOVO, untracked. A 1ª versão commitava este arquivo, tornando-o "tracked e
        # inalterado", e o caso saía `limpo` — a fixture é que estava errada, não o código, e foi o
        # teste de verdade que mostrou, na primeira execução.
        novo = ws / "novo.tsx"
        novo.write_text("import React from 'react'\n" + V1, encoding="utf-8")

        for arq, esperado, rot, base in [
            (antigo, "limpo", "import longe do hunk (caso da spec 062)", "HEAD"),
            (tocado, "acusa", "import DENTRO do hunk", "HEAD"),
            (novo,   "acusa", "arquivo NOVO (tela nova nasce v2)", "HEAD"),
            (multi,  "acusa", "hunk MULTI-LINHA, import no meio, base `--since <tag>`", "marco"),
        ]:
            rep = Report()
            check_v1_import("frontend", [arq], ws, rep, base)
            obtido = "acusa" if rep.blocking else "limpo"
            marca = "✅" if obtido == esperado else "❌"
            print(f"  {marca} {rot}: esperado {esperado}, obtido {obtido}")
            if obtido != esperado:
                falhas.append(rot)
        # sem base, o comportamento antigo (arquivo inteiro) tem de voltar
        rep = Report()
        check_v1_import("frontend", [antigo], ws, rep, None)
        obtido = "acusa" if rep.blocking else "limpo"
        marca = "✅" if obtido == "acusa" else "❌"
        print(f"  {marca} sem base (--diff ausente): esperado acusa, obtido {obtido}")
        if obtido != "acusa":
            falhas.append("sem base")
    return falhas


def _self_test_financeiro() -> list[str]:
    """[CA-12 da spec 001] Módulo append-only CORRIGIDO (gerado pelo scaffold, nunca diverge do
    template) não tem achado bloqueante; cada mutação de `tests/check-module-financeiro/
    mutations.json`, aplicada SOZINHA, produz o achado do `code` dela."""
    import contextlib
    import io
    import shutil
    import tempfile
    cfg = json.loads((HERE / "tests/check-module-financeiro/mutations.json").read_text(encoding="utf-8"))
    falhas: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="check-module-fin-"))
    try:
        ok_ws = tmp / "corrigido" / workspaces.load()["backend"]["path"]
        ns = argparse.Namespace(contexto=cfg["contexto"], modulo=cfg["modulo"], Entity=cfg["entity"],
                                plural=None, tabela=None, endpoint=None, enum=None, no_table=False,
                                sem_migration=False, append_only=True, timestamp="1000000000000",
                                dry_run=False)
        values, flags = scaffold.backend_values(ns)
        g = scaffold.Generator("backend", values, flags, False, ws=ok_ws, fmt=False)
        with contextlib.redirect_stdout(io.StringIO()):
            g.generate()
        mig = next(f for f in g.created if "/migrations/" in str(f))

        def auditar(ws: Path) -> Report:
            rep = Report()
            base = ws / "src/modules" / cfg["contexto"] / cfg["modulo"]
            files = files_for_folder(base, ws)  # o MESMO caminho da CLI — não a migration à mão
            if not any("/migrations/" in str(f) for f in files):
                rep.add("self-test", base, 0, "SELF", "files_for_folder não achou a migration do módulo")
            check_completude("backend", base, ws, rep)
            check_financeiro("backend", files, ws, rep)
            return rep

        rep = auditar(ok_ws)
        marca = "✅" if not rep.blocking else "❌"
        print(f"  {marca} financeiro/corrigido: esperado limpo, obtido {'acusa' if rep.blocking else 'limpo'}")
        for f in rep.blocking:
            print(f"       {f}")
        if rep.blocking:
            falhas.append("financeiro/corrigido")
        for i, mu in enumerate(cfg["mutacoes"]):
            ws = tmp / f"viola{i}" / workspaces.load()["backend"]["path"]
            shutil.copytree(ok_ws, ws)
            base = ws / "src/modules" / cfg["contexto"] / cfg["modulo"]
            if "new_file" in mu:
                (base / mu["new_file"]).write_text(mu["content"], encoding="utf-8")
            else:
                alvo = (ws / mig.relative_to(ok_ws)) if mu["file"] == "@migration" else base / mu["file"]
                txt = alvo.read_text(encoding="utf-8")
                if mu["find"] not in txt:
                    falhas.append(f"financeiro/{mu['desc']}: trecho a mutar não existe mais no gerado")
                    continue
                alvo.write_text(txt.replace(mu["find"], mu["replace"]), encoding="utf-8")
            rep = auditar(ws)
            codes = {f.code for f in rep.blocking}
            ok = mu["code"] in codes
            print(f"  {'✅' if ok else '❌'} financeiro/{mu['desc']}: esperado {mu['code']}, obtido {sorted(codes) or 'limpo'}")
            if not ok:
                falhas.append(f"financeiro/{mu['desc']}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return falhas


def self_test() -> int:
    """Casos versionados: o padrão proibido em comentário NÃO acusa; em código, acusa (CA-03).

    ⚠️ `check_bloco_pendente` fica FORA deste self-test de propósito: ele lê o arquivo cru, e as
    fixtures trazem `__CAMPOS__` em comentário justamente para demonstrar o filtro. Rodá-lo aqui
    acusaria a fixture pelo que ela existe para exibir — a AG-013 de novo. Quem exercita o
    `bloco-pendente` é o CA-02, sobre um módulo recém-gerado."""
    base = HERE / "tests/check-module"
    if not base.is_dir():
        print(f"self-test: faltam os casos em {base.relative_to(ROOT)}", file=sys.stderr)
        return 2
    falhas = []
    for caso in sorted(base.glob("*.t*")):
        esperado = "acusa" if caso.stem.endswith("-acusa") else "limpo"
        rep = Report()
        check_proibidos([caso], rep)
        check_placeholder([caso], rep)
        check_v1_import("frontend", [caso], base, rep)
        obtido = "acusa" if rep.blocking else "limpo"
        marca = "✅" if obtido == esperado else "❌"
        print(f"  {marca} {caso.name}: esperado {esperado}, obtido {obtido}")
        for f in rep.findings:
            print(f"       {f}")
        if obtido != esperado:
            falhas.append(caso.name)
    falhas += _self_test_hunk()
    falhas += _self_test_financeiro()

    if falhas:
        print(f"\n❌ self-test REPROVADO: {', '.join(falhas)}", file=sys.stderr)
        return 2
    print("\n✅ self-test aprovado — comentário não acusa, código acusa,")
    print("   e a acusação de v1 respeita o hunk (arquivo novo continua acusando)")
    return 0


# ----------------------------------------------------------------------------- cli
def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="check-module.py", add_help=True)
    p.add_argument("workspace", nargs="?", choices=list(workspaces.load()))
    p.add_argument("pasta", nargs="?")
    p.add_argument("--diff", action="store_true")
    p.add_argument("--since")
    p.add_argument("--ref", action="append", default=[])
    p.add_argument("--contract", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)

    if a.self_test:
        return self_test()
    if not a.workspace:
        p.print_help(sys.stderr)
        return 64
    ws = WS[a.workspace]
    kind = workspaces.load()[a.workspace]["kind"]
    if not ws.is_dir():
        print(f"check-module: {ws} não existe neste checkout", file=sys.stderr)
        return 65

    rep = Report()
    base = None
    base_ref = None
    if a.pasta:
        alvo = (ws / a.pasta).resolve()
        if alvo.is_file():
            # Arquivo avulso: útil para conferir um acerto/não-acerto à mão. `completude` não roda.
            files, escopo = [alvo], f"arquivo {a.pasta}"
        elif alvo.is_dir():
            base = alvo
            files = files_for_folder(base, ws)
            escopo = f"pasta {a.pasta}"
        else:
            print(f"check-module: caminho inexistente: {a.pasta}", file=sys.stderr)
            return 65
    elif a.diff or a.since:
        base_ref = a.since or "HEAD"
        files = files_from_diff(ws, base_ref)
        escopo = f"diff desde {base_ref}"
    else:
        p.print_help(sys.stderr)
        return 64

    check_bloco_pendente(files, rep)
    check_placeholder(files, rep)
    check_proibidos(files, rep)
    check_v1_import(kind, files, ws, rep, base_ref if (a.diff or a.since) else None)
    check_orfao(kind, files, ws, rep)
    check_vazamento(files, a.ref, rep)
    check_financeiro(a.workspace, files, ws, rep)
    if base:
        check_completude(kind, base, ws, rep)
    if a.contract:
        # ⚠️ O contrato é POR NATUREZA entre os dois workspaces — não filtra pelo `<workspace>` do
        # argumento. Rodar os dois lados duplicaria os mesmos INFO (auditoria da 087); o resumo diz
        # isso para que ninguém conte duas vezes.
        rep.note("--contract compara backend × frontend e NÃO depende do workspace do argumento — "
                 "rodar uma vez basta")
        check_contrato(rep)
        check_joi_payload(rep)

    if a.json:
        print(json.dumps({"workspace": a.workspace, "escopo": escopo, "arquivos": len(files),
                          "notas": rep.notes,
                          "achados": [f.as_dict() for f in rep.findings]}, ensure_ascii=False, indent=2))
    else:
        print(f"check-module: {a.workspace} — {escopo}, {len(files)} arquivo(s)")
        for nota in rep.notes:
            print(f"  ℹ️ {nota}")
        for f in sorted(rep.findings, key=lambda x: (not x.alta, x.rel(), x.line)):
            print(f"  {'❌' if f.alta else '⚠️ '} {f}")
        n_alta, n_info = len(rep.blocking), len(rep.findings) - len(rep.blocking)
        print(f"\n{'❌' if n_alta else '✅'} {n_alta} bloqueante(s), {n_info} INFO")
    return 1 if rep.blocking else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
