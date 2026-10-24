#!/usr/bin/env python3
"""
block-shell-write-ts.py — recusa gravar .ts/.tsx por caminho que NÃO dispara o PostToolUse.

PreToolUse, matcher `Bash` (spec 090, RN-07/RN-08; lesson AG-025).

POR QUE ELE EXISTE, com número
------------------------------
O `PostToolUse` tem matcher `Edit|MultiEdit|Write`. Gravar o mesmo `.ts` por `sed -i`,
`cat > arquivo <<'EOF'` ou `tee` **não dispara hook nenhum**: nem o ESLint por arquivo, nem
BE-001, BE-007, BE-016, BE-023, FE-009, FE-023, FE-024, nem o `protect-migrations.sh`.

Isso não é risco teórico — é o passado deste repositório:

    ~700 de ~12.400 comandos (5–6%), alcançando ~950 arquivos .ts/.tsx distintos.
    Detector `d8e9624`, corpus de 14/09/2026, medido com o `cwd` de CADA comando.

Não são poeira espalhada — módulos inteiros nasceram pela porta de fora:
`donors_collections_preparations`, `donors_freezings`, `donors_confirmation_exams`,
`storage_movements`. Falso positivo: ~2% dos barrados = ~0,1% dos comandos.

⚠️ **O corpus NÃO é monotônico** — as transcrições são compactadas e rotacionadas. Entre 13 e
14/09 ele passou de 12.493 para 12.342 comandos e perdeu uma sessão. O número não é nem piso.

⚠️ **A CONDIÇÃO DE MEDIÇÃO IMPORTA MAIS QUE O DÍGITO, e este número já mudou cinco vezes:**

| medição | resultado | o que estava errado |
|---|---|---|
| detector solto, sem resolver caminho | 1.164 | contava todo alvo relativo que não fosse `/tmp` |
| detector real, `cwd` fixo na raiz | 232 | condição que vale para só 22% dos comandos |
| detector real, `cwd` de cada comando | 651 | ✅ a condição de execução |
| depois de `cp`/`mv`/`>|`/`cd --` | 723 | regra nova, não corpus |
| corpus de 14/09 | 714 | corpus encolheu |

**Para re-medir**, extraia os comandos Bash de `~/.claude/projects/<projeto>/*.jsonl` preservando o
`cwd` de cada entrada e aponte `avaliar(cmd, cwd)` para eles.

⚠️ **Se o número mudar, rode o DETECTOR ANTERIOR sobre o corpus ATUAL antes de culpar o corpus.**
Em 13/09 o salto 651→723 foi **96% regra nova e 4% corpus** — e a explicação "o corpus é vivo",
que eu havia escrito aqui, escondia exatamente o que precisava ser olhado: uma alternativa que
aumentou a superfície de bloqueio em 11% e trouxe 10 falsos positivos junto. Esta frase é o que
não envelhece; o dígito, sim.

Até aqui a defesa era **um parágrafo em três agentes**. Funcionou no piloto da F5 — os dois
builders desobedeceram à instrução de "modo automático" e reportaram —, mas funcionar por
obediência não é mecanismo, e aquela instrução chega a todo subagente, sempre.

OS LIMITES, DECLARADOS (plan §2.3) — esta regra REDUZ a rota, não a fecha
-------------------------------------------------------------------------
Nomeados de propósito: limite declarado não vira surpresa; limite escondido vira a próxima
auditoria. O que NÃO é detectado, com a medição de cada um no corpus:

- **`python -c` / `python3 - <<PY` com `open(..., 'w')`** — o principal. Casar exigiria
  interpretar Python dentro de uma string de shell, e o falso positivo custaria mais que o buraco.
- `dd of=`, `perl -i`, `xargs`, e variável com o prefixo do workspace (`W=backend/api;
  cat > $W/src/a.ts`) — **0** ocorrências.
- `cd` dentro de subshell `( … )` — **0**.
- **`cp`/`mv` de um `.ts` para um DIRETÓRIO** (`cp /tmp/x.ts ws/src/`): o alvo não termina em
  `.ts`. **0** ocorrências reais.
- **Tag de heredoc com hífen** (`<<'PY-EOF'`) ou escapada com barra invertida: o corpo volta a ser lido
  como comando. **0** — e o inventário mostra por quê: as tags usadas são `PY` 1678 ·
  `PYEOF` 1002 · `EOF` 786 · `TS` 231 · `TSX` 37 · `SQL` 19, **todas alfanuméricas puras**.
- **Corpo de `bash <<EOF` / `ssh host <<EOF`**, que é comando de verdade e será ignorado — 3 no
  corpus, nenhum gravando módulo.

⚠️ **Por que ficam de fora, e é decisão medida, não preguiça.** A alternativa `install` entrou por
plausibilidade — "é o jeito natural de instalar arquivo" — e deu **0 verdadeiros positivos e 10
falsos**, bloqueando justamente `npx --no-install eslint --fix`: a ferramenta que este hook existe
para garantir que rode. **Num hook que BLOQUEIA, falso positivo é trabalho que não anda**, não
ruído num relatório. Regra nova sem ocorrência medida é dívida de FP paga adiantado.

⚠️ **E os zeros acima dizem "ninguém fazia assim", não "ninguém fará":** o corpus é ANTERIOR a este
hook, então nenhum número medido nele mede contorno futuro.

Quem for barrado aqui e usar uma porta ao lado está fazendo uma **escolha**, não um descuido — e a
mensagem de bloqueio diz isso.

ESCOPO — o que o impede de parar o trabalho de harness
------------------------------------------------------
Só alvos `.ts`/`.tsx` que resolvem para dentro de um workspace de `.claude/workspaces.json`.
`/tmp`, scratchpad, `.claude/`, `.md`, `.py`, `.sh` ficam de fora, de propósito: esta própria
spec é escrita por heredoc em `.md` do harness.

Uso:
  block-shell-write-ts.py            # como hook: lê o JSON do PreToolUse no stdin
  block-shell-write-ts.py --self-test
"""
import json
import os
import re
import sys

