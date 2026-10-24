# Comando: /sprint-close

> **Título**: Fechar a sprint — o "olhar para o todo", sob comando do usuário
> **Descrição**: Gate `--full` nos dois workspaces, contrato cruzado desde a base do ciclo, e a
> medição do que falta em cada feature de `em_andamento/`. Escreve o relatório da sprint.
> **Spec**: 089 (F6)

## Uso

```
/sprint-close [--since-backend <ref>] [--since-frontend <ref>]
```

⚠️ **Não existe `--since` único.** São dois repositórios, com hashes distintos — um ref só seria
inválido em um deles. A interface é por workspace de propósito: a proibição não pode depender de o
leitor chegar ao passo 1.

## O que este comando NÃO faz

- **Não move feature nenhuma** para `concluido/` (RN-06). Quem conclui é `/finish-task`.
- **Não propõe lote** (RN-07). A lista do `--lote` é montada pelo usuário, olhando a tabela — um
  erro de classificação não pode virar proposta de fechar o que não devia.
- **Não corrige nada.** Vermelho achado aqui vira task na feature de quem é.

## Antes de começar — avise o usuário

⚠️ O `--full` do backend levou **1291 s (21,5 min)** na primeira execução real de 13/09/2026 — 766
suítes, 3.970 testes. (A spec 084 mediu 624 s; a diferença é árvore maior e cache frio.) Diga o
tempo esperado e pergunte se é hora.

⚠️ **Não cabe numa chamada bloqueante de 600 s**, e a saída tentadora — `&` — é proibida pela
**AG-021**. Rode em primeiro plano e deixe estourar o limite da ferramenta: o processo continua e
termina. **E leia o `rc` do JSON de evidência**, nunca de notificação de processo nem do
encadeamento:

```bash
python3 -c "import json;d=json.load(open('.claude/gate/sprint-<data>.backend.json'));print(d['mode'],d['rc'])"
```

Isto não é teoria: na execução de 13/09 o processo foi para segundo plano e a notificação disse
**"exit code 0"** — o gate real era **`rc=1`**. O zero era do último comando do wrapper. É a
**AG-012** no lugar mais caro possível, o fechamento de sprint. Rode em **primeiro plano** (AG-021: em background não é gate) e
confira `pgrep -f "bin/(eslint|tsc|jest)"` **vazio** antes — com outra sessão lintando, o lint do
backend foi de 74 s para 314 s (medido na 084).

## Passo a passo

### 1. Descobrir a base do ciclo — **por workspace**

```bash
# um por workspace de .claude/workspaces.json que EXISTE no checkout
for w in $(python3 .claude/scripts/workspaces.py --list); do
  d=$(python3 .claude/scripts/workspaces.py --path "$w"); [ -d "$d" ] || continue
  echo "$w: $(git -C "$d" log --merges -1 --format='%h %ad %s' --date=short)"
done
```

**Declare o que achou** (hash, data, assunto) antes de usar. `--since-backend` /
`--since-frontend` sobrepõem, **cada um o seu**.

Para ler o `mode` da evidência sem `cat | grep` (AG-012 vale para leitura também):
```bash
python3 -c "import json;d=json.load(open('.claude/gate/<feature>.<ws>.json'));print(d['mode'],d['rc'])"
```

⚠️ **Nunca um `--since` único para os dois.** São repositórios distintos, com hashes distintos
(hoje `7e0faf0` e `95a729c`). Um ref só seria inválido em um deles.

⚠️ **Não se cria tag `sprint/<data>`** (decisão do usuário, 13/09/2026): a fronteira já existe como
o merge do ciclo anterior. E **não detecte pelo nome da branch** — a convenção já teve quatro
grafias (`UPDATE-`, `UPDATE_`, `SCRUM_`, data pura), e um `--grep="UPDATE"` perderia três merges
reais do frontend do ERP de origem. O último merge, sem grep, acerta todos.

### 2. Gate `--full` nos dois workspaces

```bash
bash .claude/scripts/verify.sh backend  --full --feature sprint-<AAAA-MM-DD>
bash .claude/scripts/verify.sh frontend --full --feature sprint-<AAAA-MM-DD>
bash .claude/scripts/verify.sh harness  --full --feature sprint-<AAAA-MM-DD>   # spec 001: o harness também fecha a sprint
```

