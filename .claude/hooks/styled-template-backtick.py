#!/usr/bin/env python3
r"""
[FE-023] Crase dentro de comentario CSS de um styled-component.

Num `styled.div\`...\`` o comentario /* */ nao e comentario de JS: e TEXTO do
template literal. Uma crase ali FECHA o template no meio, e o resto do arquivo
passa a ser lido como codigo.

O ESLint pega, mas a mensagem engana: sai `Parsing error: ',' expected` apontando
a linha do comentario, o que manda procurar erro de sintaxe em objeto/argumento
-- que e onde nao esta. Este script existe para dar a causa, nao o sintoma.

Deteccao: dentro de um template de styled, ao encontrar `/*`, procura o primeiro
`*/` ou crase. Se a crase vier antes, ela fecha o template dentro do comentario.
Sem falso positivo: crase em comentario que o `*/` fecha antes nao existe -- se a
crase aparece primeiro, o template ja acabou ali.

Uso: styled-template-backtick.py <arquivo>   (imprime achados; silencio = ok)
"""

import re
import sys

# `styled.div`, `styled.div<Props>`, `styled(X)`, `styled(X).attrs(...)`,
# `css`, `createGlobalStyle` -- imediatamente antes da crase de abertura.
OPENER = re.compile(
    r"(?:styled\.[A-Za-z][A-Za-z0-9]*(?:<[^`]*?>)?"
    r"|styled\([^()`]*\)(?:\.attrs\([^()`]*\))?"
    r"|\bcss"
    r"|\bcreateGlobalStyle)\s*$"
)


def scan(src):
    findings = []
    i, n, line = 0, len(src), 1
    depth = 0  # profundidade de template de styled aberto

    while i < n:
        c = src[i]

        if c == "\n":
            line += 1
            i += 1
            continue

        if depth == 0:
            # Comentario de linha
            if src.startswith("//", i):
                j = src.find("\n", i)
                i = n if j < 0 else j
                continue
            # Comentario de bloco (aqui e comentario de JS de verdade)
            if src.startswith("/*", i):
                j = src.find("*/", i + 2)
                if j < 0:
                    break
                line += src.count("\n", i, j)
                i = j + 2
                continue
            # String
            if c in "\"'":
                q, i = c, i + 1
                while i < n and src[i] != q:
                    if src[i] == "\\":
                        i += 2
                        continue
                    if src[i] == "\n":
                        line += 1
                    i += 1
                i += 1
                continue
            # Abertura de template
            if c == "`":
                if OPENER.search(src[max(0, i - 240) : i]):
                    depth = 1
                i += 1
                continue
            i += 1
            continue

        # ── dentro do template de um styled ──────────────────────────────────
        # Interpolacao: ali dentro e JS de novo, nao CSS.
        if src.startswith("${", i):
            i += 2
            braces = 1
            while i < n and braces:
                ch = src[i]
                if ch == "\n":
                    line += 1
                elif ch in "\"'":
                    q, i = ch, i + 1
                    while i < n and src[i] != q:
                        if src[i] == "\\":
                            i += 2
                            continue
                        if src[i] == "\n":
                            line += 1
                        i += 1
                elif ch == "{":
                    braces += 1
                elif ch == "}":
                    braces -= 1
                i += 1
            continue

        # Comentario CSS: e AQUI que a crase mata.
        if src.startswith("/*", i):
            j = i + 2
            start_line = line
            while j < n:
                if src[j] == "\\":
                    # Crase ESCAPADA (\`) e legitima: nao fecha o template, e e
                    # como global_v2.tsx cita `typography.htmlFontSize` no reset.
                    j += 2
                    continue
                if src[j] == "\n":
                    line += 1
                elif src[j] == "`":
                    findings.append((line, start_line))
                    break
                elif src.startswith("*/", j):
                    j += 1
                    break
                j += 1
            i = j + 1
            continue

        if src[i] == "\\":
            i += 2
            continue

        if c == "`":
            depth = 0

        i += 1

    return findings


def main():
    if len(sys.argv) < 2:
        return 0
    try:
        with open(sys.argv[1], encoding="utf-8") as fh:
            src = fh.read()
    except OSError:
        return 0

    for at, opened in scan(src):
        print(
            f"  linha {at}: crase dentro do comentario CSS aberto na linha {opened}. "
            f"Ela FECHA o template do styled ali. Escreva o nome sem crase, ou "
            f"escape (\\`) -- so os JSDoc de FORA do template usam crase solta."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
