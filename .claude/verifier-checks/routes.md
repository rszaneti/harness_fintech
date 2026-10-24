# check `routes` — rota ou controller mudou [BE-014, BE-003, BE-016, BE-024]

> Acende quando o diff toca `*.routes.ts` ou `infra/http/controllers/`.
> O `check-module.py` já reprova mecanicamente o `Joi.boolean()` em QUERY (BE-016) e o hook bloqueia
> na edição. O que fica aqui é o que exige leitura.

## BE-014 — rota literal sombreada por `/:param`

O Express casa **na ordem de registro**: com `/:id` antes, um `DELETE /file` cai no handler de
`/:id` com `id='file'`, morre no celebrate e nunca chega ao controller. O hook pega dentro de um
arquivo; confira também o **registro em `routes/index.ts`**, que ele não vê.

## BE-003 — webhook público

Rota pública de webhook é registrada **ANTES** de `ensureAuthenticated` em `routes/index.ts`.
Depois dele, o webhook responde 401 para o provedor e ninguém percebe até a integração falhar.

## Permissão

Módulo **novo** = `<tabela>_view/_create/_update/_delete`. Módulo **legado** = o sufixo que as
rotas dele já usam (`_edit` em 77 módulos) — copiar do `accessControl` existente, **nunca inventar**
(spec 085, RN-10). Confira que a permissão citada existe na tabela `permissions`: `description`
guarda o **módulo** e `type_permission` a **ação** (as colunas são invertidas em relação ao nome).

⚠️ Grep de permissão é **semântico**: procure o construto `accessControl([...])`, não a string — o
nome aparece também em comentários que mandam NÃO usá-la (AG-013).

## BE-024 — upload

`celebrate` **antes** do `multer` faz a rota de upload retornar 400 SEMPRE: o corpo multipart ainda
não foi parseado quando o Joi olha.

**Veredito**: sombreamento, webhook atrás do auth, permissão inventada ou celebrate antes do multer
= bloqueante.
