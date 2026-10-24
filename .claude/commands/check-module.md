# Comando: /check-module

> **Título**: Auditar um módulo contra os padrões
> **Descrição**: roda a verificação **mecânica** do módulo e, sobre o resultado dela, faz a leitura
> que exige julgamento. Read-only: nunca edita, nunca roda migration, nunca commita.

## Uso

```
/check-module <workspace> <caminho-do-modulo> [--ref <modulo_molde>]
```

**Exemplos:**
- `/check-module backend src/modules/clinics/clinics`
- `/check-module frontend src/pages/clinics --ref carriers`

## Passo a passo

### 1. Mecânico primeiro — ele reprova sem julgamento

```bash
python3 .claude/scripts/check-module.py <workspace> <caminho> [--ref <molde>] [--contract]
```

**Qualquer achado ALTA = REPROVADO.** Não interprete, não relativize: marcador de bloco não
preenchido, placeholder vazado, arquivo que o scaffold geraria e não existe (AG-009), componente
que ninguém monta (FE-013), padrão proibido, import do visual v1 — todos passam em lint e
typecheck sem erro nenhum, e é por isso que existe este passo.

⚠️ **A lista de padrões proibidos vive no script, num lugar só** (spec 087). Este arquivo não a
repete: um checklist copiado aqui vira a terceira cópia manuscrita do padrão e desatualiza em
silêncio — foi o que aconteceu com a versão anterior deste comando, e é o que a `ui-v2` e a
`backend-module` já corrigiram do lado das skills.

⚠️ Passe `--ref` com o módulo que o plan mandou espelhar. Sem ele a checagem de vazamento (AG-002)
é **pulada**, e o resumo diz isso — não confunda "pulado" com "limpo".

### 2. Julgamento — o que o script não alcança

Leia a skill do workspace (`.claude/skills/backend-module/SKILL.md` ou `frontend-module/SKILL.md`,
mais `ui-v2` se for tela) e confira o que exige contexto:

- **Decisões** da skill: enum espelhado com travessia (BE-015), transação no repositório
  (BE-017/018), campo sensível no Create **e** no Update (BE-010), batch com metadados (AG-010),
  guarda de regra na camada certa (BE-028).
- **Nomenclatura**: tabela plural snake_case, FK `<plural>_id`, alias camelCase, permissão
  `<modulo>_<acao>` — **módulo novo `_update`, legado o sufixo que as rotas dele já têm**.
- **Regras por camada**: service sem acesso direto ao TypeORM, controller com no máximo 5 métodos,
  Joi inline na rota, `createQueryBuilder` no repositório.
- Se o módulo pertence a uma feature SDD, use o `verifier` em vez deste comando: ele cobre também
  a evidência do gate, a classificação do diff e a cobertura RN → código.

### 3. Relatório

Mesmo formato do `verifier`: veredito, violações (com `arquivo:linha` e a referência da lesson),
atenções, divergências de fonte.

## Regras

- **Read-only.** Este comando não corrige nada — nem o que for trivial.
- Achado sem `arquivo:linha` não é achado: é impressão.
- Ao afirmar escala ("N ocorrências"), valide o detector contra um caso conhecido antes (AG-020).
- Grep próprio filtra comentário (AG-013) — o do script já filtra.