# Os workspaces vêm de `.claude/workspaces.json` (spec 001) — a lista fixa que morava aqui era uma
# das sete cópias que já divergiam. Se o JSON estiver quebrado, o import falha alto: hook que
# libera tudo em silêncio por não saber onde estão os workspaces é pior que hook que dá erro.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
try:
    import workspaces  # noqa: E402
    WORKSPACES: tuple[str, ...] | None = tuple(v["path"].strip("/") + "/" for v in workspaces.load().values())
except Exception as _e:  # noqa: BLE001
    # JSON quebrado: FALHA FECHADA só para gravação de .ts/.tsx — todo alvo fora do /tmp e das
    # fixtures conta como workspace. Bloquear todo Bash impediria consertar o JSON; liberar tudo
    # seria o hook mudo (achado MÉDIA da 1ª auditoria da spec 001: o import quebrava com exit 1, que
    # num PreToolUse não bloqueia).
    sys.stderr.write(f"block-shell-write-ts: workspaces.json ilegível ({_e}) — tratando todo .ts como workspace\n")
    WORKSPACES = None

# Escape da RN-08: o scaffold grava .ts por script, legitimamente. A allowlist é por COMANDO e
# não por variável de ambiente — uma variável é escape que qualquer um liga para se livrar do
# bloqueio, e é assim que a regra morre. O passo seguinte ao scaffold continua sendo reabrir o
# gerado com Read/Edit: o escape é para a GERAÇÃO, não para o preenchimento.
# ⚠️ A allowlist casa o scaffold como COMANDO EXECUTADO, não como menção qualquer. A primeira
# versão era `\bscaffold\.py\b` sobre o comando inteiro, e `echo scaffold.py; cat > src/a.ts`
# desligava o hook para a linha toda — AG-013 aplicada à allowlist: mencionar a regra não pode
# valer como cumpri-la.
ALLOWLIST = (re.compile(r"(?:^|[\n;&|]|&&)\s*(?:\S*/)?python3?\s+\S*scaffold\.py\b"),)

