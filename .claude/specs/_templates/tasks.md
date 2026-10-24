# Tasks: [Nome da Feature]

> **Camada 3 de 3 (SDD)** — passos de execução derivados de `plan.md`.
> Tasks são **descartáveis e regeneráveis**: se o plan mudar, regenerar este arquivo.
> **Plan de origem**: `./plan.md` (status deve ser `aprovado`)
>
> **Regras de execução:**
> 1. Executar na ordem. Marcar `[x]` IMEDIATAMENTE ao concluir cada task — nunca em lote no final.
> 2. Cada task termina com sua verificação passando. Task sem verificação aprovada = task não concluída.
> 3. Se pausar/retomar (mesma sessão ou outra): ler este arquivo primeiro e NÃO refazer o que está `[x]`.
> 4. O gate final (`verify.sh`) é obrigatório antes de mover a feature para `concluido`.

---

## Fase 1 — Backend

- [ ] **T-01** Migration `CreateTable<...>` criada e executada
  - Verificação: `yarn migration:show` lista a migration como executada
- [ ] **T-02** Enums + Entity com auditoria
  - Verificação: hook pós-edição passou (ESLint + lessons)
- [ ] **T-03** DTOs (`ICreate`, `IUpdate`, `IFind`)
  - Verificação: hook pós-edição passou
- [ ] **T-04** Repository (interface + implementação) + Provider registrado no IoC
  - Verificação: import em `src/shared/container/providers/index.ts` confirmado via grep
- [ ] **T-05** Services (Create, Update, Show, List, ListTotal, Delete + extras do plan)
  - Verificação: hook pós-edição passou em cada arquivo
- [ ] **T-06** Controller + Routes (Joi inline + accessControl) + registro em `routes/index.ts`
  - Verificação: grep confirma rota registrada APÓS `ensureAuthenticated` (ou antes, se webhook — AG-006)
- [ ] **T-07** Testes unitários (um `.spec.ts` por service)
  - Verificação: `yarn test src/modules/<contexto>/<modulo>` ✅
- [ ] **T-08** `find src/modules/<contexto>/<modulo> -type f | sort` — todos os arquivos esperados existem (AG-009)

## Fase 2 — Frontend

- [ ] **T-09** Types + Service HTTP + Constants
  - Verificação: hook pós-edição passou
- [ ] **T-10** Páginas (List / Form / abas) conforme plan
  - Verificação: hook pós-edição passou
- [ ] **T-11** Integração (rotas, menu, tab, providers no App.tsx)
  - Verificação: grep confirma registro
- [ ] **T-12** `grep -r "<modulo_de_referencia>" <pasta_do_novo_modulo>` retorna vazio (AG-002/FE-003)

### ⚠️ Obrigatória quando a feature REMOVE algo (AG-017)

> Só incluir se a feature remove um mecanismo, campo, botão, valor de enum, prop, método ou
> comportamento. Se nada é removido, apagar este bloco ao gerar o `tasks.md`.

- [ ] **T-RM** Conferir a remoção por **grep do termo VELHO**, no workspace inteiro — nunca do
      termo que entrou no lugar. Grep do texto novo confirma presença, jamais ausência.
      Conferir as duas pontas da cascata: quem **consumia** o que saiu, e quem **produzia** algo
      que só existia para alimentá-lo (campo de retorno de hook, state, acumulador, constante).
      Ler cada hit com AG-013: menção dentro de comentário que **explica a remoção** é legítima;
      comentário que afirma o mecanismo como **vigente** é defeito.
      **Verificação**: `grep -rniE "<termo1>|<termo2>" <workspace>/src` — cada ocorrência
      classificada como (a) código legítimo de outra feature, (b) comentário histórico honesto, ou
      (c) defeito a corrigir. Nenhuma na categoria (c).

---

## Fase 3 — Gate de conclusão

- [ ] **T-13** Permissões cadastradas (manual via tela — confirmar com usuário): módulo novo = `<tabela>_view/create/update/delete`; módulo legado = o sufixo que as rotas dele já têm (`_edit` na maioria) — nunca inventar (spec 085, RN-10)
- [ ] **T-14** **GATE**: `bash .claude/scripts/verify.sh backend src/modules/<contexto>/<modulo> --feature <nome-da-feature>` ✅
      (gera `.claude/gate/<feature>.backend.json` — é o que o `verifier` e o `/finish-task` conferem; exit code lido direto, AG-012)
- [ ] **T-15** **GATE**: `bash .claude/scripts/verify.sh frontend --feature <nome-da-feature>` ✅
- [ ] **T-16** Subagente `verifier` rodou auditoria (/check-module + diff) e aprovou
- [ ] **T-17** Critérios de aceite `[humano]` da spec validados pelo usuário (via `/finish-task`)

---

## Registro de execução

> Anotar aqui desvios do plan, erros encontrados e lições candidatas a `.claude/lessons/`.

| Data | Task | Observação |
|------|------|------------|
| | | |
