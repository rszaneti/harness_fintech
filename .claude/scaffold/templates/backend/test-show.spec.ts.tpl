// Test – Show__Entity__Service
import AppError from '@shared/errors/AppError'
import Show__Entity__Service from '../services/Show__Entity__Service'

describe('Show__Entity__Service', () => {
  let __entity__Repository: any
  let service: Show__Entity__Service

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
    service = new Show__Entity__Service(__entity__Repository)
  })

  it('should return a __entity__ by id', async () => {
    const mockReg = { id: 'uuid-mock' }
    __entity__Repository.findByIdRelations.mockResolvedValue(mockReg)

    const result = await service.execute({ __registro_id__: 'uuid-mock' })

    expect(result.id).toBe('uuid-mock')
    expect(__entity__Repository.findByIdRelations).toHaveBeenCalledWith('uuid-mock')
  })

  it('should throw when register is not found', async () => {
    __entity__Repository.findByIdRelations.mockResolvedValue(null)

    await expect(
      service.execute({ __registro_id__: 'uuid-inexistente' }),
    ).rejects.toBeInstanceOf(AppError)
  })
})
