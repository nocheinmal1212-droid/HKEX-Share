"""Evaluator arithmetic; operands are reviewed evidence, never detector inputs."""
from decimal import Decimal, localcontext, Inexact, Rounded
import re
from .common import require

DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
TOKEN = re.compile(r"^(?:[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]+)?$")


def decimal(value):
    require(isinstance(value, str) and bool(DECIMAL.fullmatch(value)), f"invalid exact decimal: {value!r}")
    require(len(value) <= 1000, "decimal exceeds supported 1000-character limit")
    return Decimal(value)


def text(value):
    return format(value, "f")


def parse_token(raw):
    """Preserve raw text; no interpretation of dash, percent, malformed or missing tokens."""
    if raw is None:
        return {"raw": raw, "status": "missing", "value": None}
    s = raw.strip()
    if not s:
        return {"raw": raw, "status": "blank", "value": None}
    if s in {"-", "–", "—"}:
        return {"raw": raw, "status": "dash", "value": None}
    sign = -1 if s.startswith("-") or (s.startswith("(") and s.endswith(")")) else 1
    core = s[1:] if s.startswith("-") else s[1:-1] if s.startswith("(") and s.endswith(")") else s
    if not TOKEN.fullmatch(core):
        return {"raw": raw, "status": "unrecognized", "value": None}
    value = decimal(core.replace(",", ""))
    return {"raw": raw, "status": "parsed", "value": ("-" if sign < 0 and value else "") + text(value)}


def calculate(relation):
    require(relation["operation"] == "signed_sum", "unsupported operation")
    require(relation["rounding_policy"] == "independent_nearest", "unsupported rounding policy")
    require(relation["complete"] is True, "unknown contributors")
    ops = relation["operands"]
    require(len(ops) >= 2 and len({o['operand_id'] for o in ops}) == len(ops), "invalid operands")
    require(any(o['role'] == 'total' for o in ops), "total operand is required")
    require(all(relation['context'].get(k) for k in ['concept', 'entity', 'period', 'unit', 'presentation_basis']), "incomplete context")
    with localcontext() as ctx:
        # Bounded decimal strings, products of three values, and arbitrary operand counts.
        ctx.prec = 8000 + len(str(len(ops)))
        ctx.traps[Inexact] = True
        ctx.traps[Rounded] = True
        before = after = tolerance = Decimal(0)
        for op in ops:
            a, scale, step = (decimal(op[k]) for k in ['coefficient', 'scale', 'rounding_step'])
            require(scale > 0 and step >= 0 and a != 0, "invalid scale, step or coefficient")
            before += a * decimal(op['original_value']) * scale
            after += a * decimal(op['injected_value']) * scale
            tolerance += abs(a) * step * scale / 2
        change = after - before
        magnitude = abs(change)
        band = 'within_tolerance' if magnitude <= tolerance else 'boundary' if magnitude <= 2*tolerance else 'above_tolerance'
        return {"original_residual": text(before), "injected_residual": text(after),
                "residual_change": text(change), "tolerance_bound": text(tolerance), "detectability_band": band}
