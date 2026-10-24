import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm'
import toNumber from '@shared/infra/typeorm/transformers/toNumber'

@Entity('payout_transformers')
class PayoutTransformer {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column('int4', { transformer: toNumber() }) // @acusa
  amount_cents: number

  @Column('bigint', { transformer: toNumber() })
  fee_cents: number
}

export default PayoutTransformer
