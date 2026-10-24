# check `removal` — a feature REMOVE algo [AG-017]

> Acende quando o diff remove linhas com um identificador que não aparece mais em nenhum workspace.

**Grep do texto NOVO confirma presença, jamais ausência.** Conferir uma remoção pelo termo que
entrou no lugar é o erro: o termo velho sobrevive onde ninguém olhou.

## O que fazer

1. `grep -rniE "<termo_velho1>|<termo_velho2>" <workspace>/src` — **o termo VELHO**, no workspace
   inteiro, não só na pasta da feature.
2. Conferir as **duas pontas da cascata**:
   - quem **consumia** o que saiu;
   - quem **produzia** algo que só existia para alimentá-lo (campo de retorno de hook, state,
     acumulador, constante).
3. Classificar **cada ocorrência** em: (a) código legítimo de outra feature, (b) comentário
   histórico honesto — que explica a remoção, (c) **defeito a corrigir**. Nenhuma pode ficar em (c).

⚠️ Comentário que **afirma o mecanismo como vigente** é (c), não (b). Leia com AG-013: menção dentro
de comentário que explica a remoção é legítima.

## O caso que a lesson AG-023 acrescenta

Relação/campo removido do repositório "dono" mas ainda lido por **outro repositório que acessa o
mesmo agregado por outra porta** — a tela que lê por lá continua quebrada, e o grep do módulo não
alcança.

**Veredito**: qualquer ocorrência em (c) = bloqueante.
