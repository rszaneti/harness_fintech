// Test – Delete__Entity__Service
import Delete__Entity__Service from '../services/Delete__Entity__Service'

describe('Delete__Entity__Service', () => {
  let __entity__Repository: any
  let service: Delete__Entity__Service

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
    service = new Delete__Entity__Service(__entity__Repository)
  })

  it('should delete __entities__ by ids', async () => {
    __entity__Repository.delete.mockResolvedValue(undefined)

    await service.execute({ __registro_id__: ['uuid-1', 'uuid-2'] })

    expect(__entity__Repository.delete).toHaveBeenCalledWith(['uuid-1', 'uuid-2'])
  })
})