# Três formas, e o alvo tem de ser .ts/.tsx.
#  - redirecionamento: `> x.ts`, `>> x.ts`  (NÃO casa `2>/dev/null`, nem `>` sem alvo .ts)
#  - sed no lugar: `sed -i … x.tsx`
#  - tee: `tee x.ts`
ESCRITA = re.compile(
    r">>?\|?\s*(?P<redir>[^\s|;&<>]+\.tsx?)\b"            # >  >>  >|
    r"|\bsed\b[^\n;|&]*?\s-[a-zA-Z]*i[a-zA-Z]*\b[^\n;|&]*?(?P<sed>[^\s|;&<>]+\.tsx?)\b"
    r"|\btee\b(?:\s+-[a-zA-Z]+)*\s+(?P<tee>[^\s|;&<>]+\.tsx?)\b"
    # `cp`/`mv`/`install`: o DESTINO é o último argumento. São as únicas formas da lista de burla
    # que são o jeito *natural* de fazer o que a regra proíbe — trazer do /tmp para o workspace —
    # e a superfície de falso positivo é pequena, porque copiar PARA o /tmp tem o alvo no /tmp.
    # ⚠️ Duas mudanças aqui, e **quem consertou o defeito foi o lookbehind**, não a remoção do
    # `install` — isolei as duas antes de escrever isto, porque meu primeiro comentário atribuía o
    # conserto à coisa errada:
    #
    #   `\b(?:cp|mv|install)\b`      → casa `npx --no-install eslint --fix src/x.tsx`  ⚠️
    #   `(?<![-\w])(?:cp|mv|install)` → não casa
    #
    # `-` é fronteira de palavra em regex, então `\binstall\b` casava dentro de `--no-install`, e o
    # corpus tem **173** deles. A regra bloqueava exatamente o `eslint --fix` que ela existe para
    # garantir que rode. O **lookbehind** fecha isso.
    #
    # `install` saiu por outra razão, menor: **zero** usos reais de `install(1)` no corpus — é
    # superfície de detecção sem benefício medido. Se um dia aparecer, volta com o lookbehind.
    r"|(?<![-\w])(?:cp|mv)\b(?:\s+-[a-zA-Z]+)*[^\n;|&]*?\s(?P<copia>[^\s|;&<>]+\.tsx?)\s*(?:$|[\n;|&])"
)


HEREDOC_ABRE = re.compile(r"<<-?\s*(['\"]?)(?P<tag>[A-Za-z_][A-Za-z0-9_]*)\1")


def sem_corpo_de_heredoc(cmd: str) -> str:
    """Remove o CONTEÚDO dos heredocs, preservando a linha que os abre.

    ⚠️ AG-013 na forma mais pura, e medida na prática: escrever *sobre* esta regra dispara esta
    regra. O hook bloqueou duas vezes a edição do próprio harness em dez minutos — uma ao reescrever
    este arquivo (cujos casos de teste contêm `cat >` seguido de um caminho `.ts`) e outra ao
    registrar o achado num `tasks.md`. O texto citado ia dentro de um heredoc de `python3 -`, e o
    detector o lia como comando.

    Remover só o CORPO não enfraquece a regra: a linha de abertura — onde mora o redirecionamento
    de verdade (`cat > x.ts <<'EOF'`) — continua sendo lida. O que sai é a prosa.
    """
    linhas = cmd.split("\n")
    out, pendentes, dentro = [], [], None
    for l in linhas:
        if dentro is not None:
            if l.strip() == dentro:
                dentro = None
            continue
        out.append(l)
        pendentes = [m.group("tag") for m in HEREDOC_ABRE.finditer(l)]
        if pendentes:
            dentro = pendentes[0]
    return "\n".join(out)


def alvos(cmd: str) -> list[str]:
    """Alvos .ts/.tsx que o comando GRAVA (não os que ele lê)."""
    out = []
    cmd = sem_corpo_de_heredoc(cmd)
    for m in ESCRITA.finditer(cmd):
        a = m.group("redir") or m.group("sed") or m.group("tee") or m.group("copia")
        if a:
            out.append(a)
    return out


