// Routes – endpoints REST do módulo __tabela__
// Regras: Joi INLINE (nunca em arquivo separado); ensureAuthenticated + accessControl em todas
// @if !append_only
// as rotas privadas; show é GET /show/:id; delete via query id (array).
// @endif
// @if append_only
// as rotas privadas; show é GET /show/:id. Append-only: só GET /, GET /show/:id e POST / (RN-09).
// @endif
// [BE-003] Webhooks públicos: registrar ANTES de ensureAuthenticated em routes/index.ts.
// [spec 001, RN-13] Toda rota POST/PUT/PATCH leva `ensureIdempotency` (Idempotency-Key, invariante
// 8) — o hook `idempotency-required` reprova sem ele. Isenção (webhook que deduplica por event_id,
// login/refresh) só com o marcador `idempotency-exempt: <motivo>` na linha de cima, que o verifier audita.
import { Router } from 'express'
import { celebrate, Joi, Segments } from 'celebrate'

import ensureAuthenticated from '@shared/infra/http/middlewares/ensureAuthenticated'
import ensureIdempotency from '@shared/infra/http/middlewares/ensureIdempotency'
// ⚠️ O middleware de permissão mora em `middlewares/permissions` (não existe `middlewares/accessControl`
// — o template dizia isso até 2026-09-11 e o módulo gerado não compilava; o --self-test pegou).
import accessControl from '@shared/infra/http/middlewares/permissions'
import __Entities__Controller from '../controllers/__Entities__Controller'

const __entities__Router = Router()
const __entities__Controller = new __Entities__Controller()

__entities__Router.use(ensureAuthenticated)

__entities__Router.get(
  '/',
  accessControl(['__permissao___view']),
  celebrate({
    [Segments.QUERY]: {
      // __FILTROS__ — um por filtro do IFind DTO. Exemplo declarado:
      search_name: Joi.string().optional().allow(''),
      sort_field: Joi.string().optional().allow(''),
      sort_order: Joi.string().valid('ASC', 'DESC').optional().allow(''),
      page: Joi.number().integer().min(1).optional(),
      rowsperpage: Joi.number().integer().min(0).optional(),
    },
  }),
  __entities__Controller.index,
)

__entities__Router.get(
  '/show/:id',
  accessControl(['__permissao___view']),
  celebrate({
    [Segments.PARAMS]: { id: Joi.string().uuid().required() },
  }),
  __entities__Controller.show,
)

__entities__Router.post(
  '/',
  accessControl(['__permissao___create']),
  ensureIdempotency,
  celebrate({
    [Segments.BODY]: Joi.object().keys({
      // __CAMPOS__ — espelha o ICreate DTO (o frontend espelha ESTE schema — FE-025). Exemplo declarado:
      // contracts_id: Joi.string().uuid().required(),
      // description: Joi.string().optional().allow(null, ''),
      name: Joi.string().required(),
    }),
  }),
  __entities__Controller.create,
)

// @if !append_only
__entities__Router.put(
  '/',
  accessControl(['__permissao___update']),
  ensureIdempotency,
  celebrate({
    [Segments.BODY]: Joi.object().keys({
      __registro_id__: Joi.string().uuid().required(),
      // __CAMPOS__ — espelha o IUpdate DTO. Exemplo declarado:
      name: Joi.string().required(),
      status: Joi.boolean().optional(),
    }),
  }),
  __entities__Controller.update,
)

__entities__Router.delete(
  '/',
  accessControl(['__permissao___delete']),
  celebrate({
    [Segments.QUERY]: {
      id: Joi.alternatives()
        .try(Joi.string().uuid(), Joi.array().items(Joi.string().uuid()))
        .required(),
    },
  }),
  __entities__Controller.delete,
)

// Workflow (se houver): rotas PATCH /:id/<acao> (ex.: /approve, /cancel) com __permissao___update
// e `ensureIdempotency` — PATCH é escrita (spec 001, RN-13)
// @endif

export default __entities__Router
