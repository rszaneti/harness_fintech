// Test – ListTotal__Entities__Service
import ListTotal__Entities__Service from '../services/ListTotal__Entities__Service'

describe('ListTotal__Entities__Service', () => {
  let __entity__Repository: any
  let service: ListTotal__Entities__Service

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
    service = new ListTotal__Entities__Service(__entity__Repository)
  })

  it('should return the total of __entities__', async () => {
    __entity__Repository.findTotal.mockResolvedValue(7)

    const result = await service.execute({} as any)

    expect(result).toBe(7)
    expect(__entity__Repository.findTotal).toHaveBeenCalledTimes(1)
  })
})
