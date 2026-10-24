# Comando: /add-service

> **Título**: Adicionar Service a Módulo Existente
> **Descrição**: Adiciona um ou mais services avulsos a um módulo DDD já criado, sem recriar o scaffold completo. Útil para operações extras como exportação, envio de e-mail, aprovação, cálculo, etc.

---

## Uso

```
/add-service <contexto> <modulo> <NomeDoService>
```

**Exemplos:**
- `/add-service contracts annexes ExportContractAnnexService`
- `/add-service financial receivable SendReceivableReminderService`
- `/add-service contracts contracts ApproveContractService CancelContractService`

> Você pode informar múltiplos services separados por espaço.

---

## O que este comando gera

Para cada service informado, cria:

```
src/modules/<contexto>/<modulo>/services/
└── <NomeDoService>.ts

src/modules/<contexto>/<modulo>/tests/
└── <NomeDoService>.spec.ts
```

---

## Instruções de geração

Ao receber este comando, execute **passo a passo**:

1. **Leia** o arquivo `src/modules/<contexto>/<modulo>/repositories/I<Entity>Repository.ts` para conhecer os métodos já disponíveis no repositório.
2. **Pergunte** qual a responsabilidade de cada service informado (se não for óbvio pelo nome).
3. **Gere o service** seguindo a estrutura:
   ```typescript
   import { inject, injectable } from 'tsyringe'
   import { I<Entity>Repository } from '../repositories/I<Entity>Repository'

   @injectable()
   class <NomeDoService> {
     constructor(
       @inject('<Entity>Repository')
       private <entity>Repository: I<Entity>Repository,
     ) {}

     async execute(/* parâmetros */): Promise</* retorno */> {
       // lógica
     }
   }

   export { <NomeDoService> }
   ```
4. **Se o service precisar de novo método no repositório**, gere também:
   - A assinatura no `I<Entity>Repository.ts`
   - A implementação no `<Entity>Repository.ts`
5. **Gere o teste** com mock do repositório usando `InMemory<Entity>Repository` se já existir, ou crie um mock inline.
6. **Se o service for chamado via HTTP**, informe o que adicionar manualmente:
   - Novo método no Controller (respeitando o limite de 5 — criar `<Entity>ActionsController.ts` se necessário)
   - Nova rota em `<entity>.routes.ts` com Joi inline e `accessControl`
7. **Execute** `yarn lint:fix` ao final.

---

## Regras críticas

- Services nunca acessam DB diretamente — só via Repository injetado.
- Um arquivo por service, uma responsabilidade.
- Se o controller já tem 5 métodos, criar um novo controller separado para a ação.
- Schemas Joi ficam **inline** nas rotas, nunca em arquivo separado.
- Nunca modificar services existentes — apenas adicionar novos.
