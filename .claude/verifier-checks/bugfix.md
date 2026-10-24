# check `bugfix` — a feature corrige um defeito [AG-011, AG-016]

> Acende quando a spec da feature descreve correção/defeito/regressão. As três perguntas abaixo
> reprovaram **três rodadas seguidas na spec 029**; nenhum gate mecânico as substitui.

## AG-011 — a correção trata um estado ALCANÇÁVEL?

1. **O estado que a correção trata é alcançável pelo fluxo que gerou o bug?**
   Ex.: filtrar requisição `CANCELADA` não resolve nada se o fluxo termina em `LAUDO_RECEBIDO`,
   que é terminal e não pode ser cancelado. Rastreie o fluxo **real**, não o do comentário.
2. **Quem ESCREVE o dado que a correção lê, e esse caminho é percorrido pela UI?**
   Uma marca gravada só por um endpoint que a tela não chama nunca existe em produção.
3. **Se a correção fosse revertida, qual asserção do teste falharia?**
   Se a resposta for "nenhuma", o teste acompanha a correção sem prová-la → **bloqueante**.
   Sinal de alerta: o cenário do teste precisa de um estado que o sistema não consegue atingir.

## AG-016 — correção de achado é CÓDIGO NOVO

A 2ª auditoria da spec 054 encontrou **dois defeitos ALTA introduzidos pelas próprias correções**
da 1ª. Corrigir sob pressão de fechar o gate faz tratar a correção como conserto pontual — mas ela
nasce sem teste, sem revisão e em cima de um sistema que o autor acabou de reler apressado.

- O teste que **falha com o defeito presente** vem ANTES da correção.
- Toda correção passa pelo mesmo crivo do código original — inclusive a pergunta 2 acima.
- Ao criar rota/service para tornar algo "alcançável", conferir que ficou mesmo: a correção do
  `files_id` da 054 criou uma rota que retornava 400 em 100% das chamadas.

**Veredito**: pergunta 3 sem resposta = bloqueante. Correção sem reauditoria = não concluída.
