# Documentação de negócio — Plataforma de Pagamentos (BTG BaaS)

> Esta pasta é o **contexto de negócio** que os agentes leem antes de gerar código. Não é padrão
> de código (isso está em `.claude/skills/` e `.claude/scaffold/`). Regra do harness: quando a
> documentação e o código divergem, o código que compila vence — e a divergência é reportada.
>
> Origem: conversa de concepção em 22–23/10/2026, no projeto "Startups" do Claude. Última
> atualização: 23/10/2026.

## Leia nesta ordem

| # | Documento | O que responde | Quem lê |
|---|---|---|---|
| 01 | [Proposta Bora Fazer — Plataforma de Vendas com IA](01-proposta-bora-fazer-plataforma-vendas-ia.md) | O primeiro cliente da plataforma de pagamentos: o SaaS de vendas com IA para PMEs, sua tese, mercado e MVP | Quem precisa entender **para quem** a cobrança Pix existe |
| 02 | [Roteiro do MVP — Plataforma de Pagamentos](02-roteiro-mvp-plataforma-pagamentos-btg-baas.md) | O que o MVP prova, o que pedir ao BTG, escopo, arquitetura, 12 semanas, demo para a V-Corp, custo, riscos | **Todo mundo.** É o documento mestre |
| 03 | [Modelos de custódia e regulatório](03-modelos-de-custodia-e-regulatorio.md) | Por que o dinheiro fica no BTG e nunca na plataforma; Res. BCB 494/495; regras RN-REG que toda spec respeita | `spec-new`, `spec-plan`, `verifier` |
| 04 | [Stack e segurança](04-stack-e-seguranca-backend.md) | Decisão de manter a stack do harness; o que endurecer e como; workspaces e módulos; invariantes do ledger | `backend-lead`, `backend-test-author`, `backend-builder`, `verifier` |
| 05 | [Análise do harness e plano de adaptação](05-analise-harness-e-plano-de-adaptacao.md) | O que o harness herdado é, o que muda, a spec 001 e a sequência de specs do MVP | Sessão principal; quem roda `/spec-new 001` |
| 06 | [Glossário](06-glossario.md) | Termos de pagamentos usados nas specs, com a definição que vale neste projeto | Qualquer agente que encontrar um termo |
| — | [Harness](HARNESS.md) | Origem do harness, dívidas vigentes e histórico de versões (não é contexto de negócio: é a memória do processo) | Quem mexe em `.claude/` |

## Decisões já tomadas (não reabrir em spec)

| Decisão | Onde está |
|---|---|
| Modelo de custódia: **BaaS do BTG** (modelo 2). A plataforma nunca guarda saldo de terceiros | 03 §1–§2 |
| Stack: **a do harness** (Express + TypeORM + tsyringe + Joi; React + MUI + Formik + axios) | 04 §1 |
| Dinheiro em **`BIGINT` centavos**; ledger **append-only** de partidas dobradas | 04 §2, §5 |
| JWT **assimétrico com JWKS**; token em **cookie HttpOnly**, nunca `localStorage` | 04 §2–§3 |
| V-Corp entra como **sócia-investidora**; duas empresas (pagamentos e vendas com IA), cap tables separados | 02 "Próximos passos" |
| Primeira plataforma cliente: **SaaS da Bora Fazer**; demo = cobrança Pix dentro da conversa do WhatsApp | 02 "Escopo", 01 |

## Perguntas em aberto (respostas entram aqui, não em spec)

- O que o convênio com o BTG cobre por escrito; se há BaaS com abertura de conta via API.
- Parecer jurídico sobre o modelo 2 e quem assina o contrato de BaaS.
- Custo por Pix e remuneração do BTG por conta aberta.
- Nome e marca do produto.

## Como atualizar esta pasta

- Decisão nova → tabela "Decisões já tomadas" + o documento de origem.
- Resposta a pergunta em aberto → remover da lista acima, registrar no documento certo com data.
- Documento novo → numeração sequencial, linha nesta tabela.
- Nunca editar `.claude/specs/*` para registrar decisão de negócio: spec é contrato de entrega, não
  memória do projeto.
