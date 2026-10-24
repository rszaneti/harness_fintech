// Enum – <descrição: estágios do fluxo | status operacional> de __Entity__
// ⚠️ Enum que ESPELHA valores de outro enum (mesmo conceito, recorte diferente) exige função de
// travessia explícita e teste no valor que diverge (BE-015).
export enum __Entity__<Tipo> {
  // __VALORES__ — exemplo declarado (multiplicar e ajustar):
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  CANCELLED = 'CANCELLED',
}
