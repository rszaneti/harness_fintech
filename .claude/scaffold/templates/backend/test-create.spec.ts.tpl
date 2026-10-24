// Test – Create__Entity__Service
// Regras: jest.fn() para todos os métodos do repository; NUNCA importar a Entity;
// cobrir caminho feliz + cenários de erro (unicidade etc.).
import Create__Entity__Service from '../services/Create__Entity__Service'

describe('Create__Entity__Service', () => {
  let __entity__Repository: any
  let service: Create__Entity__Service

  beforeEach(() => {
    __entity__Repository = {
      findAll: jest.fn(),
      findTotal: jest.fn(),
      findById: jest.fn(),
      findByIdRelations: jest.fn(),
      create: jest.fn(),
// @if !append_only
      save: jest.fn(),
      delete: jest.fn(),
// @endif
    }
    service = new Create__Entity__Service(__entity__Repository)
  })

  it('should create a __entity__', async () => {
    const mockReg = {
      id: 'uuid-mock',
      // __CAMPOS__ do mock. Exemplo declarado:
      name: 'Exemplo',
    }
    __entity__Repository.create.mockResolvedValue(mockReg)

    const result = await service.execute({
      // __CAMPOS__ do payload
      name: 'Exemplo',
      user_created: 'admin',
    } as any)

    expect(result.id).toBe('uuid-mock')
    expect(__entity__Repository.create).toHaveBeenCalledTimes(1)
  })

  // __TESTES_DE_ERRO__ — ex.: unicidade violada deve lançar AppError
})
