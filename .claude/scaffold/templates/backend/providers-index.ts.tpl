// Provider – registro do __Entity__Repository no container IoC (tsyringe)
// ⚠️ Importar este arquivo em src/shared/container/index.ts (checklist manual).
// NÃO em container/providers/index.ts — lá só moram os providers compartilhados.
import { container } from 'tsyringe'

import I__Entity__Repository from '../repositories/I__Entity__Repository'
import __Entity__Repository from '../infra/typeorm/repositories/__Entity__Repository'

container.registerSingleton<I__Entity__Repository>(
  '__Entity__Repository',
  __Entity__Repository,
)
