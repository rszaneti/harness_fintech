#!/usr/bin/env python3
"""
[FE-021] Implementacao de mock dentro da factory do `jest.mock` (CRA + resetMocks).

O Create React App liga `resetMocks: true`
(react-scripts/scripts/utils/createJestConfig.js:68). Implementacao declarada
DENTRO da factory do `jest.mock(...)` e APAGADA antes de cada teste, e o service
passa a devolver `undefined`. O spec parece configurado e nao esta -- o componente
quebra em todo lugar que consome aquele service, com erros sem nenhuma relacao com
o que se investiga.

A verificacao e SINTATICA e por isso vive no gate mecanico: `.mockResolvedValue(`
e irmaos, entre o `jest.mock(` e o parentese que o fecha. Fora dessa janela --
`beforeEach`, corpo do `it` -- o mesmo texto e CORRETO e nao e sinalizado, o que um
grep simples nao conseguiria distinguir.

⚠️ COMENTARIOS SAO APAGADOS ANTES DE QUALQUER ANALISE (BE-001 / AG-013). Sem isso,
o comentario que ADVERTE contra o erro dispara o proprio guard, e o autor precisa
apagar a prosa que ensina a regra para conseguir salvar o arquivo. Este hook foi
REPROVADO na auditoria exatamente por isso, com a sonda `c1` abaixo. E o mesmo
tratamento que o `post-edit-check.sh` ja aplica nas checagens de migration.

⚠️ RUIDO DE PARENTESES degrada para falso NEGATIVO, nunca positivo. Nao
tokenizamos JavaScript: contamos parenteses. Num arquivo sintaticamente valido os
parenteses reais se equilibram, entao um `(` a mais vindo de string deixa `depth`
travado acima de zero e o laco termina SEM `yield` -- o guard para de guardar
aquele arquivo em vez de bloquea-lo por engano. Para um hook que BARRA EDICAO, e a
direcao certa de errar. O custo e silencioso: falso negativo nao avisa.

⚠️ ASPA IMPAR E A EXCECAO, e degrada para o lado POSITIVO. Uma aspa sem par ANTES
do `jest.mock` -- tipicamente num regex, `/don't/i` -- deixa o scanner preso em
estado de string, e em estado de string comentario nenhum e apagado dali para a
frente: a prosa volta a disparar o guard (sonda `c8`). Nao esta fechado de
proposito: exige a CONJUNCAO de aspa impar antes do mock E comentario dentro da
factory citando um dos oito metodos. Nenhum spec do workspace tem a primeira --
em portugues os regex de teste nao levam apostrofo. E risco residual CONHECIDO,
nao armadilha a espera. Fecha-lo custaria ignorar aspas entre `/` e `/` na mesma
linha; documentar foi julgado suficiente para a probabilidade envolvida.

⚠️ NAO REORDENE OS RAMOS DE `strip_comments`. `state == '//'` e testado ANTES de
`char in ("'", '"', '`')`, e e SO por isso que `// don't` nao envenena o estado de
string. Invertida a ordem, o apostrofo de um comentario abriria string e o guard
pararia de guardar o resto do arquivo -- em silencio, sem teste que acuse.
Rode `--self-test` depois de mexer aqui.

Sondas de regressao (guard promovido sem caso NEGATIVO foi o que produziu a
reprovacao):

  c1 NEGATIVA -- comentario dentro da factory citando `.mockResolvedValue()`
                 com `jest.fn()` vazio: NAO pode acusar.
  c2 POSITIVA -- `jest.fn().mockResolvedValue({})` na factory: acusa 1.
  c3 NEGATIVA -- `.mockResolvedValue()` no `beforeEach`: NAO pode acusar.
  c4 NEGATIVA -- `jest.mock` com um argumento so.
  c5 NEGATIVA -- `jest.mock(` citado dentro de comentario.
  c6 POSITIVA -- factory com closures aninhadas: acusa SO a linha da violacao.
  c7 NEGATIVA -- `(` dentro de string (URL): demonstra a degradacao para
                 falso negativo descrita acima.
  c8 XFAIL    -- aspa impar antes do mock + comentario na factory: acusa, e ESTA
                 ERRADO. Fica registrada como limitacao conhecida, nao como bug
                 aberto -- ver o paragrafo da aspa impar.

Uso: jest-mock-factory.py <arquivo>
     jest-mock-factory.py --self-test    (roda as sondas acima)
Saida: uma linha por ocorrencia; vazia quando nao ha nenhuma.
"""

import re
import sys

METHODS = (
    '.mockResolvedValue(',
    '.mockResolvedValueOnce(',
    '.mockReturnValue(',
    '.mockReturnValueOnce(',
    '.mockRejectedValue(',
    '.mockRejectedValueOnce(',
    '.mockImplementation(',
    '.mockImplementationOnce(',
)


