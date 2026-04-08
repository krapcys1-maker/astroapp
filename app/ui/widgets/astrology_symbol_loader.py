from __future__ import annotations

import importlib.util
import re
from functools import cache, lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _wheel_template_text() -> str:
    spec = importlib.util.find_spec('kerykeion')
    if spec is None or spec.origin is None:
        raise RuntimeError('kerykeion package not found for symbol asset loading')
    package_dir = Path(spec.origin).resolve().parent
    template_path = package_dir / 'charts' / 'templates' / 'wheel_only.xml'
    return template_path.read_text(encoding='utf-8')


@cache
def get_symbol_body(symbol_id: str) -> str:
    text = _wheel_template_text()
    match = re.search(rf'<symbol id="{re.escape(symbol_id)}">(.*?)</symbol>', text, re.S)
    if match is None:
        raise KeyError(f'Symbol {symbol_id!r} not found in wheel template')
    return match.group(1).strip()


def build_symbol_svg(symbol_id: str, color: str, viewbox: str = '0 0 32 32') -> str:
    body = get_symbol_body(symbol_id)
    body = re.sub(r'var\(--kerykeion-chart-color-[^)]+\)', color, body)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{viewbox}" preserveAspectRatio="xMidYMid meet">'
        f'{body}'
        '</svg>'
    )
