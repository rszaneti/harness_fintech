# Comando: /new-report

> **Título**: Gerar Endpoint de Relatório com Filtros e Exportação
> **Descrição**: Cria um endpoint de relatório para um módulo existente com filtros avançados, totalizadores e exportação para CSV/XLSX. Padrão distinto do CRUD — não gera scaffold completo, apenas os arquivos do relatório.

---

## Uso

```
/new-report <contexto> <modulo> <NomeDoRelatorio>
```

**Exemplos:**
- `/new-report financial receivable ReceivableReport`
- `/new-report contracts contracts ContractProductionReport`
- `/new-report graduates graduates GraduateCommissionReport`

---

## O que este comando gera

```
src/modules/<contexto>/<modulo>/
├── dtos/
│   └── IFind<NomeDoRelatorio>DTO.ts          # filtros + paginação
├── services/
│   └── List<NomeDoRelatorio>Service.ts       # query com filtros
│   └── Export<NomeDoRelatorio>Service.ts     # gera buffer CSV/XLSX
├── tests/
│   └── List<NomeDoRelatorio>Service.spec.ts
└── infra/
    └── http/
        └── controllers/
        │   └── <NomeDoRelatorio>Controller.ts  # métodos: index, export
        └── routes/
            └── <camelCase>.routes.ts           # GET /list + GET /export
```

---

## Instruções de geração

Ao receber este comando, execute **passo a passo**:

1. **Leia** a entity e o repository existentes do módulo para entender os campos disponíveis.
2. **Pergunte** quais filtros o relatório deve aceitar (ex: período de datas, status, cliente, responsável).
3. **Pergunte** quais colunas devem aparecer no relatório e na exportação.
4. **Pergunte** se há totalizadores (soma de valores, contagem, médias).
5. **Gere o DTO de filtro** `IFind<NomeDoRelatorio>DTO.ts`:
   ```typescript
   export interface IFind<NomeDoRelatorio>DTO {
     page: number
     rowsperpage: number
     sort_field?: string
     sort_order?: 'ASC' | 'DESC'
     date_start?: string
     date_end?: string
     // filtros específicos informados
   }
   ```
6. **Adicione método no Repository** `findReport(filters: IFind<NomeDoRelatorio>DTO): Promise<[Entity[], number]>` com QueryBuilder usando todos os filtros.
7. **Gere o `List<NomeDoRelatorio>Service`**:
   - Chama `repository.findReport(filters)`
   - Retorna `{ <entidades>: Entity[], <entidades>total: number, totals?: { ... } }`
8. **Gere o `Export<NomeDoRelatorio>Service`**:
   - Busca todos os registros (sem paginação) com os mesmos filtros
   - Gera CSV usando apenas dependências nativas do Node.js (sem bibliotecas externas):
     ```typescript
     const header = ['Coluna 1', 'Coluna 2', ...].join(';')
     const rows = data.map(row => [row.field1, row.field2, ...].join(';'))
     const csv = [header, ...rows].join('\n')
     return Buffer.from('﻿' + csv, 'utf-8') // BOM para Excel
     ```
   - Content-Type: `text/csv; charset=utf-8`
   - Content-Disposition: `attachment; filename="<nome_relatorio>.csv"`
9. **Gere o Controller** com dois métodos:
   - `index`: lista paginada com totalizadores
   - `export`: retorna o buffer CSV via `res.send(buffer)`
10. **Gere as rotas**:
    ```
    GET  /<modulo>-report          → index   (permissão: <modulo>_view)
    GET  /<modulo>-report/export   → export  (permissão: <modulo>_view)
    ```
    Schemas Joi inline com validação dos filtros.
11. **Informe** o que fazer manualmente:
    - Registrar as rotas em `src/shared/infra/http/routes/index.ts`
    - Adicionar método `findReport` na interface `I<Entity>Repository`
12. **Execute** `yarn lint:fix` ao final.

---

## Regras críticas

- Exportação usa apenas recursos nativos do Node.js — **sem instalar `xlsx`, `exceljs` ou similares**.
- BOM (`﻿`) obrigatório no CSV para garantir encoding correto no Excel.
- Separador de colunas: ponto-e-vírgula (`;`) — padrão pt-BR.
- Filtros de data aceitam string ISO (`YYYY-MM-DD`) e são convertidos internamente com `BETWEEN`.
- O service de exportação **não pagina** — retorna todos os registros do filtro.
- Controller de relatório pode ultrapassar 5 métodos se necessário (relatórios são contexto diferente do CRUD).
- Permissão de exportação reutiliza `<modulo>_view` — não criar permissão separada.
