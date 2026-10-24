# check `harness` — o diff muda o próprio verificador

> Acende quando o diff toca `.claude/scripts/`, `.claude/hooks/`, `.claude/agents/`,
> `.claude/scaffold/` ou `.claude/verifier-checks/`.
>
> **Existe por causa da primeira auditoria feita com este procedimento** (spec 087). A feature era
> de harness: nenhum `.ts/.tsx` de produto, zero etiquetas, `check-module.py` devolvendo
> `0 bloqueante` — e **quatro defeitos ALTA** dentro dos scripts que o passo 2 usa. O passo 2 não
> se audita. Um nível 1 da hierarquia que ninguém confere é o drift silencioso que esta linha de
> specs existe para matar.

## O passo 2 não vale aqui — leia o corpo do que mudou

Se o diff alterou `check-module.py`, `diff-classify.py`, um hook ou o `scaffold.py`, o resultado
verde do passo 2 **não é evidência**: a ferramenta que produziu o verde é o que está sob auditoria.
Leia as funções alteradas.

## As quatro perguntas

1. **O detector foi apontado para o caso CONHECIDO?** (AG-020) E para um **não-acerto**? Peça as
   duas evidências no registro de execução. Os quatro ALTA da 087 eram todos detectores que
   passavam no teste do autor e falhavam no caso real.
2. **A regra cobre os idiomas que o repositório usa de fato?** Exemplos verdadeiros daquela
   auditoria: `export default function X()` (11 telas) não casava com `^export default (\w+)`;
   `[Segments.QUERY]: Joi.object().keys({` (10 rotas) não casava com o regex do bloco literal.
   Uma amostra que não contém o idioma dominante não mede nada.
3. **A regra acusa o comentário que adverte contra ela?** (AG-013) Filtro de comentário que só
   cobre `//` reprova um aviso escrito em `/* */` ou em JSX — e o autor fica travado por um hook
   que ele não pode contornar (regra crítica 7 do `CLAUDE.md`). O filtro é o
   `strip_comments_keep_lines` do `scaffold.py`, num lugar só.
4. **O gate mecânico chegou a tocar nestes arquivos?** `verify.sh` cobre `.ts/.tsx` dos
   workspaces; `.py`, `.sh` e `.md` do harness passam sem lint, sem typecheck e sem teste. Exija do
   registro a prova que substitui: `py_compile`, `bash -n`, `--self-test`, e a validação por caso
   conhecido de cada checagem nova.

## Sentinela e legado

Regra nova que varre a base inteira: conte quantos arquivos ela acusa **hoje**. Se acusa centenas,
ou é um achado de verdade sobre o legado — e aí é INFO, inventário, não reprovação desta entrega —
ou o detector está errado. As duas leituras exigem número; nenhuma aceita "parece ok".

**Veredito**: detector sem caso conhecido validado, ou regra que reprova código correto = bloqueante.
