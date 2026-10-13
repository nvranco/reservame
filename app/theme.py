"""Tema verde cancha y componentes visuales compartidos."""
from __future__ import annotations

import json
from contextlib import contextmanager

from nicegui import ui

CSS = """
body {
  --q-primary: #2f8f3e; --q-secondary: #1f6b2d; --q-accent: #f2b705;
  --q-positive: #2f8f3e; --q-negative: #d64545; --q-warning: #e8a317;
  background: #f1f7ee; color: #1c2b1f;
  font-family: 'Nunito', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}
.app-header { background: linear-gradient(135deg,#2f8f3e,#1f6b2d); box-shadow: 0 2px 10px rgba(20,70,30,.25); }
.brand { color:#fff; font-weight:800; font-size:1.25rem; letter-spacing:.2px; text-decoration:none; }
.demo-pill { background:rgba(255,255,255,.2); color:#fff; border-radius:999px; padding:2px 10px; font-size:.7rem; font-weight:800; letter-spacing:.08em; }
.page-enter { animation: fadeUp .4s ease both; }
@keyframes fadeUp { from { opacity:0; transform: translateY(10px);} to { opacity:1; transform:none;} }
.card-r { background:#fff; border:1px solid #e0ebdc; border-radius:20px; box-shadow:0 2px 14px rgba(30,80,40,.07); transition: box-shadow .2s, transform .2s; }
.card-link:hover { box-shadow:0 6px 22px rgba(30,80,40,.16); transform: translateY(-2px); cursor:pointer; }
.hero { border-radius:24px; color:#fff; padding:28px 24px;
  background:
    repeating-linear-gradient(90deg, rgba(255,255,255,.05) 0 48px, rgba(255,255,255,0) 48px 96px),
    linear-gradient(135deg,#34a047,#1c6129);
  box-shadow:0 8px 26px rgba(30,100,45,.3); }
.hero h1 { font-size:2rem; font-weight:800; line-height:1.1; margin:0; }
.hero p { margin:8px 0 0; opacity:.92; }
.muted { color:#6b7d6e; }
.chip { border-radius:999px; padding:2px 12px; font-size:.78rem; font-weight:800; white-space:nowrap; }
.chip-pendiente { background:#fff1cc; color:#8a5a00; }
.chip-confirmada { background:#d9f2dd; color:#1c6129; }
.chip-cancelada { background:#fde0e0; color:#a12626; }
.chip-neutral { background:#e8efe6; color:#405344; }
.day-chip { min-width:56px; text-align:center; border-radius:16px; padding:6px 8px; background:#fff; border:1.5px solid #dbe8d7;
  cursor:pointer; transition: all .15s; user-select:none; line-height:1.15; }
.day-chip:hover { border-color:#2f8f3e; }
.day-chip-sel { background:#2f8f3e; color:#fff; border-color:#2f8f3e; box-shadow:0 4px 12px rgba(47,143,62,.35); }
.slot { border-radius:14px; padding:10px 8px; text-align:center; font-weight:700; border:1.5px solid transparent; transition: all .15s; user-select:none; min-height:58px;
  display:flex; flex-direction:column; justify-content:center; gap:1px; }
.slot small { font-weight:600; font-size:.72rem; }
.slot-libre { background:#e6f5e8; color:#1c6129; border-color:#bfe3c5; cursor:pointer; }
.slot-libre:hover { background:#d3eed8; transform: translateY(-1px); }
.slot-sel { background:#2f8f3e; color:#fff; border-color:#1f6b2d; box-shadow:0 4px 14px rgba(47,143,62,.4); cursor:pointer; }
.slot-ocupado { background:#f0eeee; color:#8d8585; text-decoration: line-through; cursor:not-allowed; }
.slot-adm-ocupado { background:#fff1cc; color:#8a5a00; border-color:#f3dc9a; cursor:pointer; }
.slot-adm-conf { background:#d9f2dd; color:#1c6129; border-color:#a9d9b0; cursor:pointer; }
.slot-bloqueado { background:#e3e6e3; color:#5f6a62; border-color:#ccd2cc; cursor:pointer; }
.slot-pasado { background:#f6f6f4; color:#b5b8b3; cursor:default; }
.cancha-opt { border-radius:16px; padding:12px 14px; background:#f4faf3; border:1.5px solid #cfe5d2; cursor:pointer; transition: all .15s; user-select:none; display:flex; flex-direction:column; gap:2px; }
.cancha-opt:hover { border-color:#2f8f3e; transform: translateY(-1px); }
.cancha-sel { background:#2f8f3e; color:#fff; border-color:#1f6b2d; box-shadow:0 4px 14px rgba(47,143,62,.35); }
.step-num { width:34px; height:34px; min-width:34px; border-radius:50%; background:#2f8f3e; color:#fff; font-weight:800; display:flex; align-items:center; justify-content:center; }
.wa-box { background:#f4faf3; border:1px dashed #9fcfa6; border-radius:14px; padding:12px 14px; font-size:.92rem; color:#2c4a31; }
.day-strip { scrollbar-width: thin; }
.q-btn { text-transform:none !important; font-weight:700; }
.q-tab__label { text-transform:none; font-weight:800; }
"""


def init() -> None:
    ui.add_css(CSS, shared=True)
    ui.add_head_html(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">',
        shared=True,
    )


@contextmanager
def frame(wide: bool = False, volver: bool = False):
    """Estructura común: header verde + columna de contenido centrada."""
    ui.colors(primary='#2f8f3e', secondary='#1f6b2d', accent='#f2b705', positive='#2f8f3e', negative='#d64545')
    with ui.header(elevated=False).classes('app-header items-center justify-between px-4 py-2'):
        with ui.link(target='/').classes('brand'):
            ui.html('⚽ Reservame')
        with ui.row().classes('items-center gap-2'):
            ui.html('<span class="demo-pill">DEMO</span>')
            if volver:
                ui.button(icon='logout', on_click=lambda: ui.navigate.to('/')).props(
                    'flat round dense color=white').tooltip('Salir')
    with ui.column().classes('w-full items-center'):
        with ui.column().classes(
            f'w-full gap-4 p-4 pb-12 page-enter {"max-w-6xl" if wide else "max-w-4xl"}'
        ):
            yield


def estado_chip(estado: str) -> None:
    ui.html(f'<span class="chip chip-{estado.lower()}">{estado}</span>')


def copiar(texto: str, mensaje: str = 'Copiado al portapapeles') -> None:
    t = json.dumps(texto)
    ui.run_javascript(
        f"""(()=>{{const t={t};
        const f=()=>{{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();}};
        if(navigator.clipboard&&window.isSecureContext){{navigator.clipboard.writeText(t).catch(f);}}else{{f();}}}})()"""
    )
    ui.notify(mensaje, type='positive', position='top', icon='content_copy')


def base_url() -> str:
    """URL base pública, respetando el proxy de Railway."""
    req = ui.context.client.request
    proto = req.headers.get('x-forwarded-proto', req.url.scheme)
    host = req.headers.get('x-forwarded-host', req.headers.get('host', req.url.netloc))
    return f'{proto}://{host}'


def selector_dias(dias, sel: int, on_change) -> None:
    from . import store

    with ui.row().classes('day-strip w-full no-wrap overflow-x-auto gap-2 pb-1'):
        for i, d in enumerate(dias):
            cls = 'day-chip day-chip-sel' if i == sel else 'day-chip'
            with ui.element('div').classes(cls).on('click', lambda _, i=i: on_change(i)):
                ui.label(store.dia_corto(d).upper()).classes('text-xs font-bold')
                ui.label(str(d.day)).classes('text-lg font-extrabold')
