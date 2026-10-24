# Sprint <AAAA-MM-DD>

> Gerado por `/sprint-close` (spec 089/F6). Números são do **instante em que rodou** —
> `em_andamento/` cresce durante a própria sprint.

---

## 1. O que ficou aberto — e por quê

> ⚠️ **Esta seção é escrita pelo usuário, à mão.** É a razão de o arquivo existir: o `git log`
> conta o que foi feito; só isto conta **por que o resto não foi**. Uma seção gerada aqui seria
> uma lista do que já está na tabela da §5, com outras palavras.

- **<feature>** — ficou aberta porque …
- **<feature>** — ficou aberta porque …

**Decisões tomadas nesta sprint que valem para as próximas:**

- …

---

## 2. Base do ciclo

Descoberta pelo último merge alcançável do `HEAD`, **por workspace** — são repositórios distintos.

| Workspace | Hash | Data | Assunto |
|---|---|---|---|
| `backend/api` | | | |
| `frontend/operador` | | | |
| `frontend/cliente` | | | |
| `tools/btg-simulator` | | | |
| raiz (harness) | | | |

Base sobreposta por `--since`? ☐ não ☐ sim: `<ref>`, porque …

---

## 3. Gate `--full`

| Workspace | `rc` | `diff_hash` | Passos | Tempo | Árvore suja (`--porcelain \| wc -l`) |
|---|---|---|---|---|---|
| `backend/api` | | | | | |
| `frontend/operador` | | | | | |
| `frontend/cliente` | | | | | |
| `tools/btg-simulator` | | | | | |
| `harness` | | | | | |

⚠️ **O `--full` mediu a árvore de trabalho, não o último commit** — untracked incluídos. O que
estava alterado no instante, nominalmente, e por quê:

| Workspace | Arquivo | De qual feature é | Entra no gate? |
|---|---|---|---|
| | | | |

**De quem é cada vermelho** — sem isto o relatório nasce vermelho e ninguém sabe por quê:

| Suíte / arquivo | De qual spec é | Já registrado lá? |
|---|---|---|
| | | |

**Rodadas de gate por workspace** (a evidência guarda só a última — dívida da spec 090):

| Workspace | Rodadas | Escopo e `rc` de cada |
|---|---|---|
| | | |

---

## 4. Contrato cruzado desde a base

O que a auditoria por feature **não** enxerga: duas features do mesmo ciclo mexendo na mesma
resposta.

| Achado | Módulos envolvidos | Severidade | De quem é |
|---|---|---|---|
| | | | |

---

## 5. O que falta em cada feature

Saída do `sprint-status.sh`. **A categoria é heurística e erra** — a linha `↳` traz o texto da task
de propósito; é por ela que se decide, não pelo rótulo.

| Categoria | Features |
|---|---:|
| Falta só rodar o gate | |
| Aguarda validação do usuário | |
| Precisa de operação manual | |
| Em construção de fato | |
| Harness (nenhum gate as alcança) | |

<tabela completa colada aqui>

---

## 6. O que este relatório NÃO sabe

| Não sabe | Por quê | Sai quando |
|---|---|---|
| quantas rodadas de gate houve por workspace | a evidência acumula (`rc` = o pior, `scopes`), mas não guarda cada rodada | não sai — o `--full` desta sprint é a medição |
| se o `.md` do harness está certo | `verify.sh harness` roda `bash -n`, compilação e self-tests, mas não lê prosa | não sai — prosa de agente/skill é do `verifier` |
| se a classificação da §5 está certa | heurística de palavra | não sai — por isso o texto vai junto |

---

## 7. O que o harness aprendeu nesta sprint

- **Dívidas novas**: …
- **Lessons candidatas** (e se são promovíveis): …
- **O que uma verificação verde escondeu**: …
