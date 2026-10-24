#!/usr/bin/env python3
"""
code-only.py — imprime um arquivo .ts/.tsx SEM os comentários, preservando o número das linhas.

Existe porque o filtro de comentário do hook era `grep -vE '^[[:space:]]*(//|\\*|/\\*)'` (só linha
inteira) ou um `sed` de fim de linha — e nenhum dos dois cobre o comentário JSX `{/* … */}` nem o
bloco `/* … */` de várias linhas. A consequência é a AG-013 ao contrário: o arquivo que ADVERTE
contra o antipadrão é reprovado por exibi-lo. Foi assim que as fixtures da spec 087 derrubaram a
regra FE-009 do hook.

⚠️ Este arquivo é uma CASCA. A implementação é o `strip_comments_keep_lines` do `scaffold.py`
(autômato que rastreia estado de string), e tem de continuar sendo — na 1ª rodada de correção da
087 eu troquei o corpo no `check-module.py` e **esqueci aqui**, deixando as duas cópias
divergentes: FE-009, FE-024 e BE-023 continuavam deixando passar `accept="image/*"` seguido do
padrão proibido, em silêncio, no nível 1 da hierarquia. Reimplementar este filtro é repetir isso.

Uso: python3 code-only.py <arquivo>   → stdout, uma linha para cada linha do original
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scaffold"))

try:
    from scaffold import strip_comments_keep_lines  # noqa: E402
except Exception as e:  # pragma: no cover - ambiente sem o scaffold
    print(f"code-only: não consegui importar o scaffold ({e})", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: code-only.py <arquivo>", file=sys.stderr)
        return 64
    raw = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    print(strip_comments_keep_lines(raw))
    return 0


if __name__ == "__main__":
    sys.exit(main())
