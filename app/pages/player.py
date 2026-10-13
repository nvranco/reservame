from datetime import datetime

from nicegui import ui

from .. import store, theme


def _no_encontrada(texto: str):
    with theme.frame():
        with ui.column().classes('card-r p-6 items-center w-full gap-2'):
            ui.label('🤔').classes('text-4xl')
            ui.label(texto).classes('text-lg font-extrabold')
            ui.button('Volver al inicio', on_click=lambda: ui.navigate.to('/')).props('rounded unelevated no-caps')


@ui.page('/cancha/{slug}')
def cancha_publica(slug: str):
    c = store.complejos.get(slug)
    if not c:
        return _no_encontrada('No encontramos esa cancha')

    state = {'cancha': None, 'dia': 0, 'hora': None, 'nombre': '', 'telefono': '', 'seen': store.version}
    dias = store.fechas()

    with theme.frame():
        with ui.element('div').classes('grid grid-cols-1 lg:grid-cols-5 gap-4 w-full items-start'):
            # ---- info de la cancha
            with ui.column().classes('hero lg:col-span-2 gap-1 w-full'):
                ui.html(f'<h1>{c.nombre}</h1>')
                with ui.row().classes('items-center gap-1 no-wrap'):
                    ui.icon('place')
                    ui.label(c.direccion)
                ks0 = store.canchas_de(slug, solo_activas=True)
                ui.html(f'<p>{len(ks0)} canchas · seña desde <b>{store.ars(min(k.sena for k in ks0))}</b> por hora</p>')
                ui.label('Elegí la cancha, un horario libre, dejá tus datos y listo.').classes('text-sm opacity-90 mt-2')

            # ---- grilla + formulario
            with ui.column().classes('lg:col-span-3 w-full gap-4'):
                @ui.refreshable
                def selector_cancha():
                    ks = store.canchas_de(slug, solo_activas=True)
                    if state['cancha'] not in [k.id for k in ks]:
                        state['cancha'], state['hora'] = None, None
                    with ui.column().classes('card-r p-4 w-full gap-3'):
                        ui.label('1. Elegí la cancha').classes('font-extrabold')
                        with ui.element('div').classes('grid grid-cols-1 sm:grid-cols-2 gap-2 w-full'):
                            for k in ks:
                                sel = state['cancha'] == k.id
                                with ui.element('div').classes('cancha-opt' + (' cancha-sel' if sel else '')).on(
                                        'click', lambda _, kid=k.id: elegir_cancha(kid)):
                                    with ui.row().classes('items-center justify-between no-wrap w-full'):
                                        ui.label(k.nombre).classes('font-extrabold')
                                        if sel:
                                            ui.icon('check_circle')
                                    ui.label(k.tipo).classes('text-xs opacity-80')
                                    ui.label(f'Seña {store.ars(k.sena)} por hora').classes('text-sm font-bold')

                def elegir_cancha(kid):
                    state['cancha'], state['hora'] = kid, None
                    selector_cancha.refresh(); grilla.refresh(); formulario.refresh()

                @ui.refreshable
                def grilla():
                    if state['cancha'] is None:
                        return
                    fecha = dias[state['dia']]
                    with ui.column().classes('card-r p-4 w-full gap-3'):
                        ui.label('2. Elegí día y horario').classes('font-extrabold')

                        def cambiar_dia(i):
                            state['dia'], state['hora'] = i, None
                            grilla.refresh(); formulario.refresh()

                        theme.selector_dias(dias, state['dia'], cambiar_dia)
                        with ui.element('div').classes('grid grid-cols-2 sm:grid-cols-4 gap-2 w-full'):
                            for h in store.HORAS:
                                st, _ = store.estado_slot(state['cancha'], fecha, h)
                                if st == 'libre':
                                    cls = 'slot slot-sel' if state['hora'] == h else 'slot slot-libre'
                                    with ui.element('div').classes(cls).on('click', lambda _, h=h: elegir(h)):
                                        ui.label(f'{h % 24:02d}:00')
                                        ui.html('<small>Libre</small>')
                                elif st == 'pasado':
                                    continue
                                else:
                                    with ui.element('div').classes('slot slot-ocupado'):
                                        ui.label(f'{h % 24:02d}:00')
                                        ui.html('<small>Ocupado</small>')

                def elegir(h):
                    state['hora'] = h
                    grilla.refresh(); formulario.refresh()

                @ui.refreshable
                def formulario():
                    if state['cancha'] is None or state['hora'] is None:
                        return
                    fecha = dias[state['dia']]
                    if store.estado_slot(state['cancha'], fecha, state['hora'])[0] != 'libre':
                        state['hora'] = None
                        return
                    k = store.canchas[state['cancha']]
                    with ui.column().classes('card-r p-4 w-full gap-3'):
                        ui.label('3. Tus datos').classes('font-extrabold')
                        ui.html(f'<b>{k.nombre}</b> ({k.tipo}) · <b>{store.fmt_fecha(fecha)}</b> · {store.fmt_turno(state["hora"])}hs · '
                                f'Seña <b>{store.ars(k.sena)}</b>')
                        ui.input('Nombre y apellido').props('outlined rounded dense').classes('w-full').bind_value(state, 'nombre')
                        ui.input('Teléfono (WhatsApp)', placeholder='11 5555 1234').props(
                            'outlined rounded dense type=tel').classes('w-full').bind_value(state, 'telefono')
                        ui.button('Reservar', icon='check_circle', on_click=reservar).props(
                            'unelevated rounded no-caps color=primary size=lg').classes('w-full')

                def reservar():
                    nombre, tel = state['nombre'].strip(), state['telefono'].strip()
                    if len(nombre) < 3:
                        ui.notify('Escribí tu nombre y apellido', type='warning', position='top'); return
                    if len([ch for ch in tel if ch.isdigit()]) < 8:
                        ui.notify('Revisá el teléfono: necesitamos al menos 8 dígitos', type='warning', position='top'); return
                    try:
                        r = store.crear_reserva(state['cancha'], dias[state['dia']], state['hora'], nombre, tel)
                    except ValueError as e:
                        ui.notify(str(e), type='negative', position='top')
                        state['hora'] = None
                        grilla.refresh(); formulario.refresh()
                        return
                    ui.notify('¡Reserva creada! Seguí los pasos para señar.', type='positive', position='top')
                    ui.navigate.to(f'/cancha/{slug}/reserva/{r.id}')

                selector_cancha()
                grilla()
                formulario()

                def tick():
                    if store.version != state['seen']:
                        state['seen'] = store.version
                        selector_cancha.refresh(); grilla.refresh(); formulario.refresh()

                ui.timer(2.0, tick)


