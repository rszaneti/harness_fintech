#!/usr/bin/env python3
"""
check-ui-v2-refs.py — confere que tudo o que as skills citam do padrão visual v2 EXISTE no código.

Spec 086 (RN-04). Motivo: no harness gêmeo, a skill de frontend mandava usar um componente que não
existia mais, e o mapa de inputs ensinava o oposto do padrão — ninguém percebeu porque documento
não compila. Aqui, todo identificador e toda cor citados nas skills são conferidos contra
`<frontend>/src/styles/global_v2.tsx`, `globalMaterialUi_v2.tsx` e `src/theme.ts` do workspace
`operador` de `.claude/workspaces.json` (spec 001) — o padrão v2 foi herdado do ERP de origem e é
revisto nas specs 010/011. Sem o workspace, o script NÃO RODOU: exit 65, não aprovação (AG-019).

Uso:
  python3 .claude/scripts/check-ui-v2-refs.py            # audita as skills
  python3 .claude/scripts/check-ui-v2-refs.py <arquivo>… # audita arquivos avulsos (rascunho)

Exit 0 = tudo o que é citado existe · 1 = há citação sem respaldo no código · 65 = workspace ausente.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import workspaces  # noqa: E402

FE_WS = "operador"
FE = workspaces.path_of(FE_WS, ROOT) / "src"
GLOBAL_V2 = FE / "styles/global_v2.tsx"
MUI_V2 = FE / "styles/globalMaterialUi_v2.tsx"
THEME = FE / "theme.ts"

DEFAULT_TARGETS = [
    ROOT / ".claude/skills/ui-v2",
    ROOT / ".claude/skills/frontend-module/SKILL.md",
]

# Identificador entre crases que "parece componente do v2": Css*, ou PascalCase.
IDENT_RE = re.compile(r"`([A-Z][A-Za-z0-9_]*)`")
HEX_RE = re.compile(r"`?(#[0-9a-fA-F]{6})\b")
PLACEHOLDER_LINE_RE = re.compile(r"__[A-Za-z][A-Za-z_]*__")

# Nomes citados que NÃO são exports do v2 — precisam estar aqui, com o motivo, para não virarem
# desculpa silenciosa. Se um nome novo entrar sem motivo, o script acusa e alguém decide.
ALLOWED = {
    # React / libs
    "React", "Fade", "Formik", "Form", "Yup", "CircularProgress", "Modal", "Backdrop",
    "DataGrid", "DataGridPro", "DataGridPremium", "GridActionsCellItem", "GridColDef",
    "GridSortModel", "GridRowModel",
    "GridRenderCellParams", "GridCellEditStopReasons", "Drawer", "Collapse", "AppBar",
    "TabPanel", "Link", "Route", "Switch", "Autocomplete", "TextField", "Button", "Chip",
    "Checkbox", "Radio", "RadioGroup", "FormControl", "FormControlLabel", "FormLabel",
    "Tab", "Tabs", "ThemeProvider", "LocalizationProvider", "AdapterDateFns",
    "InputLabelProps", "SelectProps", "InputBase", "FormikErrors", "FormModel",
    "TypeError", "MdUpload", "MdEdit", "MdDelete", "MdSearch", "MdClear", "MdAddCircle",
    # componentes e hooks do app que não moram nos dois arquivos de estilo
    "CurrencyInput", "MuiXLicense", "KanbanCard", "CardTooltip", "AuthLayout", "DefaultLayout",
    "Header", "ErrorContext", "AuthContext", "ErrorMessage", "WORKFLOW_STAGE_COLORS",
    "CLINIC_METRICS_LIMIT", "STATUS_BOOLEAN_OPTIONS", "UF_LIST",
    # telas canônicas e módulos citados por nome
    "ClinicsList", "ClinicForm", "ClinicFormRegisterData", "ClinicFormContactsList",
    "ClinicFormContactRegister", "ClinicFormSampleEmailModal", "ClinicFormSampleEmailsList",
    "ClinicModalContext", "PatientsWorkflow", "DonorsWorkflow", "TentantsWorkflow",
    "TentantFormWorkflow",
    "CrmLeadsWorkflow", "Clinic", "Contact", "Contato", "Cadastrar", "Voltar", "Salvar",
    "Clinics", "Contacts", "ClinicContact",
    # símbolos do harness (scaffold.py)
    "FRONTEND_DEST", "BACKEND_DEST",
    # v1 citado como legado / o que NÃO existe no v2 (a menção é a regra)
    "CssBox", "CssBoxTable", "CssBoxModalForm", "CssAppBar", "CssIconButtonTableHeader",
    "CssDatePicker", "CssTextareaAutosize", "CssDateField", "UlFormCol1", "UlFormCol2",
    "UlFormCol3", "UlFormCol4", "Buttons", "Paragraph", "CssWithoutBorder",
    # tipos e utilitários genéricos
    "Record", "Partial", "Omit", "Promise", "Date", "File", "FormData", "TypeScript",
    "PascalCase", "UUID", "JWT", "API", "HTTP", "PT", "BR", "WCAG", "AA", "MUI", "CSS",
    "DOM", "JSX", "ID", "FK", "PK", "DTO", "SQL", "ILIKE", "CRUD", "CEP", "CNPJ", "CPF",
    "UF", "ASC", "DESC", "Joi", "Segments", "Express", "TypeORM", "PostgreSQL", "Postgres",
    "Redis", "Docusign", "Azure", "S3",
}

# Componentes que SÓ existem no v1. Citá-los é legítimo em nota de equivalência ("não existe no v2");
# mandar usá-los é a regressão que esta skill existe para impedir. O script não sabe a diferença —
# por isso AVISA, para quem revisa ler cada menção.
V1_ONLY = {
    "CssBox", "CssBoxTable", "CssBoxModalForm", "CssAppBar", "CssIconButtonTableHeader",
    "CssDatePicker", "CssTextareaAutosize", "CssDateField", "UlFormCol1", "UlFormCol2",
    "UlFormCol3", "UlFormCol4", "CssWithoutBorder",
}

# Hex citados que não vêm do tema nem dos tokens — só cores de EXEMPLO de domínio, com motivo.
ALLOWED_HEX = {
    "#facc15",  # amarelo de etapa de board: exemplo do pior caso de contraste (4.58:1)
}


def exports_of(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    names = set(re.findall(r"^export (?:const|function|interface|type|class) ([A-Za-z0-9_]+)",
                           text, re.M))
    for m in re.finditer(r"^export \{([^}]*)\}", text, re.M):
        names |= {n.strip().split(" as ")[-1] for n in m.group(1).split(",") if n.strip()}
    return names


def local_consts_of(path: Path) -> set[str]:
    """Tokens `const NOME = '#...'` não exportados (FIELD_BORDER, LABEL_COLOR…)."""
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"^const ([A-Z][A-Z0-9_]+) =", text, re.M))


def hexes_of(paths: list[Path]) -> set[str]:
    out: set[str] = set()
    for p in paths:
        out |= {h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", p.read_text(encoding="utf-8"))}
    return out


def rel(p: Path) -> str:
    """Caminho relativo à raiz quando possível — um alvo avulso pode estar fora dela."""
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def md_files(targets: list[Path]) -> list[Path]:
    out: list[Path] = []
    for t in targets:
        if t.is_dir():
            out += sorted(t.rglob("*.md"))
        elif t.exists():
            out.append(t)
    return out


def main(argv: list[str]) -> int:
    if not FE.parent.is_dir():
        print(f"⚠️ workspace {FE_WS} ({FE.parent.relative_to(ROOT)}) não existe neste checkout — nada "
              f"conferido; nasce na spec {workspaces.load()[FE_WS]['spec']}", file=sys.stderr)
        return 65
    for p in (GLOBAL_V2, MUI_V2, THEME):
        if not p.exists():
            print(f"❌ fonte ausente: {p}", file=sys.stderr)
            return 1

    known = exports_of(GLOBAL_V2) | exports_of(MUI_V2) | local_consts_of(GLOBAL_V2) | local_consts_of(MUI_V2)
    known_hex = hexes_of([GLOBAL_V2, MUI_V2, THEME])

    targets = [Path(a) for a in argv] if argv else DEFAULT_TARGETS
    files = md_files(targets)
    if not files:
        print("❌ nenhum .md para auditar", file=sys.stderr)
        return 1

    problems: list[str] = []
    v1_mentions: list[str] = []
    checked_idents = 0
    checked_hex = 0

    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            # Numa linha que documenta PLACEHOLDER do scaffold, o que se cita é o VALOR DE EXEMPLO
            # do módulo canônico (`Clinics`, `ClinicContact`…). Descartamos só os tokens da coluna de
            # exemplo — não a linha inteira, senão uma citação errada ali passaria calada.
            #
            # ⚠️ RESÍDUO CONHECIDO (auditoria da 086, 2ª rodada): citação errada que esteja NA
            # PRÓPRIA coluna de exemplo continua passando — é exatamente a coluna descartada. É onde
            # alguém escreveria `CssDateField` como modelo. Revisar essa coluna à mão ao editar a
            # tabela de placeholders; o resto da linha é conferido.
            if PLACEHOLDER_LINE_RE.search(line):
                line = re.sub(r"\|[^|]*\|\s*$", "|", line)
            for ident in IDENT_RE.findall(line):
                checked_idents += 1
                if ident in V1_ONLY:
                    v1_mentions.append(f"{rel(f)}:{n} — `{ident}`")
                    continue
                if ident in known or ident in ALLOWED:
                    continue
                problems.append(f"{rel(f)}:{n} — `{ident}` não existe no v2 "
                                f"(nem consta da lista de exceções do script)")
            for hx in HEX_RE.findall(line):
                checked_hex += 1
                if hx.lower() in known_hex or hx.lower() in ALLOWED_HEX:
                    continue
                problems.append(f"{rel(f)}:{n} — cor {hx} não existe em "
                                f"theme.ts nem nos tokens do v2")

    print(f"check-ui-v2-refs: {len(files)} arquivo(s), {checked_idents} identificador(es) e "
          f"{checked_hex} cor(es) conferidos contra o código")
    if v1_mentions:
        print(f"\n⚠️ {len(v1_mentions)} menção(ões) a componente do v1 — legítimas só em nota de "
              f"equivalência ou de 'não existe no v2'. O script prova EXISTÊNCIA, não direção: "
              f"leia cada uma e confirme que não está mandando usar.")
        for m in v1_mentions:
            print("  " + m)
    if problems:
        print(f"\n❌ {len(problems)} citação(ões) sem respaldo no código:")
        for p in problems:
            print("  " + p)
        return 1
    print("✅ tudo o que é citado existe no código")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
