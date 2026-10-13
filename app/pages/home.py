from nicegui import ui

from .. import store, theme


@ui.page('/')
def home():
    with theme.frame():
        with ui.element('div').classes('hero w-full'):
            ui.html('<h1>Reservá tu cancha<br>y señá en minutos</h1>')
            ui.label('Sin vueltas por WhatsApp: elegís el horario, transferís la seña y listo.')
            ui.button('Entrar como admin', icon='sports_soccer',
                      on_click=lambda: ui.navigate.to('/admin')).props(
                'unelevated rounded no-caps color=white text-color=primary size=lg').classes('mt-4')

        ui.label('Complejos de ejemplo').classes('text-lg font-extrabold mt-2')
        ui.label('Abrí una como si fueras jugador. Lo que cambies desde el admin se ve acá.').classes('muted -mt-3')
        with ui.element('div').classes('grid grid-cols-1 md:grid-cols-3 gap-3 w-full'):
            for c in store.complejos.values():
                ks = store.canchas_de(c.slug, solo_activas=True)
                with ui.link(target=f'/cancha/{c.slug}').classes('no-underline text-inherit'):
                    with ui.column().classes('card-r card-link p-4 gap-1 w-full'):
                        ui.label('⚽').classes('text-3xl')
                        ui.label(c.nombre).classes('text-lg font-extrabold')
                        with ui.row().classes('items-center gap-1 no-wrap muted'):
                            ui.icon('place', size='sm')
                            ui.label(c.direccion).classes('text-sm')
                        ui.label(f'{len(ks)} canchas · seña desde {store.ars(min(k.sena for k in ks))} por hora').classes('font-bold text-primary')
                        ui.label(f'/cancha/{c.slug}').classes('text-xs muted')

        ui.label('Demo con datos de ejemplo: todo se guarda en memoria y se reinicia con el servicio. '
                 'No hay pagos, mails ni WhatsApp reales.').classes('muted text-xs text-center w-full mt-4')