@ui.page('/cancha/{slug}/reserva/{rid}')
def reserva_publica(slug: str, rid: int):
    r = store.reservas.get(rid)
    if not r or r.slug != slug:
        return _no_encontrada('No encontramos esa reserva')
    c = store.complejos[slug]
    k = store.canchas[r.cancha_id]
    state = {'seen': -1}

    with theme.frame():
        with ui.column().classes('w-full max-w-xl self-center gap-4'):
            @ui.refreshable
            def contenido():
                est = r.estado
                color = {'Pendiente': 'amber', 'Confirmada': 'green', 'Cancelada': 'red'}[est]
                icono = {'Pendiente': 'hourglass_top', 'Confirmada': 'check_circle', 'Cancelada': 'cancel'}[est]
                titulo = {
                    'Pendiente': 'Reserva pendiente de seña',
                    'Confirmada': '¡Reserva confirmada!',
                    'Cancelada': 'Reserva cancelada',
                }[est]
                with ui.column().classes(f'card-r p-5 w-full gap-1 items-center text-center'):
                    ui.icon(icono, size='3rem', color=color)
                    ui.label(titulo).classes('text-xl font-extrabold')
                    ui.label(f'{c.nombre} · {k.nombre} · {store.fmt_fecha(r.fecha)} · {store.fmt_turno(r.hora)}hs').classes('muted')
                    ui.label(f'A nombre de {r.nombre} · Reserva #{r.id}').classes('text-sm muted')
                    if est == 'Cancelada':
                        quien = store.MOTIVOS.get(r.cancelada_por or '', 'la cancha')
                        ui.label(f'Se canceló por {quien}. El horario volvió a quedar libre.').classes('text-sm mt-1')
                        ui.button('Reservar otro horario', icon='event',
                                  on_click=lambda: ui.navigate.to(f'/cancha/{slug}')).props(
                            'unelevated rounded no-caps color=primary').classes('mt-2')
                    if est == 'Confirmada':
                        ui.label('La cancha validó tu seña. ¡Nos vemos en la cancha!').classes('text-sm mt-1')

                if est == 'Pendiente':
                    with ui.column().classes('card-r p-5 w-full gap-4'):
                        ui.label('Para asegurar tu turno').classes('font-extrabold text-lg')
                        # 1
                        with ui.row().classes('no-wrap gap-3 w-full items-start'):
                            ui.html('<div class="step-num">1</div>')
                            with ui.column().classes('gap-2 w-full'):
                                ui.label('Mandá un mensaje a la cancha por WhatsApp con los datos de la reserva.').classes('font-bold')
                                ui.button('Abrir WhatsApp', icon='chat').props(
                                    f'unelevated rounded no-caps color=positive href="{store.link_whatsapp(r)}" target=_blank')
                                ui.label('Este es el mensaje que se va a mandar:').classes('text-xs muted')
                                ui.html(f'<div class="wa-box">{store.mensaje_whatsapp(r)}</div>')
                                ui.label('El comprobante lo mandás vos por ese mismo chat; Reservame no lo guarda.').classes('text-xs muted')
                        # 2
                        with ui.row().classes('no-wrap gap-3 w-full items-start'):
                            ui.html('<div class="step-num">2</div>')
                            with ui.column().classes('gap-1'):
                                ui.html(f'<b>Transferí la seña de {store.ars(k.sena)} al alias {c.alias}</b>')
                                ui.button('Copiar alias', icon='content_copy',
                                          on_click=lambda: theme.copiar(c.alias, 'Alias copiado')).props(
                                    'outline rounded no-caps size=sm color=primary')
                        # 3
                        with ui.row().classes('no-wrap gap-3 w-full items-start'):
                            ui.html('<div class="step-num">3</div>')
                            ui.html(f'<b>La cancha valida tu seña dentro de {c.plazo_horas} '
                                    f'{"hora" if c.plazo_horas == 1 else "horas"}.</b><br>'
                                    f'<span class="muted text-sm">Si no recibe la seña a tiempo, cancela la reserva '
                                    f'y te avisa por WhatsApp y mail.</span>')

                if est != 'Cancelada':
                    with ui.column().classes('card-r p-4 w-full gap-2'):
                        if store.puede_cancelar_jugador(r):
                            ui.label(f'Podés cancelar hasta las {store.fmt_hora(store.vence(r))} '
                                     f'({store.fmt_fecha(store.vence(r).date())}).').classes('text-sm')
                            ui.button('Cancelar mi reserva', icon='close', on_click=confirmar_cancelacion).props(
                                'outline rounded no-caps color=negative')
                        else:
                            ui.label('Ya pasó el plazo para cancelar desde acá. Si no podés ir, avisale a la cancha por WhatsApp.').classes('text-sm muted')

                avisos = store.notificaciones_de(slug, r.id, 'jugador')
                if avisos:
                    with ui.column().classes('card-r p-4 w-full gap-2'):
                        ui.label('Avisos que recibiste (simulados)').classes('font-extrabold')
                        for n in avisos:
                            with ui.row().classes('no-wrap gap-2 items-start w-full'):
                                ui.icon('mail' if n.canal == 'Mail' else 'chat', color='primary').classes('mt-1')
                                with ui.column().classes('gap-0'):
                                    ui.label(f'{n.canal} · {store.fmt_hora(n.creada)}').classes('text-xs muted')
                                    ui.label(n.asunto).classes('font-bold text-sm')
                                    ui.label(n.texto).classes('text-sm')

            holder = ui.element('div')

            def confirmar_cancelacion():
                with holder:
                    with ui.dialog() as d, ui.card().classes('rounded-2xl'):
                        ui.label('¿Cancelar tu reserva?').classes('text-lg font-extrabold')
                        ui.label('El horario va a volver a quedar libre.')
                        with ui.row().classes('justify-end w-full'):
                            ui.button('Volver', on_click=d.close).props('flat no-caps')
                            ui.button('Sí, cancelar', on_click=lambda: hacer(d)).props('unelevated no-caps color=negative rounded')
                d.open()

            def hacer(d):
                d.close()
                try:
                    store.cambiar_estado(r.id, 'Cancelada', 'jugador')
                    ui.notify('Reserva cancelada', type='positive', position='top')
                except ValueError as e:
                    ui.notify(str(e), type='negative', position='top')
                contenido.refresh()

            contenido()

            def tick():
                if store.version != state['seen']:
                    state['seen'] = store.version
                    contenido.refresh()

            ui.timer(2.0, tick)