def dentro_do_workspace(alvo: str, cwd: str) -> bool:
    """O alvo resolve para dentro de algum workspace do `workspaces.json`?

    Resolve relativo ao cwd porque `cd backend/api && cat > src/a.ts` é o caso real — o alvo
    escrito é `src/a.ts` e só o cwd revela de qual workspace ele é.
    """
    p = alvo if os.path.isabs(alvo) else os.path.normpath(os.path.join(cwd, alvo))
    p = p.replace(os.sep, "/")
    if "/tmp/" in p or p.startswith("/tmp"):
        return False
    # Mesma regra do `workspaces.which`: FIXTURE do harness nunca é de workspace — só ela.
    if "/.claude/scripts/tests/" in p + "/":
        return False
    if WORKSPACES is None:
        return True
    return any(w in p + "/" for w in WORKSPACES)


# `cd <dir> && <comando>` no começo da linha. É a FORMA DOMINANTE no histórico real deste
# projeto — o levantamento das transcrições mostra `cd .../donors_collections_preparations &&
# cat > repositories/IX.ts <<EOF` arquivo por arquivo. Sem tratar isso, o alvo escrito é
# `repositories/IX.ts` e o resolvedor o julga fora do workspace: o hook libera justamente o
# caso que mais ocorre. Foi o `--self-test` que pegou, antes de o detector ir para o ar.
_ASPAS = "'[^']*'|" + chr(34) + "[^" + chr(34) + "]*" + chr(34)
# ⚠️ TODO `cd`, em qualquer posição, e o separador inclui NEWLINE.
#
# A primeira versão exigia `&&` ou `;` e casava só na posição 0. A auditoria da T-17 achou, **no
# corpus real**, a forma que escapava:
#
#     cd /home/…/frontend/operador
#     cat > src/types/carriers.types.ts <<'TS'
#
# — 23 comandos do histórico nesse formato. E também escapavam `mkdir -p X && cd X && cat > a.ts`
# (o `cd` não é prefixo) e `cd backend && cd api && …` (encadeado). É a MESMA classe de defeito
# que o self-test celebrou ter pego com `&&`, com outro separador: o teste tinha caso para `&&` e
# para `;`, nenhum para newline.
#
# Aplicar TODOS os `cd` em ordem também conserta o falso positivo simétrico:
# `cd backend/api && cd /tmp && cat > a.ts` antes barrava, porque só o primeiro era lido.
CD_QUALQUER = re.compile(r"(?:^|[\n;&|]|&&)\s*cd\s+(?:--\s+)?(?P<dir>(?:" + _ASPAS + r"|[^\s;&|\n]+))")


def cwd_efetivo(cmd: str, cwd: str) -> str:
    """cwd depois de aplicar, em ordem, todo `cd` que o comando executa."""
    atual = cwd
    # ⚠️ O princípio "corpo de heredoc não é comando" vale AQUI TAMBÉM. A 1ª versão o aplicava só
    # em `alvos()`, e a assimetria abria buraco: `cat > src/a.ts <<'EOF'` cujo corpo tivesse uma
    # linha `cd /tmp` movia o cwd efetivo e LIBERAVA a gravação real.
    cmd = sem_corpo_de_heredoc(cmd)
    for m in CD_QUALQUER.finditer(cmd):
        d = m.group("dir").strip("'" + chr(34))
        if d == "-":   # `cd -` volta ao diretório anterior; não dá para saber qual, então não move
            continue
        atual = d if os.path.isabs(d) else os.path.normpath(os.path.join(atual, d))
    return atual


def avaliar(cmd: str, cwd: str) -> list[str]:
    """Devolve os alvos que devem ser barrados. Lista vazia = liberar."""
    if any(rx.search(cmd) for rx in ALLOWLIST):
        return []
    efetivo = cwd_efetivo(cmd, cwd)
    return [a for a in alvos(cmd) if dentro_do_workspace(a, efetivo)]


