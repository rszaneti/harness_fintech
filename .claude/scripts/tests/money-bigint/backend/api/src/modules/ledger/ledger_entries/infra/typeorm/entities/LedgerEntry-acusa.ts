import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm'

@Entity('ledger_entries')
class LedgerEntry {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column('numeric', { precision: 12, scale: 2 }) // @acusa
  amount: number
}

export default LedgerEntry
