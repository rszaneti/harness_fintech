#!/usr/bin/env python3
"""
idempotency-required.py — hook pós-edição: rota POST/PUT/PATCH exige ensureIdempotency ou isenção com motivo (spec 001, RN-13/RN-15).

Ponto de entrada fino: a regra mora em `financial_rules.py`, junto com as outras três, e é a mesma
que o `check-module.py` (check `financeiro`) e o `scaffold.py --self-test static` usam.
Chamado pelo `post-edit-check.sh` para todo .ts de workspace.

Uso:
  idempotency-required.py <arquivo> [--as <caminho-virtual>]   imprime os achados; exit 1 se houver
  idempotency-required.py --self-test                          fixtures de .claude/scripts/tests/idempotency-required/
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Exit 1 = ACHADO. Biblioteca que não importa (erro de sintaxe, JSON de workspaces quebrado) sai
    # 3: o post-edit-check.sh trata qualquer código ≠ 0/1 como "hook NÃO RODOU", que também reprova
    # — e com o rótulo certo (achado BAIXA da 1ª auditoria da spec 001).
    try:
        import financial_rules  # noqa: E402
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"idempotency-required: financial_rules não carregou ({type(e).__name__}: {e})\n")
        sys.exit(3)
    sys.exit(financial_rules.cli("idempotency-required", sys.argv[1:]))
