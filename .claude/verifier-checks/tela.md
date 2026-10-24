# check `tela` — tela nova ou alterada [spec 086, FE-013, FE-016, FE-024]

> Acende quando o diff toca `.tsx` em `pages/` ou `components/`.
> Rode `check-module.py <operador|cliente> --diff` (v1-import, órfão, proibidos) — é ele que lê o `.tsx`.
> O `check-ui-v2-refs.py` mede **documentação**, não tela: ele só coleta `.md`, e sem argumento
> audita as skills; aponte-o para o **recorte da §3.4** do plan
> (`awk '/^### 3\.4 Telas/{f=1} /^### 3\.5|^## 4\./{f=0} f' plan.md > /tmp/telas.md` e então o script sobre
> `/tmp/telas.md`) — o plan inteiro dá falso positivo em `GET`, `POST`, `Edit`. No código quem cobre é o
> `tsc`. **`rc=1` sobre o recorte não é achado**: a §3.4 nomeia páginas e escreve prosa, que o
> script não conhece — resolva cada acusado contra `src/pages`/`src/components` antes de concluir
> (o `ui-reviewer` traz o comando pronto). O que fica aqui é julgamento.

## Cadeia do padrão visual

```
código (*_v2 + theme.ts) > skill ui-v2 > frontend/<ws>/CLAUDE.md
```

A fonte é `.claude/skills/ui-v2/` (SKILL + `references/familias.md`, `paleta.md`,
`telas-canonicas.md`), e **o que compila vence a skill**. Achado visual cita o export real de
`global_v2.tsx` ou `globalMaterialUi_v2.tsx`.

⚠️ **Exceções declaradas — não abrir achado**: aba de Arquivos/Anexos e `components/KanbanBoard/`
permanecem v1 por decisão do usuário; as 152 páginas v1 puras são legado que migra quando a feature
as tocar. Componente do v1 (`CssBox`, `CssDateField`, `UlFormCol*`…) em tela **nova** é violação.

## O que o script não alcança

- **A tela faz o que a RN pede?** Cobertura spec → código continua sendo leitura.
- **Montagem**: família certa para o caso (listagem × formulário com abas × aba filha × modal ×
  workflow) — ver `telas-canonicas.md`.
- **Modal dentro de `<Form>`**: se a grade fica dentro do `<Form>` da aba, o modal precisa ficar
  **fora** dele e o id sobe para o contexto. Submit atravessa portal pela árvore do React, e o
  modal salvaria o formulário inteiro.
- **FE-016**: paginação e ordenação server-side de verdade (`paginationMode`, `sortingMode` e os
  handlers), não só `rowCount`.
- **FE-017**: condição terminal como gatilho de ação apaga o botão para sempre.
- **FE-026**: tela entregue com o corpo comentado (`carriers` já fez isso 3×).

**Veredito**: v1 em tela nova, componente inexistente, ou RN sem implementação na tela = bloqueante.
