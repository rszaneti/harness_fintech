# check `contract` — a forma de uma resposta mudou [AG-022, FE-025]

> Acende quando o diff **REMOVE um campo** (`- campo: tipo`) de um arquivo em `dtos/` ou
> `*.types.ts` — a forma da resposta que MUDOU.
>
> ⚠️ **Não acende** para campo acrescentado nem para `*.service.ts`: acrescentar é o dia a dia e
> tocar service acendia em quase toda feature (T-11). O que a AG-022 pega é o campo que SUMIU.
> Campo renomeado aparece como removido + adicionado, e acende.
>
> O `check-module.py --contract` compara por NOME e reporta INFO. O julgamento de **que lado
> corrige** é seu — e é o que o script não faz.

## AG-022 — o tipo do frontend é uma AFIRMAÇÃO, não uma verificação

Quando o backend muda a forma da resposta, **nada quebra**: `tsc` limpo, ESLint limpo, e os testes
de componente mockam o service. A funcionalidade some em silêncio.

Caso real (spec 074): `IDonorFreezingTestReserve` declarava `test_units_quantity`, `…_consumed`,
`…_remaining` e `warning`; o backend passara a responder `has_test_batch`, `test_units_total`,
`test_units_in_stock`, `test_units_used` — e **nenhum `warning`**. O aviso da RN-02 nunca aparecia
no modal, porque `testReserve.warning` era `undefined`.

**Compare campo a campo** o DTO do backend com a interface do frontend. Não basta procurar o termo
velho: naquele caso o defeito só apareceu na comparação, porque os nomes novos não eram
pesquisáveis a partir dos antigos.

## FE-025 — espelhar a tela não espelha o contrato da rota

O payload de create/update tem de bater com o `[Segments.BODY]` da rota que ele chama. Copiar a
tela de outro módulo traz o payload do outro módulo, e o 400 só aparece com o servidor de pé.

⚠️ **Limite do script**: ele compara contra a UNIÃO de todos os `[Segments.BODY]`, então acusa só o
campo que não existe em rota nenhuma. Campo que existe **noutra** rota passa. Resultado limpo não
prova contrato certo — para a rota que a feature toca, confira à mão.

## De que lado corrigir

Nem sempre é o frontend. Na 074 a frase de aviso voltou para o **backend**: montá-la na tela
duplicaria a redação da regra em dois lugares que ninguém compara.

**Veredito**: campo que a tela lê e o backend não envia (ou vice-versa) = bloqueante, com o lado da
correção justificado.
