// Test – Update__Entity__Service
import AppError from '@shared/errors/AppError'
import Update__Entity__Service from '../services/Update__Entity__Service'

describe('Update__Entity__Service', () => {
  let __entity__Repository: any
  let service: Update__Entity__Service

  beforeEach(() => {
    __entity__Repository = {
      findAll: jest.fn(),
      findTotal: jest.fn(),
      findById: jest.fn(),
      findByIdRelations: jest.fn(),
      create: jest.fn(),
      save: jest.fn(),
      delete: jest.fn(),
    }
    service = new Update__Entity__Service(__entity__Repository)
  })

  it('should update a __entity__', async () => {
    // __CAMPOS__ do registro existente. Exemplo declarado:
    const existing = { id: 'uuid-mock', name: 'Antigo', status: true }
    __entity__Repository.findById.mockResolvedValue(existing)
    __entity__Repository.save.mockImplementation(async (reg: any) => reg)

    const result = await service.execute({
      __registro_id__: 'uuid-mock',
      // __CAMPOS__
      name: 'Novo',
      user_updated: 'admin',
    } as any)

    expect(__entity__Repository.findById).toHaveBeenCalledWith('uuid-mock')
    // A asserção tem de FALHAR se a atribuição do service for removida (AG-011 §3).
    expect(result.name).toBe('Novo')
    expect(result.user_updated).toBe('admin')
  })

  it('should throw when register is not found', async () => {
    __entity__Repository.findById.mockResolvedValue(null)

    await expect(
      service.execute({
        __registro_id__: 'uuid-inexistente',
        user_updated: 'admin',
      } as any),
    ).rejects.toBeInstanceOf(AppError)
  })
})