def strip_comments(source):
    """
    Troca comentarios por espacos, PRESERVANDO os `\\n`.

    Preservar a quebra de linha e o que mantem o numero da linha reportada igual
    ao do arquivo original. Percorremos caractere a caractere em vez de usar
    regex porque `'https://exemplo'` dentro de uma string NAO e comentario --
    uma regex ingenua comeria o resto da linha e criaria o falso negativo que
    este cuidado existe para evitar.
    """
    out = []
    state = None  # None | "'" | '"' | '`' | '//' | '/*'
    index = 0
    length = len(source)

    while index < length:
        char = source[index]
        nxt = source[index + 1] if index + 1 < length else ''

        if state in ("'", '"', '`'):
            out.append(char)
            if char == '\\' and index + 1 < length:
                out.append(nxt)
                index += 2
                continue
            if char == state:
                state = None
            index += 1
            continue

        if state == '//':
            if char == '\n':
                out.append('\n')
                state = None
            else:
                out.append(' ')
            index += 1
            continue

        if state == '/*':
            if char == '*' and nxt == '/':
                out.append('  ')
                state = None
                index += 2
                continue
            out.append('\n' if char == '\n' else ' ')
            index += 1
            continue

        if char == '/' and nxt == '/':
            state = '//'
            out.append('  ')
            index += 2
            continue

        if char == '/' and nxt == '*':
            state = '/*'
            out.append('  ')
            index += 2
            continue

        if char in ("'", '"', '`'):
            state = char

        out.append(char)
        index += 1

    return ''.join(out)


def spans(source):
    """Intervalos [inicio, fim) de cada chamada `jest.mock(...)`, por parenteses."""
    for match in re.finditer(r'\bjest\.mock\s*\(', source):
        depth = 0
        index = match.end() - 1

        while index < len(source):
            char = source[index]

            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    yield match.start(), index
                    break

            index += 1


# ---------------------------------------------------------------------------
# Sondas de regressao, EXECUTAVEIS.
#
# ⚠️ ELAS VIVEM AQUI, e nao so no docstring, porque este script foi corrigido
# DUAS VEZES EM DUAS RODADAS de auditoria. Sonda descrita em prosa e relida;
# sonda embutida e RODADA. `--self-test` sai != 0 quando alguma diverge.
# ---------------------------------------------------------------------------

PROBES = (
    (
        'c1',
        "jest.mock('../x', () => ({\n"
        '  __esModule: true,\n'
        '  // nao declare .mockResolvedValue() aqui\n'
        '  buscar: jest.fn(),\n'
        '}))\n',
        [],
    ),
    (
        'c2',
        "jest.mock('../x', () => ({\n"
        '  __esModule: true,\n'
        '  buscar: jest.fn().mockResolvedValue({}),\n'
        '}))\n',
        [3],
    ),
    (
        'c3',
        "jest.mock('../x', () => ({ __esModule: true, buscar: jest.fn() }))\n"
        'beforeEach(() => {\n'
        '  ;(buscar as jest.Mock).mockResolvedValue({})\n'
        '})\n',
        [],
    ),
    ('c4', "jest.mock('../x')\nbeforeEach(() => { m.mockResolvedValue(1) })\n", []),
    (
        'c5',
        "// exemplo: jest.mock('../x', () => ({ y: jest.fn().mockResolvedValue(1) }))\n"
        'beforeEach(() => { m.mockResolvedValue(1) })\n',
        [],
    ),
    (
        'c6',
        "jest.mock('../x', () => ({\n"
        '  __esModule: true,\n'
        '  buscar: jest.fn(() => ({ nested: (a) => a })),\n'
        '  outro: jest.fn().mockReturnValue({ z: (b) => b }),\n'
        '}))\n'
        'beforeEach(() => { ;(buscar as jest.Mock).mockResolvedValue({}) })\n',
        [4],
    ),
    (
        'c7',
        "const url = 'https://exemplo.com/a(b'\n"
        "jest.mock('../x', () => ({ __esModule: true, buscar: jest.fn() }))\n"
        'beforeEach(() => { ;(buscar as jest.Mock).mockResolvedValue({}) })\n',
        [],
    ),
    (
        'c8-xfail',
        'const re = /don\'t/i\n'
        "jest.mock('../x', () => ({\n"
        '  __esModule: true,\n'
        '  // nao use .mockResolvedValue() aqui\n'
        '  fn: jest.fn(),\n'
        '}))\n',
        [4],  # ERRADO de proposito: limitacao conhecida da aspa impar.
    ),
)


def scan(source):
    """
    Ocorrencias em `source`, como `(linha, metodo)` ordenadas.

    ⚠️ E O UNICO LUGAR QUE ANALISA. `main` e `--self-test` chamam esta funcao --
    se a sonda testasse uma COPIA da logica, as duas poderiam divergir e a
    regressao passaria a proteger codigo que nao e o que roda no hook.
    """
    cleaned = strip_comments(source)
    found = []

    for start, end in spans(cleaned):
        window = cleaned[start:end]

        for method in METHODS:
            offset = window.find(method)

            while offset != -1:
                line = cleaned.count('\n', 0, start + offset) + 1
                found.append((line, method.strip('(').lstrip('.')))
                offset = window.find(method, offset + 1)

    return sorted(set(found))


def self_test():
    failures = 0

    for name, source, expected in PROBES:
        got = [line for line, _method in scan(source)]

        if got == sorted(expected):
            print(f'  ok   {name}: {got or "limpo"}')
        else:
            failures += 1
            print(f'  FALHA {name}: esperado {expected}, obtido {got}')

    if failures:
        print(f'\n{failures} sonda(s) divergiram.')
        return 1

    print(f'\n{len(PROBES)} sondas conferem.')
    return 0


def main():
    if len(sys.argv) < 2:
        return 0

    if sys.argv[1] == '--self-test':
        return self_test()

    path = sys.argv[1]

    try:
        with open(path, encoding='utf-8') as handle:
            raw = handle.read()
    except OSError:
        return 0

    for line, method in scan(raw):
        print(f'  linha {line}: {method} dentro da factory do jest.mock')

    return 0


if __name__ == '__main__':
    sys.exit(main())
