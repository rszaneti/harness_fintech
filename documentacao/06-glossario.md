# Glossário — termos de pagamentos como valem neste projeto

> Definição operacional, não jurídica. Quando uma spec usar um termo daqui, é com este sentido.

| Termo | Definição neste projeto |
|---|---|
| **Plataforma** | Um SaaS cliente da nossa API (ex.: o SaaS da Bora Fazer). Tem chave de API, endpoints de webhook e regra de split. Tabela `platforms`. |
| **Cliente** | A PME que usa a plataforma e recebe pagamentos. Tem uma **conta de pagamento** no BTG aberta pela nossa API. Tabela `accounts`. |
| **Pagador** | Quem paga a cobrança. Pode estar em qualquer banco. Não é cadastrado. |
| **Conta de pagamento** | Conta aberta no BTG em nome do cliente, via BaaS, com KYC do BTG. O saldo é do cliente e está no banco; nós só lemos e ordenamos. |
| **BaaS** (Banking as a Service) | Modelo em que o banco licenciado (BTG) expõe abertura de conta, Pix, extrato por API e o parceiro (nós) faz onboarding e produto. |
| **IP** (Instituição de Pagamento) | Entidade autorizada pelo Banco Central a gerir contas de pagamento / emitir moeda eletrônica. **Não somos e não queremos ser no MVP.** |
| **Modelo 1 / 2 / 3** | Ver `03-modelos-de-custodia`. 1 = conta BTG do cliente por consentimento; **2 = conta embutida via BaaS (escolhido)**; 3 = plataforma recebe e repassa (proibido). |
| **Cobrança** (`charge`) | Pedido de pagamento Pix com QR dinâmico, valor, vencimento e `external_reference` (ID do negócio no CRM). Estados: `pending` → `paid` / `expired` / `cancelled`. |
| **QR dinâmico** | QR Code Pix gerado por cobrança (`cob`/`cobv` da API Pix do BCB), com valor fixo e identificador único (`txid`). |
| **Webhook** | Notificação HTTP assinada. **Recebido** do BTG (pagamento, crédito, status de conta) ou **emitido** por nós para a plataforma (`charge.paid`, `account.approved`, `payout.settled`). |
| **Ledger** | Registro contábil de partidas dobradas, **append-only**. Todo movimento de dinheiro é um conjunto de lançamentos que soma zero. Saldo é derivado. |
| **Lançamento** (`ledger_entry`) | Uma linha do ledger: conta, valor em centavos (`BIGINT`), débito ou crédito, referência ao evento de origem. Nunca alterado nem apagado. |
| **Estorno** | Lançamento novo, inverso, com referência ao original. Nunca exclusão. |
| **Split** | Divisão automática de um crédito entre cliente, plataforma (taxa) e terceiros (ex.: Bora Fazer). Executado como **transferências entre contas BTG**, nunca retenção nossa. |
| **Take rate** | Nossa taxa sobre a transação (hipótese 0,8–1,2 %, teto R$ 5). Uma das pernas do split. |
| **Payout** (saque) | Pix enviado da conta do cliente para a chave que ele indicar. Tem limite diário e dupla aprovação acima de um valor. Estados: `requested` → `approved` → `sent` → `settled` / `failed`. |
| **Dupla aprovação** | Payout acima do limite exige aprovação de um segundo usuário, diferente do solicitante, com MFA. |
| **Conciliação** | Comparação diária entre saldo derivado do ledger e saldo da conta BTG lido por API. Divergência gera alerta; nunca ajuste automático. |
| **Idempotência** | Garantia de que repetir uma chamada de escrita com a mesma `Idempotency-Key` devolve a mesma resposta sem repetir o efeito. Obrigatória em todo `POST`/`PUT`. |
| **HMAC** | Assinatura do corpo da requisição com segredo compartilhado (SHA-256). Usada nas chamadas das plataformas para nós e nos webhooks nos dois sentidos. |
| **JWKS** | Conjunto público de chaves para validar JWT assinado com chave assimétrica (RS256/ES256). Permite que plataformas validem nossos tokens sem a chave privada. |
| **KYC** | Verificação de identidade do cliente (CNPJ, sócios, documentos). **Feita pelo BTG**; nós coletamos e enviamos. |
| **Simulador BTG** | Servidor fake em `tools/btg-simulator/` que imita as respostas do BTG (abertura de conta, Pix pago, extrato). Mesma interface do adaptador real. |
| **Adaptador BTG** | Única peça que fala com o banco. Interface + implementação real + simulador. Trocável sem mudar o resto. |
| **Portão** | Decisão de seguir, ajustar ou parar ao fim de cada fase do roteiro. Quatro no MVP. |
