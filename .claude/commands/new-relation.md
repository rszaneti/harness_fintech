# Comando: /new-relation

> **Título**: Adicionar Relacionamento entre Módulos Existentes
> **Descrição**: Adiciona uma FK entre duas entidades já existentes, atualizando Entity, DTOs, Repository e gerando a migration correspondente. Evita o erro de esquecer algum dos pontos de atualização.

---

## Uso

```
/new-relation <contexto-origem> <modulo-origem> <Entity-origem> <contexto-destino> <modulo-destino> <Entity-destino> <tipo>
```

**Tipos de relacionamento:**
| Tipo | Significado |
|------|-------------|
| `ManyToOne` | Muitos origem para um destino (FK fica na tabela de origem) |
| `OneToMany` | Um origem para muitos destino (FK fica na tabela de destino) |
| `OneToOne` | Um para um (FK fica na tabela de origem) |
| `ManyToMany` | Muitos para muitos (tabela pivot) |

**Exemplos:**
- `/new-relation contracts annexes ContractAnnex contracts contracts Contract ManyToOne`
  *(ContractAnnex pertence a Contract — FK `contracts_id` em `contract_annexes`)*
- `/new-relation employees employees Employee graduates graduates Graduate ManyToMany`
  *(pivot `employees_graduates`)*

---

## O que este comando gera/modifica

### ManyToOne / OneToOne

```
MODIFICA:
  src/modules/<ctx-origem>/<mod-origem>/infra/typeorm/entities/<Entity-origem>.ts
  src/modules/<ctx-origem>/<mod-origem>/dtos/ICreate<Entity-origem>DTO.ts
  src/modules/<ctx-origem>/<mod-origem>/dtos/IUpdate<Entity-origem>DTO.ts
  src/modules/<ctx-origem>/<mod-origem>/dtos/IFind<Entity-origem>DTO.ts
  src/modules/<ctx-origem>/<mod-origem>/infra/typeorm/repositories/<Entity-origem>Repository.ts
  src/modules/<ctx-origem>/<mod-origem>/repositories/I<Entity-origem>Repository.ts

GERA MIGRATION:
  AlterTable<Tabela-origem>Add<Entity-destino>Id
```

### ManyToMany

```
MODIFICA: ambas as entidades (sem FK direta — apenas decorators @ManyToMany/@JoinTable)

GERA MIGRATION:
  CreateTable<Tabela-origem>_<tabela-destino>  (tabela pivot)
```

---

## Instruções de geração

Ao receber este comando, execute **passo a passo**:

1. **Leia** as entities de origem e destino para entender os campos atuais.
2. **Pergunte** o comportamento `onDelete`: `CASCADE`, `SET NULL` ou `RESTRICT`.
3. **Pergunte** se o campo FK é obrigatório (`NOT NULL`) ou opcional (`nullable`).
4. **Para ManyToOne**:
   - Adicione o campo FK (`<entity_destino_singular>_id: string`) na entity de origem com `@Column` + decorator `@ManyToOne(() => <Entity-destino>)`.
   - Adicione o campo FK nos DTOs `ICreate` e `IUpdate`.
   - Adicione filtro por FK no `IFind` DTO.
   - Atualize o método `list` do repository para incluir `leftJoinAndSelect` se necessário.
5. **Para ManyToMany**:
   - Adicione `@ManyToMany(() => <Entity-destino>)` + `@JoinTable` na entity de origem.
   - Adicione `@ManyToMany(() => <Entity-origem>)` na entity de destino (lado inverso).
6. **Gere a migration** seguindo o padrão do projeto (FKs separadas, `onDelete` explícito).
7. **Informe** o que fazer manualmente:
   - Rodar: `yarn typeorm migration:run`
   - Se quiser eager loading, adicionar `relations` nas queries dos services
8. **Execute** `yarn lint:fix` ao final.

---

## Regras críticas

- FK sempre no plural snake_case: `contracts_id`, não `contract_id`.
- `onDelete` deve ser sempre explícito — nunca omitir.
- FKs são criadas **separadas** da tabela na migration (não inline em `columns`).
- Nunca usar `eager: true` nas entities — carregar relações explicitamente nos services.
- `@JoinTable` fica apenas em **um** dos lados do ManyToMany (lado dominante/origem).