**Exija `"mode": "full"`** na evidência de cada um antes de aceitá-la como cobertura de sprint — o
campo já existe no JSON (spec 084). Evidência em `"mode": "scope"` não serve aqui.

⚠️ **A evidência é sobrescrita entre rodadas do mesmo workspace** (dívida da **spec 090**): se você
rodar mais de uma vez, o JSON guarda só a última. Enquanto a 090 não fechar, **declare no relatório
todas as rodadas**, com escopo e `rc` de cada — não afirme cobertura que o arquivo não prova.

⚠️ **O `--full` mede a ÁRVORE DE TRABALHO, não o último commit** — inclusive arquivos
**untracked**, cujo conteúdo entra no `diff_hash`. Um vermelho de trabalho não commitado aparece
como vermelho da sprint. Três coisas a registrar no relatório, para a declaração ser **conferível**
e não só honesta:

1. **O que está na árvore**, nominalmente — `git -C <ws> status --short -uall`. Em especial:
   `tsconfig.json` alterado durante um gate é o tipo de coisa que envenena a leitura do verde um mês
   depois. Diga **o que** mudou nele. (Hoje é o `incremental` + `tsBuildInfoFile` da spec 084 —
   conferido: não estreita o typecheck.)
2. **Os untracked contam.** Arquivos novos em `src/` entram no hash e são medidos. A §3 do template
   ("de quem é cada vermelho") existe para isso — use-a.
3. **O `diff_hash` e a contagem do instante**: grave o hash de cada workspace ao lado do `rc`, mais
   `git -C <ws> status --porcelain | wc -l`. Sem o hash, "o gate rodou sobre a árvore de então" é
   frase que ninguém confere depois; com ele, o `--check-evidence` refaz a conta.

⚠️ **Passando pasta como argumento, termine com `/`** — o argumento vira `jest <pattern>` e o
pattern é **regex de caminho** (lesson AG-026): sem a barra, `src/modules/donors/donors` casa 282
suítes em vez de 12.

### 3. Contrato cruzado desde a base

```bash
python3 .claude/scripts/check-module.py backend --since <base backend> --contract
```

⚠️ **Uma vez só.** O próprio script imprime: *"`--contract` compara backend × frontend e NÃO
depende do workspace do argumento — rodar uma vez basta"*. Rodar os dois lados devolve os mesmos
achados, e a §4 do template nasceria com a contagem dobrada.

É o que a auditoria por feature **não** enxerga: dois módulos alterando a mesma resposta em
features diferentes do mesmo ciclo.

### 4. Medir o que falta

```bash
bash .claude/scripts/sprint-status.sh
```

⚠️ A categoria é **heurística de palavra e erra** — ela já errou duas vezes ao ser escrita, e a
segunda só apareceu porque alguém conferiu quatro features à mão. Leia a linha `↳` com o texto da
task antes de agir sobre a categoria. Divergência é achado sobre o script, não sobre a feature.

### 5. Escrever o relatório

`.claude/sprints/<AAAA-MM-DD>.md`, a partir de `.claude/sprints/_template.md`.

**A primeira seção — "O que ficou aberto, e por quê" — é escrita pelo usuário, não por você.** O
`git log` conta o que foi feito; só ela conta por que o resto não foi (RN-04). Preencha as demais
seções com o que mediu e **deixe a primeira com as perguntas**, para ele responder.

## O que o relatório precisa declarar que NÃO sabe

Três coisas, sempre, enquanto as dívidas existirem:

| Não sabe | Por quê |
|---|---|
| se houve mais de uma rodada de gate | a evidência é sobrescrita (spec **090**) |
| se o `--full` cobre o harness | não cobre: `verify.sh` não lê `.py`/`.sh`/`.md` (spec **087**) |
| se a classificação está certa | é heurística; por isso o texto da task vai junto |

E **de quem é cada vermelho**. Hoje há um conhecido: `donorDonatableAvailability.spec.ts`, obsoleto
desde a spec **074**. Sem dizer de quem é, o relatório nasce vermelho e ninguém sabe por quê.

## Regras críticas

- Primeiro plano, sempre. Exit code lido do script, nunca de um pipe (AG-012, AG-021).
- Nada se move. Nenhum lote é proposto.
- Gate vermelho por problema alheio à sprint: **reporte**, não contorne (regra crítica 7).
