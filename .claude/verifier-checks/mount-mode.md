# check `mount-mode` — o modo de montagem mudou [FE-020]

> Acende quando o diff, num `.tsx`: traz ou tira **`TabPanel`**; traz ou tira **`display…none`**;
> ou **REMOVE** um render condicional (`? <`, `&& <`). **Esta família reprovou QUATRO rodadas na
> spec 069 e nenhum gate mecânico a alcança.**
>
> ⚠️ **Não acende** para render condicional ACRESCENTADO nem para `display` genérico: `? <` é todo
> React e acendia em 90% das features (T-11). O sinal é a TROCA de modo, não a presença de
> condicional.

Trocar **renderização condicional ⇄ `display` ⇄ aba de `TabPanel`** (ou mover um componente para
dentro de um `TabPanel`) muda quando o componente **monta e desmonta**. Liste CADA `useState` e
`useRef` do componente afetado **e do pai**, e classifique:

| Origem do estado | O que acontece ao desmontar |
|---|---|
| vem do servidor | recarrega sozinho — seguro |
| derivado de props | recalcula — seguro |
| **construído por INTERAÇÃO** | **morre, e ninguém o traz de volta** |

O terceiro grupo é o perigoso. Duas perguntas, nos dois sentidos:

1. **Que estado foi construído por interação e não é reconstruído na MONTAGEM?** Ele precisa
   subir para um componente que sobrevive, ser reconstruído num efeito de montagem, ou ter o
   requisito de sobrevivência **revogado por escrito**.
2. O inverso: algum `useEffect` que lê dado escrito em OUTRO passo/aba passou a rodar no mount do
   **pai**, antes de o dado existir? Efeito assim não pode dividir `useEffect` com os que leem
   dado estático.

⚠️ `<select>` nativo com `value` sem `<option>` correspondente **renderiza vazio**. Tela em branco
enquanto o payload leva o id certo é pior que erro: ninguém procura o defeito onde ele está.

**Veredito**: estado do terceiro grupo sem destino = **bloqueante**.
