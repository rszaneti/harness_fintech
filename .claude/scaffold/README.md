# `.claude/scaffold/` — geração determinística de módulos (spec 085)

Substitui a cópia manual dos templates: o script deriva os placeholders de identidade, substitui do
mais longo para o mais curto, formata com o Prettier do workspace e **falha se sobrar placeholder**
fora da lista fechada de marcadores de bloco. O agente faz três coisas: rodar o scaffold, preencher
os blocos, rodar o gate.

## Uso

```bash
python3 .claude/scaffold/scaffold.py backend  <contexto> <modulo> <Entity> [--plural E] [--tabela t] [--endpoint e] [--enum Tipo] [--no-table] [--sem-migration] [--append-only] [--timestamp ms] [--dry-run]
python3 .claude/scaffold/scaffold.py frontend <contexto> <modulo> <Modulo> --ws <operador|cliente> --label "Rótulo" [--label-plural "Rótulos"] [--plural M] [--endpoint e] [--filho Filho --filho-label "Rótulo"] [--constants] [--dry-run]
python3 .claude/scaffold/scaffold.py migration create <Tabela> [--timestamp ms]
python3 .claude/scaffold/scaffold.py migration alter  <Tabela> --mudanca <PascalCase> [--coluna c] [--ref tabela] [--timestamp ms]
python3 .claude/scaffold/scaffold.py --list-placeholders
python3 .claude/scaffold/scaffold.py --self-test [backend|frontend|static]
```

**`--append-only`** (spec 001): perfil para registro que nunca muda nem some — Create/Show/List/ListTotal,
controller de 3 métodos, repositório que insere (nunca `save`), migration com a trigger
`reject_mutation()`. Obrigatório para os módulos de `financial_rules.APPEND_ONLY_MODULES` (o scaffold
recusa sem a flag, exit 64). **`--self-test static`**: todas as variações num diretório temporário,
sem workspace — é a prova que existe antes de haver `backend/api` (roda no `verify.sh harness`).
Workspaces vêm de `.claude/workspaces.json`; `frontend` exige `--ws`.

Exemplos: `backend charges charges Charge --enum Status` · `backend ledger ledger_entries LedgerEntry --plural LedgerEntries --append-only` ·
`frontend charges charge Charge --ws operador --label Cobrança --constants`.

## O que sai

- Lista dos arquivos criados e, para cada **marcador de bloco** que ficou, `arquivo:linha marcador`
  — é a lista de trabalho do agente.
- O scaffold **nunca sobrescreve** (exit 3). `migration create` para tabela que já tem
  `CreateTable<Tabela>` → exit 4.
- Um módulo recém-gerado, com os blocos ainda vazios, **compila, passa lint e testes** — cada
  marcador tem um exemplo declarado (`name`/`status`) para multiplicar e ajustar, não para deixar.

## Placeholders

**Identidade** (derivados dos argumentos — ver as tabelas em `skills/backend-module/SKILL.md` e
`skills/frontend-module/SKILL.md`). **Blocos — lista fechada**:
`__CAMPOS__ __FILTROS__ __COLUNAS__ __REGRAS__ __TESTES_DE_ERRO__ __WHERES__ __FKS__ __VALORES__
__IMPORTS_RELACIONAMENTOS__ __ATRIBUICOES__ __CAMPOS_FILHO__`. Qualquer outro `__X__` num template
→ exit 2 com arquivo e linha. `--list-placeholders` é a auditoria: template novo com placeholder
novo quebra o scaffold até ser declarado em `scaffold.py`.

Concatenações (`__permissao___view`, `__tabela___id`, `CreateTable__Entities____timestamp__`)
resolvem porque a substituição vai do placeholder mais longo para o mais curto e o resto é literal.

## Diretivas de template

Linha inteira, removida na saída: `// @if filho` … `// @endif` (também `constants`, `enum`, e a
negação `// @if !filho`). Servem para trechos que só existem com aba filha etc.

## `--self-test`

Gera os dois módulos **dentro do workspace** (`src/modules/zz_scaffold/…`, `src/pages/zz_scaffold/…`
— é a única forma de o `tsc` resolver `@modules/*` e os imports relativos), roda `tsc --noEmit`,
`eslint` nos gerados (e `jest` no backend), confere as invariantes e **apaga tudo no `finally`**,
exigindo que o `git status` do fim seja igual ao do início. Invariantes: nenhum placeholder de
identidade; nome de arquivo sem `__`; nenhum import v1 (`styles/global`, `styles/globalMaterialUi`);
todo `Css*`/componente importado consta dos exports de `globalMaterialUi_v2.tsx`/`global_v2.tsx`;
nada de Clínicas vazou para o gerado; sem `slots={{ backdrop }}` (FE-024). As checagens olham o
**código**, não os comentários (AG-013).

Rode com `pgrep -f "bin/(eslint|tsc|jest)"` vazio (AG-021).

## Exit codes

`0` ok · `1` prettier falhou (o gerado é removido, nada fica no workspace) · `2` placeholder ou
diretiva desconhecidos, ou template fora da tabela de destinos (morto) · `3` destino já existe ·
`4` migration duplicada · `5` self-test reprovado · `64` uso.

## Templates

`templates/backend/` (24) e `templates/frontend/` (9, v2 — modelados em `pages/clinics/`). As tabelas
de destino vivem em `BACKEND_DEST`/`FRONTEND_DEST` no script; as skills mantêm uma cópia de leitura.
