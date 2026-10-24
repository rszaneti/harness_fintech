#!/usr/bin/env python3
"""
financial_rules.py — as regras financeiras do harness, num lugar só (spec 001, RN-11 a RN-16).

Quem usa:
  - os 4 hooks pós-edição (`money-bigint.py`, `ledger-immutable.py`, `idempotency-required.py`,
    `no-secret-in-code.py`), que são pontos de entrada finos sobre `cli()`;
  - o `check-module.py` (check `financeiro`), que chama as mesmas funções;
  - o `scaffold.py --self-test static`, que roda as 4 sobre o módulo append-only gerado.

Regra mora AQUI e só aqui (o mesmo princípio da RN-03 da spec 087 do ERP): skill e markdown mandam
rodar o hook, não repetem a lista de padrões.

Cada regra é `f(ws_key, rel, text, ws_dir) -> [(linha, mensagem)]`:
  ws_key  chave do workspace (`.claude/workspaces.json`) — "" se o arquivo não é de workspace
  rel     caminho relativo ao workspace (`src/modules/ledger/...`)
  text    conteúdo do arquivo
  ws_dir  diretório do workspace (para achar a entity de uma tabela) — pode não existir
A própria regra decide se o arquivo está no escopo dela. É de propósito: o teste por fixture cobre
também o ESCOPO, que é onde os detectores costumam errar calados.

⚠️ As regras 11–13 olham o CÓDIGO SEM COMENTÁRIO (AG-013): a skill e os templates citam `save(`,
`numeric` e `idempotency-exempt` em comentário para ensinar a evitá-los. Duas leituras usam o texto
CRU: o marcador de isenção (vive em comentário por construção) e a **RN-14 inteira** — credencial
comentada é a forma mais comum de vazamento, e um aviso legítimo não contém uma chave de verdade
(achado ALTA da 1ª auditoria da spec 001: a 1ª versão filtrava comentário e deixava passar
`// AKIA…` e `/* -----BEGIN … PRIVATE KEY----- */`).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARNESS = HERE.parent
sys.path.insert(0, str(HARNESS / "scaffold"))
sys.path.insert(0, str(HARNESS / "scripts"))
from scaffold import strip_comments_keep_lines  # noqa: E402
import workspaces  # noqa: E402

# ----------------------------------------------------------------------------- escopo
# `documentacao/04` §4. Contexto financeiro = onde há dinheiro, saldo, cobrança ou ordem ao BTG.
FINANCIAL_CONTEXTS = {"ledger", "accounts", "charges", "payouts", "splits", "btg", "platforms"}
# Módulos cujo registro nunca muda nem some (`documentacao/04` §4, perfil `--append-only`).
APPEND_ONLY_MODULES = {"ledger/*", "audit/*", "btg/btg_events", "splits/split_executions"}
# Só o backend da plataforma move dinheiro; o simulador do BTG é um fake e fica fora.
MONEY_WORKSPACES = {"backend"}

MIGRATIONS_DIR = "src/shared/infra/typeorm/migrations/"


def module_of(rel: str) -> tuple[str, str] | None:
    parts = rel.split("/")
    if len(parts) >= 4 and parts[0] == "src" and parts[1] == "modules":
        return parts[2], parts[3]
    return None


def is_append_only(ctx: str, mod: str) -> bool:
    return f"{ctx}/*" in APPEND_ONLY_MODULES or f"{ctx}/{mod}" in APPEND_ONLY_MODULES


def code_lines(text: str) -> list[str]:
    return strip_comments_keep_lines(text).split("\n")


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


# ----------------------------------------------------------------------------- RN-11 dinheiro
FRACTIONAL_TYPES = r"numeric|decimal|float|float4|float8|double precision|real|money"
COLUMN_TYPE_RE = re.compile(
    r"(?:\btype\s*:\s*|@Column\(\s*)['\"](" + FRACTIONAL_TYPES + r")['\"]", re.I)
SQL_DDL_RE = re.compile(r"(?i)\b(create|alter)\s+table\b|\badd\s+column\b")
SQL_TYPE_RE = re.compile(r"(?i)\b(numeric|decimal|float[48]?|double\s+precision|real|money)\b")
STRING_RE = re.compile(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`")
CENTS_MIGRATION_RE = re.compile(r"name\s*:\s*['\"](\w+_cents)['\"]([^}]*)\}")
FLOAT_CALL_RE = re.compile(r"\bparseFloat\s*\(|\.toFixed\s*\(")
TABLE_NAME_RE = re.compile(r"new\s+Table\(\s*\{\s*name\s*:\s*['\"](\w+)['\"]"
                           r"|queryRunner\.\w+\(\s*['\"](\w+)['\"]"
                           r"|(?i:\btable\s+(?:if\s+(?:not\s+)?exists\s+)?)\"?(\w+)\"?")
ENTITY_TABLE_RE = re.compile(r"@Entity\(\s*['\"](\w+)['\"]")


def entity_contexts(ws_dir: Path | None) -> dict[str, str]:
    """{tabela: contexto} lido das entities do workspace — é o que diz de quem é uma migration."""
    out: dict[str, str] = {}
    base = (ws_dir / "src/modules") if ws_dir else None
    if not base or not base.is_dir():
        return out
    for ent in base.glob("*/*/infra/typeorm/entities/*.ts"):
        m = ENTITY_TABLE_RE.search(ent.read_text(encoding="utf-8", errors="replace"))
        if m:
            out[m.group(1)] = ent.relative_to(base).parts[0]
    return out


def _migration_is_financial(code: str, ws_dir: Path | None) -> bool:
    tabelas = {next(g for g in m.groups() if g) for m in TABLE_NAME_RE.finditer(code)}
    tabelas.discard("if")
    if not tabelas:
        return True  # sem tabela identificável: falha FECHADA
    ctxs = entity_contexts(ws_dir)
    # Tabela sem entity correspondente conta como financeira (falha fechada — plan 2.8.4).
    return any(ctxs.get(t) is None or ctxs[t] in FINANCIAL_CONTEXTS for t in tabelas)


def money_violations(ws_key: str, rel: str, text: str, ws_dir: Path | None = None) -> list[tuple[int, str]]:
    if ws_key not in MONEY_WORKSPACES or not rel.endswith(".ts"):
        return []
    code = strip_comments_keep_lines(text)
    mod = module_of(rel)
    if rel.startswith(MIGRATIONS_DIR):
        if not _migration_is_financial(code, ws_dir):
            return []
    elif not (mod and mod[0] in FINANCIAL_CONTEXTS):
        return []
    out: list[tuple[int, str]] = []
    for m in COLUMN_TYPE_RE.finditer(code):
        out.append((_line_of(code, m.start()),
                    f"coluna `{m.group(1)}` em contexto financeiro — dinheiro é `bigint` em centavos "
                    "(`*_cents`); proporção é inteiro na unidade que a spec da feature define"))
    for s in STRING_RE.finditer(code):
        if SQL_DDL_RE.search(s.group(0)):
            for t in SQL_TYPE_RE.finditer(s.group(0)):
                out.append((_line_of(code, s.start() + t.start()),
                            f"SQL com tipo `{t.group(1)}` em contexto financeiro — usar `bigint` em centavos"))
    # `@Column(` com o span balanceado — `[^)]*` parava no `)` de `transformer: f()` e o `*_cents`
    # escapava (achado BAIXA da 1ª auditoria).
    for m in re.finditer(r"@Column\s*\(", code):
        fecha = _span_end(code, m.end() - 1)
        resto = code[fecha + 1:]
        # pular outros decorators (`@Index()`) e modificadores (`public readonly`) até a propriedade
        while True:
            dec = re.match(r"\s*@\w+\s*", resto)
            if dec:
                fim = dec.end()
                if resto[fim:fim + 1] == "(":
                    fim = _span_end(resto, fim) + 1
                resto = resto[fim:]
                continue
            mod = re.match(r"\s*(?:public|private|protected|readonly|declare)\b", resto)
            if mod:
                resto = resto[mod.end():]
                continue
            break
        prop = re.match(r"\s*(\w+)", resto)
        if prop and prop.group(1).endswith("_cents") and not re.search(r"['\"](?:bigint|int8)['\"]", code[m.end():fecha]):
            out.append((_line_of(code, m.start()),
                        f"`{prop.group(1)}` não é `@Column('bigint')` — coluna `*_cents` é sempre bigint"))
    for m in CENTS_MIGRATION_RE.finditer(code):
        tipo = re.search(r"type\s*:\s*['\"](\w[\w ]*)['\"]", m.group(2))
        if not tipo or tipo.group(1).lower() not in ("bigint", "int8"):
            out.append((_line_of(code, m.start()),
                        f"coluna `{m.group(1)}` com tipo `{tipo.group(1) if tipo else '?'}` — "
                        "coluna `*_cents` é sempre `bigint`"))
    for m in FLOAT_CALL_RE.finditer(code):
        out.append((_line_of(code, m.start()),
                    f"`{m.group(0).strip('(').strip()}` em contexto financeiro — aritmética de dinheiro é "
                    "inteira em centavos; formatação é do frontend"))
    return sorted(set(out))


# ----------------------------------------------------------------------------- RN-12 imutabilidade
MUTATION_RE = re.compile(
    r"\.(save|update|delete|remove|softDelete|softRemove|restore|upsert|increment|decrement|clear|orUpdate)\s*\(")
# Sem diferenciar maiúsculas, mas com FORMA de SQL (`update <tabela> set`), para não casar texto comum.
SQL_MUTATION_RE = re.compile(r"(?i)\bupdate\s+\"?\w+\"?\s+set\b|\bdelete\s+from\b"
                             r"|\btruncate\s+(?:table\s+)?\"?[a-z_][a-z0-9_]*\"?\s*(?:;|cascade\b|restart\b|$|['\"`])")
# Variável que guarda um Hmac/Hash: `const hmac = createHmac(...)` e depois `hmac.update(body)` — a
# forma em dois passos da documentação do Node (achado MÉDIA da 1ª auditoria).
CRYPTO_VAR_RE = re.compile(r"\b(\w+)\s*=\s*(?:\w+\.)?create(?:Hmac|Hash)\s*\(")
# `createHmac(...).update(corpo)` / `createHash(...).update(...)` é a API do `crypto`, não escrita
# em banco — e a verificação de assinatura do webhook mora justamente em `btg_events` (append-only).
CRYPTO_CHAIN_RE = re.compile(r"\bcreate(?:Hmac|Hash)\s*\(")


def immutable_violations(ws_key: str, rel: str, text: str, ws_dir: Path | None = None) -> list[tuple[int, str]]:
    if ws_key not in MONEY_WORKSPACES or not rel.endswith(".ts"):
        return []
    mod = module_of(rel)
    if not mod or not is_append_only(*mod):
        return []
    if "/tests/" in rel and rel.endswith(".spec.ts"):
        return []  # teste pode provar que a mutação é recusada
    lines = code_lines(text)
    crypto_vars = set(CRYPTO_VAR_RE.findall("\n".join(lines)))
    out = []
    for n, line in enumerate(lines, 1):
        for m in MUTATION_RE.finditer(line):
            if m.group(1) == "update":
                receptor = re.search(r"(\w+)\s*$", line[:m.start()])
                if receptor and receptor.group(1) in crypto_vars:
                    continue
                anterior = next((l for l in reversed(lines[:n - 1]) if l.strip()), "")
                if CRYPTO_CHAIN_RE.search(line[:m.start()]) or (
                        line[:m.start()].strip() == "" and CRYPTO_CHAIN_RE.search(anterior)):
                    continue
            out.append((n, f"`.{m.group(1)}(` em módulo append-only ({mod[0]}/{mod[1]}) — registro "
                           "imutável não se altera nem se apaga; estorno é lançamento NOVO; inserção é "
                           "por `createQueryBuilder().insert()`, nunca `save()`"))
    code = "\n".join(lines)
    for s in STRING_RE.finditer(code):
        for t in SQL_MUTATION_RE.finditer(s.group(0)):
            out.append((_line_of(code, s.start() + t.start()),
                        f"SQL `{t.group(0).strip()}` em módulo append-only ({mod[0]}/{mod[1]}) — o banco "
                        "rejeita pela trigger `reject_mutation()`, e o código não deve tentar"))
    return sorted(set(out))


# ----------------------------------------------------------------------------- RN-13/15 idempotência
# ⚠️ Vê TODA chamada `.post/.put/.patch(` — inclusive `router.route('/').post(` e cadeias. A 2ª
# versão exigia um identificador antes do ponto (para isentar só pelo mesmo router) e, com isso,
# deixou de VER essas formas: regressão ALTA achada na reauditoria da spec 001. O receptor agora é
# lido à parte (`_receptor`) e só decide a isenção por `.use`; sem receptor simples, não há isenção.
WRITE_ROUTE_RE = re.compile(r"\.(post|put|patch)\s*\(")
USE_RE = re.compile(r"(\w+)\s*\.use\s*\(")
EXEMPT_RE = re.compile(r"idempotency-exempt\b\s*:\s*(.*)$")
# Marcador sem `:` só quando ele ABRE o comentário — prosa que apenas fala do marcador não é marcador
# (BAIXA da reauditoria).
EXEMPT_ANY_RE = re.compile(r"(?://|/\*|^\s*\*)\s*idempotency-exempt\b(?!\s*:)")
IDEM_IDENT_RE = re.compile(r"\bensureIdempotency\b")


def _receptor(code: str, dot: int) -> str | None:
    """Identificador imediatamente antes do `.` (com espaço/quebra de linha no meio), ou None quando
    o que vem antes é `)` — `r.route('/').post(`, `r.get(...).post(`."""
    m = re.search(r"(\w+)\s*$", code[:dot])
    return m.group(1) if m else None


def _blank_strings(code: str) -> str:
    """Troca o CONTEÚDO das strings por espaços (mesmas posições): a string `'ensureIdempotency'`
    não é o middleware (achado BAIXA da 1ª auditoria)."""
    return STRING_RE.sub(lambda m: m.group(0)[0] + re.sub(r"[^\n]", " ", m.group(0)[1:-1]) + m.group(0)[-1], code)
EXEMPT_MIN = 10


def _span_end(code: str, open_paren: int) -> int:
    """Índice do `)` que fecha o `(` em `open_paren`, respeitando string (o código já vem sem
    comentário). Sem fechamento, o fim do texto."""
    depth, i, n, quote = 0, open_paren, len(code), None
    while i < n:
        c = code[i]
        if quote:
            if c == "\\":
                i += 2; continue
            if c == quote or (c == "\n" and quote != "`"):
                quote = None
        elif c in "'\"`":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n


def _exempt_motive(raw_lines: list[str], first: int, last: int) -> str | None:
    """Motivo do marcador associado à chamada nas linhas [first, last] (1-based) ou no bloco de
    comentário imediatamente acima de `first`. None = sem marcador."""
    cand = list(range(first, last + 1))
    k = first - 1
    while k >= 1 and raw_lines[k - 1].strip().startswith(("//", "/*", "*")):
        cand.append(k); k -= 1
    for ln in cand:
        m = EXEMPT_RE.search(raw_lines[ln - 1])
        if m:
            return m.group(1).strip().rstrip("*/").strip()
    return None


def idempotency_violations(ws_key: str, rel: str, text: str, ws_dir: Path | None = None) -> list[tuple[int, str]]:
    if ws_key not in MONEY_WORKSPACES or not rel.startswith("src/") or not (
            rel.endswith(".routes.ts") or rel.endswith("/routes/index.ts")):
        return []
    code = strip_comments_keep_lines(text)
    ident = _blank_strings(code)  # onde procurar o IDENTIFICADOR ensureIdempotency
    raw = text.split("\n")
    out = []
    for n, line in enumerate(raw, 1):
        if EXEMPT_ANY_RE.search(line):
            out.append((n, "`idempotency-exempt` sem `:` — a forma é `// idempotency-exempt: <motivo>`; "
                           "sem os dois-pontos não vale como isenção"))
    # Marcador inválido é reprovado onde estiver — não só quando associado a uma rota (RN-15).
    for n, line in enumerate(raw, 1):
        m = EXEMPT_RE.search(line)
        if m and len(re.sub(r"\s", "", m.group(1).rstrip("*/"))) < EXEMPT_MIN:
            out.append((n, f"`idempotency-exempt` sem motivo (mínimo {EXEMPT_MIN} caracteres depois de "
                           "`:`) — isenção sem motivo não vale como isenção"))
    # `.use(ensureIdempotency)` só vale para o MESMO router e só para rota registrada DEPOIS dele.
    router_level = [(m.group(1), m.start()) for m in USE_RE.finditer(code)
                    if IDEM_IDENT_RE.search(ident[m.start():_span_end(code, m.end() - 1) + 1])]
    for m in WRITE_ROUTE_RE.finditer(code):
        abre = m.end() - 1
        fecha = _span_end(code, abre)
        if IDEM_IDENT_RE.search(ident[abre:fecha + 1]):
            continue
        receptor = _receptor(code, m.start())
        if receptor and any(nome == receptor and p < m.start() for nome, p in router_level):
            continue
        first, last = _line_of(code, m.start()), _line_of(code, fecha)
        motivo = _exempt_motive(raw, first, last)
        if motivo is not None and len(re.sub(r"\s", "", motivo)) >= EXEMPT_MIN:
            continue
        if motivo is not None:
            continue  # já acusado acima como marcador sem motivo
        out.append((first, f"rota `{m.group(1).upper()}` sem `ensureIdempotency` — toda escrita exige "
                           "`Idempotency-Key` (invariante 8). Isenção só com `// idempotency-exempt: "
                           "<motivo>` na linha de cima"))
    return sorted(set(out))


# ----------------------------------------------------------------------------- RN-14 segredos
PEM_RE = re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")
AWS_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")
SECRET_ASSIGN_RE = re.compile(
    r"(?i)\b\w*(secret|password|passwd|api_?key|token|private_?key|client_?secret|hmac)\w*"
    r"['\"]?\s*[:=]\s*(['\"`])([^'\"`\s]{16,})\2")


def _looks_like_secret(v: str) -> bool:
    """Literal de 16+ caracteres sem espaço que tem letra E dígito, e não é URL nem NOME de variável
    de ambiente (`BTG_CLIENT_SECRET`). Nome kebab (`x-idempotency-key`) raramente tem dígito; segredo
    real (hex, base64) quase sempre tem. ⚠️ Limite declarado: segredo só de letras passa."""
    if re.match(r"https?://", v):
        return False
    if "_" in v and re.fullmatch(r"[A-Z][A-Z0-9_]*", v):
        return False
    # nome de header / caminho de rota (`x-btg-signature-sha256`, `/auth/reset-token/v2`): segredo
    # real não é kebab minúsculo nem começa com `/` (achado BAIXA da 1ª auditoria)
    if v.startswith("/") or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", v):
        return False
    return bool(re.search(r"[A-Za-z]", v) and re.search(r"\d", v))


def secret_violations(ws_key: str, rel: str, text: str, ws_dir: Path | None = None) -> list[tuple[int, str]]:
    if not ws_key or not rel.startswith("src/") or not rel.endswith((".ts", ".tsx")):
        return []
    # TEXTO CRU, de propósito — ver o cabeçalho: segredo comentado é segredo vazado.
    code = text
    out = []
    for rx, nome in ((PEM_RE, "chave privada PEM"), (AWS_RE, "access key AWS"), (JWT_RE, "JWT")):
        for m in rx.finditer(code):
            out.append((_line_of(code, m.start()), f"{nome} literal no código (inclusive em comentário)"))
    for m in SECRET_ASSIGN_RE.finditer(code):
        if _looks_like_secret(m.group(3)):
            out.append((_line_of(code, m.start()),
                        f"literal atribuído a nome de segredo (`{m.group(1)}`) — segredo vem do cofre/env; "
                        "em teste, monte o valor em tempo de execução (`randomBytes(32).toString('hex')`)"))
    return sorted(set(out))


# ----------------------------------------------------------------------------- registro + CLI
RULES = {
    "money-bigint": ("RN-11", money_violations),
    "ledger-immutable": ("RN-12", immutable_violations),
    "idempotency-required": ("RN-13", idempotency_violations),
    "no-secret-in-code": ("RN-14", secret_violations),
}
TESTS = HARNESS / "scripts/tests"


def locate(path: str) -> tuple[str, str, Path | None]:
    """(ws_key, rel, ws_dir) de um caminho — real ou virtual."""
    ws_key = workspaces.which(path)
    if not ws_key:
        return "", "", None
    d = workspaces.which_dir(path)
    p = path.replace("\\", "/")
    rel = p[len(d):].lstrip("/") if p.startswith(d) else p.split(workspaces.load()[ws_key]["path"] + "/", 1)[-1]
    return ws_key, rel, Path(d)


def run_rule(name: str, path_as: str, text: str, ws_dir: Path | None = None) -> list[tuple[int, str]]:
    ws_key, rel, d = locate(path_as)
    return RULES[name][1](ws_key, rel, text, ws_dir if ws_dir is not None else d)


def _caso(base: Path, f: Path) -> str | None:
    """`acusa`/`limpo` pelo NOME do arquivo ou por um diretório-caso `<x>-acusa/` no topo — o 2º
    existe para arquivo cujo nome o escopo fixa (`routes/index.ts`)."""
    for part in (f.name,) + f.relative_to(base).parts[:1]:
        if "-acusa" in part:
            return "acusa"
        if "-limpo" in part:
            return "limpo"
    return None


def fixtures(name: str) -> list[Path]:
    base = TESTS / name
    return sorted(p for p in base.rglob("*") if p.is_file() and _caso(base, p))


MARK_RE = re.compile(r"@acusa(-abaixo)?\b")


def expected_lines(text: str) -> set[int]:
    """Linhas que a fixture `-acusa` DECLARA que têm de ser acusadas: comentário `@acusa` na própria
    linha, ou `@acusa-abaixo` na linha de cima (para linha que não aceita comentário, como o meio de
    um template literal). É o que transforma "acusou alguma coisa" em "acusou ISTO, AQUI"."""
    out = set()
    for n, line in enumerate(text.split("\n"), 1):
        for m in MARK_RE.finditer(line):
            out.add(n + 1 if m.group(1) else n)
    return out


def _self_test_once(name: str, rule) -> tuple[list[str], int, int, int]:
    base = TESTS / name
    falhas, n_acusa, n_limpo, n_linhas = [], 0, 0, 0
    for f in fixtures(name):
        virtual = "/" + str(f.relative_to(base))  # ex.: /backend/api/src/modules/ledger/...
        ws_key = workspaces.which(virtual)
        d = base / workspaces.which_dir(virtual).lstrip("/") if ws_key else None
        rel = virtual.split(workspaces.load()[ws_key]["path"] + "/", 1)[-1] if ws_key else ""
        text = f.read_text(encoding="utf-8")
        achados = rule(ws_key, rel, text, d)
        obtidas = {n for n, _ in achados}
        if _caso(base, f) == "acusa":
            n_acusa += 1
            esperadas = expected_lines(text)
            n_linhas += len(esperadas)
            if not esperadas:
                falhas.append(f"{f.relative_to(base)}: fixture -acusa sem marcador `@acusa` — não prova onde")
            elif obtidas != esperadas:
                falhas.append(f"{f.relative_to(base)}: linhas esperadas {sorted(esperadas)}, "
                              f"obtidas {sorted(obtidas)} {achados[:2]}")
        else:
            n_limpo += 1
            if achados:
                falhas.append(f"{f.relative_to(base)}: esperado limpo, obtido {achados[:2]}")
    return falhas, n_acusa, n_limpo, n_linhas


def self_test(name: str) -> int:
    """Cada `-acusa` tem de acusar EXATAMENTE as linhas marcadas; cada `-limpo`, nada. (A 1ª versão
    tinha uma sonda "regra desligada reprova" que era só `n_acusa > 0` com outro nome — achado MÉDIA
    da 1ª auditoria da spec 001; a conferência por linha a substitui.)"""
    rn, rule = RULES[name]
    falhas, n_acusa, n_limpo, n_linhas = _self_test_once(name, rule)
    if not n_acusa or not n_limpo:
        falhas.append(f"{name}: precisa de ao menos 1 caso -acusa e 1 -limpo (tem {n_acusa}/{n_limpo})")
    for f in falhas:
        print("  ❌ " + f)
    if falhas:
        print(f"❌ {name} --self-test REPROVADO ({len(falhas)} falha(s))")
        return 2
    print(f"✅ {name} ({rn}) --self-test: {n_acusa} caso(s) acusa com {n_linhas} linha(s) conferida(s), "
          f"{n_limpo} limpo")
    return 0


def cli(name: str, argv: list[str]) -> int:
    if argv[:1] == ["--self-test"]:
        return self_test(name)
    if not argv:
        print(f"uso: {name}.py <arquivo> [--as <caminho-virtual>] | --self-test", file=sys.stderr)
        return 64
    arquivo, path_as = argv[0], argv[0]
    if "--as" in argv:
        i = argv.index("--as")
        if i + 1 >= len(argv):
            return 64
        path_as = argv[i + 1]
    try:
        text = Path(arquivo).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    try:
        achados = run_rule(name, str(Path(path_as).resolve()) if not path_as.startswith("/") else path_as, text)
    except Exception as e:  # noqa: BLE001 — regra quebrada NÃO é achado (exit 1); é "não rodou"
        print(f"  {name}: a regra quebrou ({type(e).__name__}: {e}) — arquivo NÃO verificado", file=sys.stderr)
        return 3
    for n, msg in achados:
        print(f"  linha {n}: {msg}")
    return 1 if achados else 0
