// Test – List__Entities__Service
import List__Entities__Service from '../services/List__Entities__Service'

describe('List__Entities__Service', () => {
  let __entity__Repository: any
  let service: List__Entities__Service

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
    service = new List__Entities__Service(__entity__Repository)
  })

  it('should list __entities__ with filters and pagination', async () => {
    const mockList = [{ id: 'uuid-1' }, { id: 'uuid-2' }]
    __entity__Repository.findAll.mockResolvedValue(mockList)

    const result = await service.execute({
      page: 1,
      rowsperpage: 25,
      sort_order: 'ASC',
    } as any)

    expect(result).toHaveLength(2)
    expect(__entity__Repository.findAll).toHaveBeenCalledTimes(1)
  })
})
