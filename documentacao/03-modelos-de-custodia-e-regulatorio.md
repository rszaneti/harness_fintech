# Modelos de custódia e enquadramento regulatório

> **Decisão registrada em 23/10/2026**: o produto nasce no **modelo 2 (BaaS do BTG)**. A plataforma
> é software e API; o BTG é o custodiante. A plataforma **nunca** mantém saldo próprio de terceiros.
> Esta decisão é premissa de toda spec do backend: qualquer desenho que a viole é defeito de spec.

---

## 1. A pergunta que define a arquitetura

Quem paga (o cliente final do nosso cliente) pode usar qualquer banco: Pix e boleto são
interoperáveis. **A pergunta é sobre quem recebe**: onde cai o dinheiro do cliente da plataforma
SaaS, e quem é dono legal daquele saldo.

| | 1. Conta BTG por consentimento | **2. Conta embutida (BaaS do BTG)** ← escolhido | 3. Plataforma recebe e repassa |
|---|---|---|---|
| Onde o dinheiro cai | Direto na conta BTG Empresas do cliente | Numa conta de pagamento aberta **pela nossa API, em nome do cliente**, dentro do BTG | Na conta da plataforma (ou da V-Corp); repasse posterior |
| Cliente precisa "ter BTG"? | Sim: abre conta BTG Empresas (digital, gratuita) e dá consentimento OAuth | Tecnicamente sim, mas não percebe: a conta nasce no onboarding, o KYC é do BTG, e ele saca para qualquer banco | Não |
| Quem é regulado | Só o BTG. Plataforma = software | O BTG. Plataforma = provedor de tecnologia, com contrato de BaaS | **A plataforma.** Guardar dinheiro de terceiros é gestão de conta de pagamento / emissão de moeda eletrônica (Lei 12.865/2013) |
| Split automático | Não nativo: taxa vira fatura ou débito autorizado | **Nativo**: retém a taxa antes de liberar o saldo | Sim |
| Quem faz assim | Omie, Senior, Kobana e os 200+ ERPs integrados ao BTG | Fintechs em cima de Dock, QI Tech, Celcoin | Asaas, Pagar.me, PagSeguro — todos instituições de pagamento (IP) autorizadas |
| Papel no projeto | **Plano B** se o BaaS atrasar | **Modelo do MVP** | **Proibido** sem licença |

## 2. Por que o modelo 3 está fora

O desenho "dinheiro entra na conta da V-Corp, a plataforma controla o saldo e transfere quando o
cliente pede" tem três elementos — dinheiro de terceiros em conta que não é deles, saldo mantido
pela plataforma em nome de cada cliente, saque sob demanda — e esses três elementos **são** a
definição de conta de pagamento e moeda eletrônica.

- **Banco Central**: a Res. BCB 494 (set/2025) acabou com a isenção por volume. Toda IP nova precisa
  de autorização **antes** do primeiro cliente. A Res. 495 exige sede física exclusiva, governança,
  auditoria. Custo de conformidade estimado para IP pequena: R$ 500 mil a R$ 2 milhões. IPs que
  operavam sem licença tiveram janela única em maio/2026 para regularizar.
- **O próprio BTG**: conta PJ recebendo pagamentos de milhares de pagadores destinados a terceiros,
  com repasses fracionados, é o padrão de "conta de passagem" que as regras de PLD mandam o banco
  bloquear. O compliance não enxerga os beneficiários finais; a conta tende a ser encerrada.
- **Fiscal**: todo o volume entraria como receita da V-Corp. Sem estrutura própria, é faturamento
  tributável de dinheiro que não é dela.

Não há zona cinzenta a explorar aqui. Se um dia fizer sentido ter licença própria, é decisão de
rodada de investimento (12+ meses, capital, sede), não de MVP. O pitch à V-Corp **nomeia** esse
caminho como opção futura, não o esconde.

## 3. O que o modelo 2 exige do BTG

