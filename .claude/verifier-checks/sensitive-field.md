# check `sensitive-field` — campo sensível [BE-010, BE-021]

> Acende quando uma linha **adicionada** traz `api_key`, `private_key`, `_secret`, `_pem`,
> `password` ou `crypt`.
>
> ⚠️ **`_key` solto NÃO acende**, de propósito: casava `rack_key`, `stock_key` e afins, e a
> etiqueta ia a 100% das features (T-11). Se aparecer um segredo com outro sufixo
> (`signature_key`, `*_token`), a regra em `diff-classify.py` é que precisa crescer — este texto
> não cobre o que o script não acende.

## BE-010 — criptografia no Create **E** no Update

O `CryptoProvider` (AES-256-GCM, token `'CryptoProvider'`) é injetado nos dois services. Esquecer o
Update é o erro: o registro nasce cifrado e é sobrescrito em claro na primeira edição.

```typescript
// só re-criptografar se veio preenchido — senão "sem alteração" vira "apagar"
if (api_key !== undefined && api_key !== '') {
  reg.api_key = this.cryptoProvider.encrypt(api_key)
}
```

## BE-021 — `leftJoinAndSelect` vaza o que o `@Exclude()` protege

A entity marca o campo com `@Exclude()`, mas o `class-transformer` só age quando o controller
responde com `classToClass(...)`. Um `leftJoinAndSelect` que traz a entity sensível num controller
que responde `response.json(reg)` cru **vaza o campo inteiro**.

Confira: (a) a entity tem `@Exclude()`; (b) **todo** controller que retorna essa entity — inclusive
por join, inclusive em outro módulo — passa por `classToClass`.

## Onde mais olhar

- O campo aparece em log, em mensagem de erro, ou no payload de um webhook?
- O `.env.example` ganhou a variável, sem o valor real?

**Veredito**: Update sem criptografia, ou entity com `@Exclude()` respondida sem `classToClass` =
bloqueante.
