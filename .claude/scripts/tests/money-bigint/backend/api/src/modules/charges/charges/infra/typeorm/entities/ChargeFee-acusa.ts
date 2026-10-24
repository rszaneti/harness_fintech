import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm'

@Entity('charge_fees')
class ChargeFee {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column('int4') // @acusa
  fee_cents: number
}

export default ChargeFee
