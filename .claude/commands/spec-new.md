# Comando: /spec-new

> **Título**: Criar Spec de Feature (Camada 1 — SDD)
> **Descrição**: Conduz uma entrevista curta com o usuário e gera APENAS o `spec.md` de uma
> nova feature em `.claude/specs/a_fazer/<feature>/`. Não gera plan, não gera tasks, não gera código.

## Uso

```
/spec-new <nome-da-feature>
```

Exemplo: `/spec-new donor-collection-vitality`

## Passo a passo

1. **Coletar o "o quê"** — perguntar ao usuário (apenas o que não estiver claro):
   - Objetivo de negócio (1-3 frases)
   - Regras de negócio (fórmulas, limites, validações de domínio, fluxos de estado)
   - O que está explicitamente fora do escopo
   - Dependências (módulos existentes, outras specs)
   - Como o usuário vai validar que está pronto (vira critério de aceite `[humano]`)

2. **Consultar contexto existente**:
   - `documentacao/` (processo do doador, mapas de dados, workflows)
   - Módulos similares já implementados (apenas para entender o domínio — design fica para o plan)

3. **Gerar o arquivo** usando `.claude/specs/_templates/spec.md`:
   - Criar `.claude/specs/a_fazer/<feature>/spec.md`
   - Status inicial: `rascunho`
   - Critérios de aceite: todos verificáveis, marcados `[auto]` ou `[humano]`
   - Dúvidas não resolvidas vão para "Questões em aberto"

4. **Apresentar ao usuário para revisão** e perguntar explicitamente:
   **"A spec está correta e completa? Posso marcá-la como aprovada?"**
   - Só marcar `Status: aprovada` + data após o "sim" do usuário.

## Regras críticas

- **NUNCA** incluir design técnico na spec (tabelas, services, endpoints, componentes) — isso é o `/spec-plan`.
- **NUNCA** gerar código neste comando.
- Spec com "Questões em aberto" não pode ser aprovada.
- Regras de negócio devem ter ID (`RN-01`, `RN-02`...) — o plan vai mapear cada uma.
