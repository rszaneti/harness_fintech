import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm'

// Dinheiro NUNCA é @Column('numeric') nem type: 'decimal' — é bigint em centavos (AG-013: este
// comentário cita o antipadrão e não pode acusar o arquivo).
@Entity('charges')
class Charge {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column('bigint')
  amount_cents: string

  @Column('int4')
  installments: number
}

export default Charge
