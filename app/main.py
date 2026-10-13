import os

from nicegui import ui

from . import theme
from .pages import admin, home, player  # noqa: F401  (registran las rutas)

theme.init()

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='Reservame · Reservá tu cancha',
        favicon='⚽',
        host='0.0.0.0',
        port=int(os.getenv('PORT', '8080')),
        language='es',
        reload=False,
        show=False,
    )
