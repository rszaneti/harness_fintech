# check `enum` — enum novo ou alterado [BE-015]

> Acende quando o diff cria ou edita arquivo em **`enums/`** (backend).
>
> ⚠️ **Não acende para `constants/`**, de propósito: acendia em 100% das features de frontend, e
> etiqueta que acende sempre não classifica nada (medição da T-11, spec 087). O espelho do
> frontend é conferido **dentro** deste check, na seção abaixo.

## Enum que ESPELHA outro (mesmo conceito, recortes diferentes)

Se a feature cria um enum que repete valores de outro já existente, confira:

1. Existe uma **função de travessia explícita** entre os dois?
2. Ela é usada em **TODOS** os pontos de cruzamento — incluindo o **backfill da migration**?
3. Existe teste para o valor que **DIVERGE** entre os dois enums? Testar só o que coincide não
   prova nada.

É o tipo de erro que typecheck e lint não pegam: na fronteira, ambos são `string`.

## Espelho no frontend

O enum de `src/constants/` espelha o do backend e os **valores crus têm de bater exatamente** — é o
enum do backend que o Joi da rota usa em `.valid(...)`. No frontend moram só os rótulos de tela.
Sem opção sentinela ("Não informado"): ausência já é ausência, e um valor a mais obriga todo
consumidor a tratar dois "vazios" diferentes.

## Enum de identidade com carga inicial completa

[BE-019] Enum que identifica registros + seed que já preenche todos os valores = cadastro
impossível: não sobra valor para o usuário escolher.

**Veredito**: travessia ausente, ponto de cruzamento sem ela, ou ausência do teste do valor
divergente = bloqueante.
