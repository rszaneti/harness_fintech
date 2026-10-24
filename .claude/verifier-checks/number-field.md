# check `number-field` — campo numérico ou conversor [FE-022]

> Acende quando o diff toca `type="number"` ou uma função conversora (`toNumber*`, `parse*Number`).

O `handleChange` do Formik **converte para número** o valor de todo input `type="number"`. Um campo
declarado `string` chega ao submit como número, e o `tsc` não pega: quem quebra a promessa é a
biblioteca, em runtime. Se o corpo do conversor chamar método de string (`.trim()`, `.replace()`),
lança `TypeError` dentro do `try` do salvamento e a chamada seguinte nunca acontece — a tela grava
metade e o operador vê "não salvou" sem saber o quê.

**Leia o CORPO da função, não a assinatura.** Três armadilhas, todas cometidas na spec 069:

1. **Mesma assinatura não é mesmo comportamento.** Cinco arquivos declaravam `(value: string)`; só
   dois chamavam método de string. O acusado pelo nome era o único seguro por construção.
2. **O campo `type="number"` pode estar num componente FILHO.** Grep no arquivo do pai devolve zero
   e mente (AG-017). Rode `grep -rn 'type="number"' <pasta do componente>` — pai **e** filhos — e
   siga o `onChange` de cada acerto.
3. **A condição de segurança é "o `onChange` NÃO é o do Formik"**, não "não há campo numérico".
   `HTMLInputElement.value` é sempre string; quem coage é o Formik. Registrar o motivo errado deixa
   armadilha para quem trocar o callback depois.

**Veredito**: conversor que chama método de string alimentado por campo `type="number"` do Formik =
bloqueante.
