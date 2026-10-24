import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm'

// O simulador imita o BTG e não move dinheiro: fora do escopo da RN-11 (MONEY_WORKSPACES).
@Entity('fake_payouts')
class FakePayout {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column('numeric', { precision: 12, scale: 2 })
  amount: number
}

export default FakePayout
