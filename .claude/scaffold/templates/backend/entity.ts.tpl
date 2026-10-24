// Entity – modelo persistido da tabela __tabela__
import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  CreateDateColumn,
// @if !append_only
  UpdateDateColumn,
// @endif
} from 'typeorm'
// Com FK: acrescentar `ManyToOne, JoinColumn` ao import acima (fora daqui o ESLint acusa import sem uso).
// import { Exclude, Expose } from 'class-transformer' // ← apenas se houver campo sensível/computed

// __IMPORTS_RELACIONAMENTOS__
// import Contract from '@modules/contracts/contracts/infra/typeorm/entities/Contract'

@Entity('__tabela__')
class __Entity__ {
  @PrimaryGeneratedColumn('uuid')
  id: string

  // __FKS__ — exemplo:
  // @Column('uuid')
  // contracts_id: string
  //
  // @ManyToOne(() => Contract, (contract) => contract.__entity__)
  // @JoinColumn({ name: 'contracts_id' })
  // contract: Contract

  // __CAMPOS__ — campos do domínio. Regras:
  // - varchar: padrão 255 (não declarar length se 255) | text: sem length
  // - sensíveis (senha, api_key): adicionar @Exclude()
  // - computed (file_url): @Expose() get
  // Exemplo DECLARADO (multiplicar e ajustar — o módulo gerado precisa compilar):
  @Column('varchar')
  name: string

  @Column('bool', { default: true })
  status: boolean

  // --- auditoria (obrigatório em toda entity) ---
// @if append_only
  // Append-only (spec 001, RN-09): sem `user_updated`/`updated_at` — o registro nunca é alterado.
// @endif
  @Column('varchar', { nullable: true })
  user_created: string | null

// @if !append_only
  @Column('varchar', { nullable: true })
  user_updated: string | null

// @endif
  @CreateDateColumn({ type: 'timestamp' })
  created_at: Date
// @if !append_only

  @UpdateDateColumn({ type: 'timestamp' })
  updated_at: Date
// @endif
}

export default __Entity__
