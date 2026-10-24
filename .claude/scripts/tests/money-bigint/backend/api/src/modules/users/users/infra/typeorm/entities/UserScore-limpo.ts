import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm'

// `users` não é contexto financeiro: decimal aqui não é dinheiro (escopo da RN-11).
@Entity('user_scores')
class UserScore {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column('numeric', { precision: 5, scale: 2 })
  score: number
}

export default UserScore
