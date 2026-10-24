# Spec: [Nome da Feature]

> **Camada 1 de 3 (SDD)** — esta spec descreve **O QUÊ** e **POR QUÊ**. Nada de "como".
> Design técnico vai em `plan.md`. Passos de execução vão em `tasks.md`.
> **Status**: `rascunho` | `aprovada`
> **Contexto de negócio**: [donors / customers / laboratories / storages / ...]
> **Data**: YYYY-MM-DD
> **Aprovada pelo usuário em**: [data ou "pendente"] ← gate humano obrigatório

---

## 1. Objetivo

[1-3 frases: o que esta feature entrega e por que existe, na linguagem do negócio.
Ex.: "Permitir o registro da análise de concentração espermática da coleta do doador,
com validação automática da diferença entre réplicas conforme tabela WHO/OMS."]

## 2. Contexto do domínio

[O que um desenvolvedor que não conhece clínica de fertilidade precisa saber para
entender esta feature. Referenciar docs: `documentacao/01-processo-doador`, etc.]

## 3. Regras de Negócio

> Apenas regras que a IA não conseguiria inferir do código existente:
> limites, fórmulas, validações de domínio, dependências entre campos, fluxos de estado.

- [RN-01] ...
- [RN-02] ...
- [RN-03] ...

## 4. Escopo

**Dentro do escopo:**
- ...

**Fora do escopo (explicitamente NÃO fazer):**
- ...

## 5. Dependências

- [Módulos/tabelas existentes dos quais esta feature depende]
- [Specs/tasks que precisam estar concluídas antes]

## 6. Critérios de Aceite

> Cada critério deve ser **verificável** (por teste, por inspeção de código ou pelo usuário na tela).
> Marcar a forma de verificação: `[auto]` (teste/lint/script) ou `[humano]` (validação na UI).

- [ ] [CA-01] ... `[auto]`
- [ ] [CA-02] ... `[auto]`
- [ ] [CA-03] ... `[humano]`

## 7. Questões em aberto

> Dúvidas que precisam de resposta do usuário ANTES de gerar o plan.
> O `/spec-plan` não roda enquanto houver questão aberta.

- [ ] ...
