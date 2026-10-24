# Comando: /finish-task

> **Título**: Concluir Feature/Task em Andamento
> **Descrição**: Conduz o encerramento de uma feature (pasta SDD) ou task legada (TASK_*.md)
> que está em `.claude/specs/em_andamento/`: confere os gates, revisa os critérios de aceite,
> pede confirmação explícita do usuário e move para `.claude/specs/concluido/`.

## Uso

```
/finish-task [nome ou parte do nome da feature/arquivo]
/finish-task --lote <feature> <feature> …
```

Sem argumento: listar o que está em `em_andamento/` e perguntar qual concluir.

### `--lote` — agrupa o percurso, **não** a verificação (spec 089, RN-05)

Percorre a lista aplicando os **passos 1 a 6 inteiros** em cada feature, com **confirmação
explícita do usuário por feature**, e fecha com um resumo do lote.

⚠️ **São 1 a 6, não 1 a 5**: o passo 6 é a **colheita de lições**, e pulá-lo em 20 features
seguidas é perder exatamente o que a política de promoção do `lessons/README.md` existe para
capturar. O que o lote economiza é abrir e fechar o comando N vezes; o
gate humano continua sendo um "sim" para cada uma.

- **Uma confirmação única para o lote não existe** — seria o oposto do que o harness inteiro
  defende. Se o usuário pedir, explique e ofereça o percurso agrupado.
- **"Não" numa feature não interrompe o lote**: ela fica em `em_andamento/`, o motivo vai para o
  registro de execução dela, e o comando segue para a próxima.
- **Gate mecânico reprovado em uma feature** a tira do lote, com o motivo — sem perguntar ao
  usuário se ele quer concluir assim.
  ⚠️ O passo 2 manda **parar** quando um gate reprova. No `--lote`, "parar" é **parar naquela
  feature**, não abortar o lote: ela fica em `em_andamento/`, o motivo vai para o registro de
  execução dela, e o comando segue. Sem esta ressalva, quem executar "os passos inteiros" aborta o
  lote na primeira reprovada.
- Ao fim, um resumo: concluídas, recusadas pelo usuário (com o motivo), barradas pelo gate.

⚠️ **A lista do `--lote` é montada pelo usuário**, olhando a tabela do `/sprint-close`. O
`/sprint-close` **não** a propõe (RN-07): a categoria dele é heurística — já errou duas vezes ao
ser escrita — e um erro de classificação não pode virar proposta de fechar o que não devia.

## Passo a passo

1. **Localizar** em `.claude/specs/em_andamento/`:
   - Pasta de feature (formato SDD: `spec.md` + `plan.md` + `tasks.md`), ou
   - Arquivo legado `TASK_*.md` (fluxo antigo — usar o Checklist de Execução dele)
   - Se nada encontrado: informar e parar (não criar, não inventar).

2. **Conferir os GATES mecânicos** (formato SDD):
   - `tasks.md`: todas as tasks de execução marcadas `[x]`?
   - Gate `verify.sh`: **conferir a evidência** (spec 084), por workspace tocado:
     `bash .claude/scripts/verify.sh --check-evidence <feature> <ws>` — `<ws>` é a chave do
     `.claude/workspaces.json` (`backend`, `operador`, `cliente`, `simulator`), e `harness` se a
     feature mudou `.claude/`, `CLAUDE.md` ou `documentacao/` (spec 001).
     - exit 0 (`válida`): gate conferido sem reexecutar — ler `rc: 0` e `missing: []` no
       `.claude/gate/<feature>.<workspace>.json`.
     - exit 5 (hash igual, gate reprovado): a feature NÃO pode ser concluída — corrigir e rodar o gate.
     - exit 3 (`desatualizada`) ou 4 (`ausente`): **rodar agora**
       `bash .claude/scripts/verify.sh backend <modulo> --feature <feature>` e/ou
       `bash .claude/scripts/verify.sh <operador|cliente|harness> --feature <feature>` (exit code lido direto, nunca
       via `tail` — AG-012) e conferir de novo. Exit 65 = toolchain ausente: não é gate (AG-019).
   - Auditoria do subagente `verifier`: executada e aprovada? Se não, **executar agora**.
   - Qualquer gate reprovado → a feature NÃO pode ser concluída. Reportar o que falta e parar.

> ⚠️ **Formato da evidência a partir da spec 090**: `steps` é objeto (`.status`, mais `suites`/
> `tests` no jest), há `scopes` com os módulos que o gate pretendia cobrir, e o `rc` gravado é o
> **pior** de todas as rodadas do mesmo `diff_hash` — uma rodada verde **não** apaga uma vermelha.
> Se o JSON ainda tiver `steps` com strings, é de antes da 090: vale, mas não distingue rodadas.

3. **Conferir os critérios de aceite da spec**:
   - `[auto]`: verificar objetivamente no código (✅ / ⚠️ / ❌, com arquivo:linha quando aplicável)
   - `[humano]`: listar para o usuário validar na tela

4. **Pedir confirmação explícita ao usuário**:
   - Apresentar resumo: gates ✅, critérios `[auto]` ✅, critérios `[humano]` pendentes de confirmação
   - Perguntar: **"Você já validou esses pontos como usuário e confirma que a feature está concluída?"**
   - **Nunca mover sem essa confirmação.** Se faltar algo, manter em `em_andamento/` e anotar
     no "Registro de execução" do tasks.md o que falta.

5. **Mover**:
   - Após o "ok": mover a pasta (ou arquivo legado) de `em_andamento/` para `concluido/`
     (usar `git mv` se versionado, senão `mv`)
   - Marcar critérios confirmados como `[x]` na spec
   - Confirmar ao usuário o caminho final.

6. **Colheita de lições** (novo):
   - Revisar o "Registro de execução" do tasks.md: algum erro novo virou candidata a lesson?
   - Se sim, perguntar ao usuário se deseja registrar em `.claude/lessons/` — e avaliar se a
     lesson é **automatizável** (ver política de promoção em `.claude/lessons/README.md`).

## Regras críticas

- **Jamais mover para `concluido/` sem confirmação explícita do usuário** — e isso vale **por
  feature**, inclusive dentro do `--lote`.
- **Jamais concluir com gate mecânico reprovado** — não existe "concluir com pendência de lint/teste".
- Não gerar código novo aqui (apenas rodar verificações).
- Funciona a partir de qualquer workspace — caminhos de `.claude/specs/` sempre relativos à raiz do monorepo.
