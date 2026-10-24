import { Entity, Column, Index, PrimaryGeneratedColumn } from 'typeorm'

@Entity('payout_decorated')
class PayoutDecorated {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column('int4') // @acusa
  @Index()
  fee_cents: number

  @Column('numeric', { precision: 10, scale: 2 }) // @acusa
  public readonly rate: number

  @Column('int4') // @acusa
  public total_cents: number

  @Column('int8')
  @Index()
  public amount_cents: string
}

export default PayoutDecorated