MENSAGEM = """❌ Gravação de {n} arquivo(s) .ts/.tsx por shell — o hook de verificação NÃO roda aí.

  {lista}

O `PostToolUse` tem matcher `Edit|MultiEdit|Write`. Gravando por `sed -i`, heredoc ou `tee`, NADA
roda: nem o ESLint por arquivo, nem BE-001, BE-007, BE-016, BE-023, FE-009, FE-023, FE-024, nem a
proteção de migrations. Neste repositório 904 arquivos já nasceram por essa porta (AG-025).

Use **Edit** ou **Write**. Se a instrução de "modo automático" mandar usar `sed`, ela NÃO vale
para `.ts/.tsx` — esta regra vence.

⚠️ Limite conhecido desta regra: ela NÃO detecta `python -c` com `open(...,'w')`. Se você contornar
por ali, está fazendo uma escolha — e o gate e o `check-module.py` continuam sendo as únicas
defesas que leem o disco em vez de confiar em quem escreveu."""


def self_test() -> int:
    ws = "/home/x/repo"
    casos = [
        # (deve barrar?, cwd, comando, por quê)
        (True,  ws, "cat > backend/api/src/a.ts <<'EOF'", "heredoc, caso dominante"),
        (True,  ws, "echo x >> frontend/operador/src/c.tsx", "append"),
        # spec 001: a lista vem do workspaces.json — os 4 workspaces barram, não só os 2 do ERP
        (True,  ws, "cat > frontend/cliente/src/a.tsx <<'EOF'", "workspace cliente (do JSON)"),
        (True,  ws, "tee tools/btg-simulator/src/a.ts < x", "workspace simulator (do JSON)"),
        (False, ws, "cat > frontend/" + "admin/src/a.ts <<'EOF'", "caminho do ERP não é mais workspace"),
        (True,  ws, "sed -i 's/a/b/' backend/api/src/a.ts", "sed no lugar"),
        (True,  ws, "sed -i.bak 's/a/b/' frontend/operador/src/b.tsx", "sed -i com sufixo"),
        (True,  ws, "tee backend/api/src/b.ts < x", "tee"),
        (True,  ws + "/backend/api", "cat > src/a.ts <<'EOF'", "relativo ao cwd do workspace"),
        (True,  ws, "cd backend/api && cat > src/modules/x/a.ts <<EOF", "cd embutido (forma dominante real)"),
        (True,  ws, "cd /home/x/repo/frontend/operador && sed -i 's/a/b/' src/p.tsx", "cd absoluto"),
        (True,  ws, "cd 'backend/api' ; tee src/y.ts < z", "cd com aspas e ;"),
        (False, ws, "cd documentacao && cat > x.ts <<EOF", "cd para fora do workspace"),
        (True,  ws, "cd backend/api\ncat > src/types/x.types.ts <<'TS'", "cd + NEWLINE (achado no corpus)"),
        (True,  ws, "mkdir -p X && cd backend/api && cat > src/a.ts <<EOF", "cd fora da posição 0"),
        (True,  ws, "cd backend && cd api && cat > src/a.ts <<EOF", "cd encadeado"),
        (False, ws, "cd backend/api && cd /tmp && cat > a.ts <<EOF", "último cd manda: /tmp libera"),
        # ⚠️ Este caso tinha alvo em `/tmp` e não provava nada: o guard de `/tmp` já o liberava,
        # com ou sem allowlist. O alvo TEM de estar no workspace para o caso reprovar se a
        # allowlist voltar a casar por menção. Achado da reauditoria da T-17.
        (True,  ws, "echo scaffold.py; cat > backend/api/src/zz.ts <<'EOF'",
         "menção a scaffold NÃO é allowlist (alvo NO workspace)"),
        (True,  ws, "cd -- backend/api && cat > src/zz.ts <<EOF", "cd -- consome o token seguinte"),
        (True,  ws, "cp /tmp/x.ts backend/api/src/zz.ts", "cp trazendo do /tmp para o workspace"),
        (True,  ws, "mv /tmp/x.tsx frontend/operador/src/zz.tsx", "mv"),
        (False, ws, "cp backend/api/src/a.ts /tmp/x.ts", "cp PARA o /tmp libera"),
        (True,  ws, "cat >| backend/api/src/zz.ts <<EOF", ">| (noclobber)"),
        # ⚠️ Escrever SOBRE a regra não pode disparar a regra (AG-013). Medido na prática: o hook
        # bloqueou duas vezes a edição do próprio harness em dez minutos, porque o texto citado
        # ia dentro de um heredoc. A linha que ABRE o heredoc continua sendo lida — só o corpo sai.
        (False, ws, "python3 - <<'PY'\ns = \"cat > backend/api/src/a.ts\"\nPY",
         "citação dentro de CORPO de heredoc não é comando"),
        (True,  ws, "cat > backend/api/src/zz.ts <<'EOF'\nconst a = 1\nEOF",
         "…mas a linha que ABRE o heredoc continua sendo lida"),
        # ---- não-casos: LEITURA ----
        (False, ws, "grep -n 'foo' backend/api/src/a.ts", "leitura"),
        (False, ws, "cat backend/api/src/a.ts", "leitura"),
        (False, ws, "wc -l backend/api/src/a.tsx", "leitura"),
        (False, ws, "ls backend/api/src/*.ts", "listagem"),
        (False, ws, "yarn jest src/modules/x/tests", "teste"),
        (False, ws, "git diff -- backend/api/src/a.ts", "diff"),
        (False, ws, "sed -n '5,9p' backend/api/src/a.ts", "sed SEM -i é leitura"),
        (False, ws, "python3 -m py_compile x.py 2>/dev/null", "2>/dev/null não é alvo .ts"),
        # ---- não-casos: FORA DO ESCOPO ----
        (False, ws, "cat > /tmp/x/a.ts <<'EOF'", "/tmp não é workspace"),
        (False, ws, "cat > .claude/scripts/x.ts <<'EOF'", ".claude/ não é workspace"),
        (False, ws, "cat > .claude/scripts/tests/h/backend/api/src/a.ts <<'EOF'",
         "fixture com caminho de workspace DENTRO de .claude/scripts/tests/ não é workspace"),
        (True,  ws, "cat > .claude/worktrees/w1/backend/api/src/a.ts <<'EOF'",
         "worktree dentro de .claude/ CONTINUA sendo workspace"),
        (False, ws, "cat > documentacao/HARNESS.md <<'EOF'", ".md não é alvo"),
        (False, ws, "python3 - <<'PY' > .claude/hooks/x.py", ".py não é alvo"),
        (False, ws, "cat > backend/api/README.md <<'EOF'", ".md dentro do workspace"),
        # ---- escape da RN-08 ----
        (False, ws, "python3 .claude/scaffold/scaffold.py backend donors x X", "scaffold"),
        (False, ws, "python3 .claude/scaffold/scaffold.py --self-test", "scaffold --self-test"),
        # ---- limite declarado: NÃO detecta, e o teste registra isso ----
        (False, ws, "python3 -c \"open('backend/api/src/a.ts','w').write('x')\"",
         "LIMITE DECLARADO: python -c não é detectado (plan §2.3)"),
    ]
    falhas = 0
    print("block-shell-write-ts --self-test\n")
    for esperado, cwd, cmd, porque in casos:
        barrou = bool(avaliar(cmd, cwd))
        ok = barrou == esperado
        marca = "✅" if ok else "❌"
        rot = "barra " if barrou else "libera"
        if not ok:
            falhas += 1
        print(f"  {marca} {rot}  {cmd[:56]:58} {porque}")
    print()
    if falhas:
        print(f"❌ {falhas} falha(s)")
        return 1
    print("✅ self-test aprovado — casos conhecidos barram, não-casos liberam,")
    print("   escape do scaffold funciona, e o limite do `python -c` está registrado como caso.")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # entrada ilegível não é motivo para barrar trabalho
    ti = payload.get("tool_input") or {}
    cmd = ti.get("command")
    if not isinstance(cmd, str) or not cmd:
        return 0
    cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    barrados = avaliar(cmd, cwd)
    if not barrados:
        return 0
    sys.stderr.write(MENSAGEM.format(n=len(barrados), lista="\n  ".join(barrados)) + "\n")
    return 2  # 2 = bloqueia e devolve o stderr ao agente


if __name__ == "__main__":
    sys.exit(main())