A lista completa e priorizada está no `02-roteiro-mvp` (seção "Pré-requisitos com o BTG"). O
essencial, em ordem:

1. Abertura de conta de pagamento PJ via API, em nome do cliente da plataforma, com KYC do BTG.
2. Pix recebimento com QR dinâmico (API Pix padrão BCB: `cob`, `cobv`, webhook).
3. Pix envio (saque) por API, com limites e dupla aprovação.
4. Transferência entre contas BTG por API (o split).
5. Extrato e saldo por API, com webhook de crédito.
6. Sandbox e credenciais de homologação.

Hoje os ERPs integrados usam OAuth por consentimento do cliente (`client_id`/`client_secret`,
escopos por produto como `bank-slips`, token de 24 h, webhooks de Pix e boleto) — isso é o modelo 1
e já está documentado publicamente. O que o MVP precisa **a mais** é o item 1.

## 4. Regras que decorrem da decisão (para specs e para o `verifier`)

- **RN-REG-01** Nenhuma tabela da plataforma guarda "saldo" como coluna editável. O saldo exibido é
  derivado do ledger **e** conferido contra o saldo da conta BTG do cliente lido por API.
- **RN-REG-02** Todo lançamento do ledger referencia um evento do BTG (webhook ou extrato) ou uma
  ordem enviada ao BTG (Pix envio, transferência). Lançamento sem contrapartida no banco é
  divergência de conciliação, nunca "ajuste manual".
- **RN-REG-03** Split é executado como **transferência entre contas BTG**, nunca como retenção em
  conta da plataforma.
- **RN-REG-04** Saque é um Pix enviado **da conta do cliente** para a chave que ele indicar. A
  plataforma ordena; não intermedeia.
- **RN-REG-05** Dados de onboarding (CNPJ, sócios, documentos) são dados pessoais sob LGPD:
  consentimento registrado, criptografia em repouso (`CryptoProvider`), exportação e exclusão.
- **RN-REG-06** Qualquer spec que proponha "conta transitória", "saldo interno", "carteira" ou
  "repasse" deve ser contestada e devolvida com referência a este documento.

## 5. O que ainda falta confirmar

- [ ] O que o convênio atual com o BTG cobre por escrito, e quem são os contatos técnico e comercial.
- [ ] Se o BTG oferece BaaS formal com abertura de contas via API (item 1) — resposta define se o
  MVP nasce no modelo 2 ou no modelo 1 com migração.
- [ ] Parecer jurídico sobre o desenho do modelo 2 e sobre quem assina o contrato de BaaS (nova
  empresa, V-Corp ou o fundador).
- [ ] Modelo comercial do BTG: custo por Pix, remuneração por conta aberta, prazo de homologação.

## Fontes

Consultadas em 23/10/2026.

- [Capital Aberto: Resoluções BCB 494 e 495](https://capitalaberto.com.br/regulacao/legislacao-mercados/2025/12/mudancas-estruturais-no-regime-de-autorizacao-de-instituicoes-de-pagamento-as-resolucoes-494-e-495-do-banco-central) · [Resolução BCB 494 (texto)](https://www.legisweb.com.br/legislacao/?id=483156)
- [Senior: onboarding BTG (OAuth, escopos, webhooks)](https://documentacao.senior.com.br/seniorxplatform/manual-do-usuario/erp/Banking/ativacao-parceiros/onboarding-btg.htm) · [Omie: integração BTG via API](https://ajuda.omie.com.br/pt-BR/articles/11419274-configurando-a-integracao-com-o-btg-pactual-boletos-pix-via-api) · [Kobana: integração BTG](https://www.kobana.com.br/en/integrations/banks/btg)
- [Startups.com.br: BTG Pay e bandeira própria B2B](https://startups.com.br/negocios/btg-pactual-bandeira-propria-de-cartao-para-abrir-mercado-b2b-de-r-50-trilhoes/)
- [BTG Developer Portal (Payments)](https://developer.btgpactual.com/)
- [BCB: API Pix](https://github.com/bacen/pix-api)
