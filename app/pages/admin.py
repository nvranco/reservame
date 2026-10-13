from datetime import date

from nicegui import ui

from .. import store, theme


@ui.page('/admin')
def admin():
    state = {'slug': next(iter(store.complejos)), 'cancha': None, 'dia': 0, 'filtro': 'Todas', 'seen': store.version,
             'm_fecha': None, 'm_hora': None, 'm_cancha': None, 'm_nombre': '', 'm_tel': ''}
    dias = store.fechas()
    base = theme.base_url()

    def complejo():
        return store.complejos[state['slug']]

    def cancha_sel() -> int:
        """Cancha elegida en la grilla (la primera activa si la elegida ya no existe)."""
        ids = [k.id for k in store.canchas_de(state['slug'])]
        if state['cancha'] not in ids:
            state['cancha'] = ids[0]
        return state['cancha']

    def refrescar():
        link_card.refresh(); reservas_ui.refresh(); grilla_ui.refresh(); notifs_ui.refresh(); canchas_ui.refresh()

    with theme.frame(wide=True, volver=True):
        holder = ui.element('div')  # los diálogos viven acá, fuera de los refreshables

        # ------------------------------------------------ cabecera
        with ui.element('div').classes('grid grid-cols-1 lg:grid-cols-2 gap-3 w-full'):
            with ui.column().classes('card-r p-4 gap-2 w-full'):
                ui.label('Panel del complejo').classes('text-xl font-extrabold')

                def cambiar_cancha(e):
                    state['slug'] = e.value
                    state['cancha'] = None
                    state['filtro'] = 'Todas'
                    refrescar(); form_ui.refresh()

                ui.select({s: c.nombre for s, c in store.complejos.items()}, value=state['slug'],
                          label='Complejo', on_change=cambiar_cancha).props('outlined rounded dense').classes('w-full')

            @ui.refreshable
            def link_card():
                url = f'{base}/cancha/{state["slug"]}'
                with ui.column().classes('card-r p-4 gap-2 w-full'):
                    ui.label('Link público del complejo (el jugador elige la cancha ahí)').classes('font-extrabold')
                    ui.label(url).classes('text-sm break-all bg-green-50 rounded-xl p-2 w-full')
                    with ui.row().classes('gap-2'):
                        ui.button('Copiar link', icon='content_copy', on_click=lambda: theme.copiar(url, 'Link copiado')).props(
                            'unelevated rounded no-caps color=primary')
                        ui.button('Abrir como jugador', icon='open_in_new',
                                  on_click=lambda: ui.navigate.to(url, new_tab=True)).props('outline rounded no-caps color=primary')
            link_card()

        # ------------------------------------------------ pestañas
        with ui.tabs().classes('w-full card-r').props('active-color=primary indicator-color=primary align=justify narrow-indicator') as tabs:
            t_res = ui.tab('Reservas', icon='event_available')
            t_gri = ui.tab('Grilla', icon='grid_view')
            t_can = ui.tab('Canchas', icon='sports_soccer')
            t_cfg = ui.tab('Complejo', icon='tune')
            t_not = ui.tab('Avisos', icon='notifications')

        # ------------------------------------------------ reservas
        def pedir_cancelacion(r):
            with holder:
                with ui.dialog() as d, ui.card().classes('rounded-2xl w-96 max-w-full'):
                    ui.label(f'Cancelar la reserva de {r.nombre}').classes('text-lg font-extrabold')
                    ui.label(f'{store.canchas[r.cancha_id].nombre} · {store.fmt_fecha(r.fecha)} · {store.fmt_turno(r.hora)}hs').classes('muted')
                    motivo = ui.select({'falta_sena': 'Falta de seña', 'cancha': 'Decisión de la cancha'},
                                       value='falta_sena', label='Motivo').props('outlined dense rounded').classes('w-full')
                    ui.label('Se le envía un aviso simulado al jugador por WhatsApp y mail.').classes('text-xs muted')
                    with ui.row().classes('justify-end w-full'):
                        ui.button('Volver', on_click=d.close).props('flat no-caps')
                        ui.button('Cancelar reserva', on_click=lambda: (
                            d.close(), cambiar(r, 'Cancelada', motivo.value))).props('unelevated rounded no-caps color=negative')
            d.open()

        def cambiar(r, nuevo, motivo='cancha'):
            try:
                store.cambiar_estado(r.id, nuevo, motivo)
                ui.notify(f'Reserva {nuevo.lower()}' + (' · aviso enviado al jugador' if nuevo == 'Cancelada' else ' · jugador avisado'),
                          type='positive', position='top')
            except ValueError as e:
                ui.notify(str(e), type='negative', position='top')
            tick(force=True)

        @ui.refreshable
        def reservas_ui():
            rs = store.reservas_de(state['slug'])
            pend = sum(r.estado == 'Pendiente' for r in rs)
            conf = sum(r.estado == 'Confirmada' for r in rs)
            with ui.row().classes('w-full gap-3'):
                for t, v, ic in (('Pendientes', pend, 'hourglass_top'), ('Confirmadas', conf, 'check_circle'),
                                 ('Señas confirmadas', store.ars(sum(store.sena_de(r) for r in rs if r.estado == 'Confirmada')), 'payments')):
                    with ui.column().classes('card-r p-3 gap-0 flex-1 min-w-[140px]'):
                        ui.label(t).classes('text-xs muted')
                        ui.label(str(v)).classes('text-2xl font-extrabold text-primary')
            with ui.row().classes('w-full items-center justify-between'):
                with ui.row().classes('gap-1'):
                    for f in ('Todas', *store.ESTADOS):
                        ui.button(f, on_click=lambda f=f: (state.update(filtro=f), reservas_ui.refresh())).props(
                            f'rounded no-caps size=sm {"unelevated color=primary" if state["filtro"] == f else "outline color=primary"}')
                ui.button('Reserva manual', icon='add', on_click=lambda: abrir_manual()).props('unelevated rounded no-caps color=accent text-color=dark')
            visibles = [r for r in rs if state['filtro'] in ('Todas', r.estado)]
            if not visibles:
                with ui.column().classes('card-r p-6 w-full items-center'):
                    ui.label('No hay reservas para mostrar').classes('muted')
            with ui.element('div').classes('grid grid-cols-1 xl:grid-cols-2 gap-3 w-full'):
                for r in visibles:
                    with ui.column().classes('card-r p-4 gap-2 w-full'):
                        with ui.row().classes('justify-between items-start w-full no-wrap'):
                            with ui.column().classes('gap-0'):
                                ui.label(r.nombre).classes('font-extrabold text-base')
                                ui.label(f'{r.telefono}').classes('text-sm muted')
                            theme.estado_chip(r.estado)
                        ui.label(f'{store.canchas[r.cancha_id].nombre} · {store.fmt_fecha(r.fecha)} · {store.fmt_turno(r.hora)}hs').classes('text-sm font-bold')
                        extra = f'Seña {store.ars(store.sena_de(r))} · ' + ('Reserva manual' if r.origen == 'manual' else 'Reserva web')
                        if r.estado == 'Pendiente':
                            extra += f' · validar antes de las {store.fmt_hora(store.vence(r))}'
                        if r.estado == 'Cancelada':
                            extra += f' · cancelada por {store.MOTIVOS.get(r.cancelada_por or "", "la cancha")}'
                        ui.label(extra).classes('text-xs muted')
                        with ui.row().classes('gap-2'):
                            if r.estado == 'Pendiente':
                                ui.button('Confirmar seña', icon='check', on_click=lambda r=r: cambiar(r, 'Confirmada')).props(
                                    'unelevated rounded no-caps size=sm color=primary')
                            if r.estado != 'Cancelada':
                                ui.button('Cancelar', icon='close', on_click=lambda r=r: pedir_cancelacion(r)).props(
                                    'outline rounded no-caps size=sm color=negative')
                            ui.button('WhatsApp', icon='chat').props(
                                f'flat rounded no-caps size=sm color=positive href="https://wa.me/{store.tel_wa(r.telefono)}" target=_blank')

        # ------------------------------------------------ reserva manual
        def abrir_manual(fecha: date | None = None, hora: int | None = None, cancha_id: int | None = None):
            state['m_fecha'] = (fecha or dias[state['dia']]).isoformat()
            state['m_hora'] = hora
            state['m_cancha'] = cancha_id or cancha_sel()
            state['m_nombre'] = state['m_tel'] = ''
            with holder:
                with ui.dialog() as d, ui.card().classes('rounded-2xl w-96 max-w-full'):
                    ui.label('Reserva manual').classes('text-lg font-extrabold')
                    ui.label('Para turnos que te piden por teléfono o en persona. Queda confirmada.').classes('text-sm muted')

                    def libres():
                        f = date.fromisoformat(state['m_fecha'])
                        return {h: store.fmt_turno(h) for h in store.HORAS
                                if store.estado_slot(state['m_cancha'], f, h)[0] == 'libre'}

                    def recalcular():
                        opts = libres()
                        hora_sel.set_options(opts, value=state['m_hora'] if state['m_hora'] in opts else next(iter(opts), None))

                    def al_cambiar_fecha(e):
                        state['m_fecha'] = e.value
                        recalcular()

                    def al_cambiar_cancha(e):
                        state['m_cancha'] = e.value
                        recalcular()

                    ui.select({k.id: k.nombre for k in store.canchas_de(state['slug'], solo_activas=True)},
                              value=state['m_cancha'], label='Cancha', on_change=al_cambiar_cancha).props(
                        'outlined dense rounded').classes('w-full')

                    ui.select({d_.isoformat(): store.fmt_fecha(d_) for d_ in dias}, value=state['m_fecha'],
                              label='Día', on_change=al_cambiar_fecha).props('outlined dense rounded').classes('w-full')
                    opts = libres()
                    hora_sel = ui.select(opts, value=hora if hora in opts else next(iter(opts), None),
                                         label='Horario', on_change=lambda e: state.update(m_hora=e.value)).props(
                        'outlined dense rounded').classes('w-full')
                    state['m_hora'] = hora_sel.value
                    ui.input('Nombre').props('outlined dense rounded').classes('w-full').bind_value(state, 'm_nombre')
                    ui.input('Teléfono').props('outlined dense rounded type=tel').classes('w-full').bind_value(state, 'm_tel')

                    def guardar():
                        if state['m_hora'] is None or len(state['m_nombre'].strip()) < 2:
                            ui.notify('Completá horario y nombre', type='warning', position='top'); return
                        try:
                            store.crear_reserva(state['m_cancha'], date.fromisoformat(state['m_fecha']), state['m_hora'],
                                                state['m_nombre'], state['m_tel'] or '-', 'manual')
                        except ValueError as e:
                            ui.notify(str(e), type='negative', position='top'); return
                        d.close()
                        ui.notify('Reserva manual cargada', type='positive', position='top')
                        tick(force=True)

                    with ui.row().classes('justify-end w-full'):
                        ui.button('Volver', on_click=d.close).props('flat no-caps')
                        ui.button('Guardar', on_click=guardar).props('unelevated rounded no-caps color=primary')
            d.open()

        # ------------------------------------------------ grilla
        def slot_dialog(fecha: date, hora: int, st: str, r):
            kid = cancha_sel()
            with holder:
                with ui.dialog() as d, ui.card().classes('rounded-2xl w-96 max-w-full'):
                    ui.label(f'{store.canchas[kid].nombre} · {store.fmt_fecha(fecha)} · {store.fmt_turno(hora)}hs').classes('text-lg font-extrabold')
                    if st == 'libre':
                        ui.label('Horario libre').classes('muted')
                        ui.button('Cargar reserva manual', icon='person_add', on_click=lambda: (d.close(), abrir_manual(fecha, hora, kid))).props(
                            'unelevated rounded no-caps color=primary').classes('w-full')
                        ui.button('Bloquear horario', icon='block', on_click=lambda: (
                            store.bloquear(kid, fecha, hora), d.close(), ui.notify('Horario bloqueado', type='positive', position='top'),
                            tick(force=True))).props('outline rounded no-caps color=grey-8').classes('w-full')
                    elif st == 'bloqueado':
                        ui.label('Horario bloqueado: los jugadores no pueden reservarlo.').classes('muted')
                        ui.button('Desbloquear', icon='lock_open', on_click=lambda: (
                            store.desbloquear(kid, fecha, hora), d.close(), ui.notify('Horario liberado', type='positive', position='top'),
                            tick(force=True))).props('unelevated rounded no-caps color=primary').classes('w-full')
                    else:
                        with ui.row().classes('items-center gap-2'):
                            ui.label(r.nombre).classes('font-bold'); theme.estado_chip(r.estado)
                        ui.label(r.telefono).classes('muted')
                        if r.estado == 'Pendiente':
                            ui.button('Confirmar seña', icon='check', on_click=lambda: (d.close(), cambiar(r, 'Confirmada'))).props(
                                'unelevated rounded no-caps color=primary').classes('w-full')
                        ui.button('Cancelar reserva', icon='close', on_click=lambda: (d.close(), pedir_cancelacion(r))).props(
                            'outline rounded no-caps color=negative').classes('w-full')
                    ui.button('Cerrar', on_click=d.close).props('flat no-caps').classes('w-full')
            d.open()

        @ui.refreshable
        def grilla_ui():
            fecha = dias[state['dia']]
            with ui.column().classes('card-r p-4 w-full gap-3'):
                ui.label('Tocá un horario para bloquearlo, cargar una reserva o gestionarla').classes('text-sm muted')

                with ui.row().classes('gap-2 flex-wrap'):
                    for k in store.canchas_de(state['slug']):
                        on = k.id == cancha_sel()
                        ui.button(k.nombre + ('' if k.activa else ' (inactiva)'),
                                  on_click=lambda k=k: (state.update(cancha=k.id), grilla_ui.refresh())).props(
                            f'rounded no-caps size=sm {"unelevated color=primary" if on else "outline color=primary"}')

                def cambiar_dia(i):
                    state['dia'] = i
                    grilla_ui.refresh()

                theme.selector_dias(dias, state['dia'], cambiar_dia)
                with ui.element('div').classes('grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 w-full'):
                    for h in store.HORAS:
                        st, r = store.estado_slot(cancha_sel(), fecha, h)
                        if st == 'pasado':
                            with ui.element('div').classes('slot slot-pasado'):
                                ui.label(f'{h % 24:02d}:00'); ui.html('<small>Pasó</small>')
                            continue
                        cls = {'libre': 'slot-libre', 'bloqueado': 'slot-bloqueado'}.get(
                            st, 'slot-adm-conf' if r and r.estado == 'Confirmada' else 'slot-adm-ocupado')
                        sub = {'libre': 'Libre', 'bloqueado': 'Bloqueado'}.get(st, r.nombre.split()[0] if r else '')
                        if st == 'ocupado' and r:
                            sub += f' · {r.estado[:4]}.' if r.estado == 'Pendiente' else ''
                        with ui.element('div').classes(f'slot {cls}').on(
                                'click', lambda _, f=fecha, h=h, st=st, r=r: slot_dialog(f, h, st, r)):
                            ui.label(f'{h % 24:02d}:00'); ui.html(f'<small>{sub}</small>')
                with ui.row().classes('gap-3 text-xs muted flex-wrap'):
                    for t, c_ in (('Libre', '#e6f5e8'), ('Pendiente', '#fff1cc'), ('Confirmada', '#d9f2dd'), ('Bloqueado', '#e3e6e3')):
                        ui.html(f'<span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:{c_};border:1px solid #bbb"></span> {t}')

        # ------------------------------------------------ mi cancha
        @ui.refreshable
        def form_ui():
            c = complejo()
            f = {'nombre': c.nombre, 'direccion': c.direccion, 'alias': c.alias,
                 'plazo': c.plazo_horas, 'whatsapp': c.whatsapp}

            def guardar():
                if not f['nombre'].strip() or not f['alias'].strip():
                    ui.notify('Completá nombre y alias', type='warning', position='top'); return
                store.actualizar_complejo(c.slug, nombre=f['nombre'].strip(), direccion=f['direccion'].strip(),
                                        alias=f['alias'].strip(),
                                        plazo_horas=max(1, int(f['plazo'] or 2)),
                                        whatsapp=store.tel_wa(f['whatsapp'] or c.whatsapp))
                ui.notify('Cambios guardados. Ya se ven en el link del jugador.', type='positive', position='top', icon='save')
                tick(force=True)

            with ui.column().classes('card-r p-4 w-full gap-3 max-w-2xl'):
                ui.label('Datos del complejo').classes('font-extrabold')
                ui.input('Nombre').props('outlined dense rounded').classes('w-full').bind_value(f, 'nombre')
                ui.input('Dirección').props('outlined dense rounded').classes('w-full').bind_value(f, 'direccion')
                ui.number('Plazo de validación (horas)', min=1, max=48, step=1, format='%.0f').props('outlined dense rounded').classes('w-full').bind_value(f, 'plazo')
                ui.input('Alias para transferir').props('outlined dense rounded').classes('w-full').bind_value(f, 'alias')
                ui.input('WhatsApp de la cancha').props('outlined dense rounded type=tel hint="Con código de área, ej. 54 9 11 5550 1234"').classes('w-full').bind_value(f, 'whatsapp')
                ui.button('Guardar cambios', icon='save', on_click=guardar).props('unelevated rounded no-caps color=primary')

        # ------------------------------------------------ canchas del complejo
        def dialogo_cancha(k=None):
            f = {'nombre': k.nombre if k else f'Cancha {len(store.canchas_de(state["slug"])) + 1}',
                 'tipo': k.tipo if k else store.TIPOS[0], 'sena': k.sena if k else 8000}
            with holder:
                with ui.dialog() as d, ui.card().classes('rounded-2xl w-96 max-w-full'):
                    ui.label('Editar cancha' if k else 'Agregar cancha').classes('text-lg font-extrabold')
                    ui.input('Nombre').props('outlined dense rounded').classes('w-full').bind_value(f, 'nombre')
                    ui.select(list(store.TIPOS), label='Tipo').props('outlined dense rounded').classes('w-full').bind_value(f, 'tipo')
                    ui.number('Seña por hora (ARS)', min=0, step=500, format='%.0f').props('outlined dense rounded prefix="$"').classes('w-full').bind_value(f, 'sena')

                    def guardar():
                        if len(f['nombre'].strip()) < 2 or not f['sena'] or f['sena'] <= 0:
                            ui.notify('Completá el nombre y una seña válida', type='warning', position='top'); return
                        if k:
                            store.actualizar_cancha(k.id, nombre=f['nombre'].strip(), tipo=f['tipo'], sena=int(f['sena']))
                        else:
                            nueva = store.agregar_cancha(state['slug'], f['nombre'], f['tipo'], int(f['sena']))
                            state['cancha'] = nueva.id
                        d.close()
                        ui.notify('Cancha guardada. Ya aparece en el link del jugador.' if not k else 'Cambios guardados',
                                  type='positive', position='top')
                        tick(force=True)

                    with ui.row().classes('justify-end w-full'):
                        ui.button('Volver', on_click=d.close).props('flat no-caps')
                        ui.button('Guardar', on_click=guardar).props('unelevated rounded no-caps color=primary')
            d.open()

        def alternar_cancha(k):
            try:
                store.set_cancha_activa(k.id, not k.activa)
                ui.notify('Cancha activada' if k.activa else 'Cancha desactivada: los jugadores ya no la ven',
                          type='positive', position='top')
            except ValueError as e:
                ui.notify(str(e), type='warning', position='top')
            tick(force=True)

        @ui.refreshable
        def canchas_ui():
            ks = store.canchas_de(state['slug'])
            with ui.row().classes('w-full items-center justify-between'):
                ui.label(f'{len(ks)} canchas en {complejo().nombre}').classes('font-extrabold')
                ui.button('Agregar cancha', icon='add', on_click=lambda: dialogo_cancha()).props(
                    'unelevated rounded no-caps color=accent text-color=dark')
            with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 w-full'):
                for k in ks:
                    with ui.column().classes('card-r p-4 gap-1 w-full'):
                        with ui.row().classes('justify-between items-start w-full no-wrap'):
                            ui.label(k.nombre).classes('font-extrabold text-base')
                            ui.html(f'<span class="chip chip-{"confirmada" if k.activa else "neutral"}">{"Activa" if k.activa else "Inactiva"}</span>')
                        ui.label(k.tipo).classes('text-sm muted')
                        ui.label(f'Seña {store.ars(k.sena)} por hora').classes('font-bold')
                        ui.label(f'{len(store.reservas_vigentes(k.id))} reservas vigentes').classes('text-xs muted')
                        with ui.row().classes('gap-2 mt-1'):
                            ui.button('Editar', icon='edit', on_click=lambda k=k: dialogo_cancha(k)).props(
                                'outline rounded no-caps size=sm color=primary')
                            ui.button('Desactivar' if k.activa else 'Activar', icon='visibility_off' if k.activa else 'visibility',
                                      on_click=lambda k=k: alternar_cancha(k)).props('flat rounded no-caps size=sm color=grey-8')

        # ------------------------------------------------ avisos
        @ui.refreshable
        def notifs_ui():
            ns = store.notificaciones_de(state['slug'])[:60]
            ui.label('Mails y WhatsApp simulados: no se envía nada real.').classes('text-sm muted')
            if not ns:
                ui.label('Todavía no hay avisos').classes('muted')
            for n in ns:
                with ui.row().classes('card-r p-3 no-wrap gap-3 items-start w-full'):
                    ui.icon('mail' if n.canal == 'Mail' else 'chat', color='primary' if n.canal == 'Mail' else 'positive', size='md')
                    with ui.column().classes('gap-0'):
                        ui.label(f'{n.canal} para {"el jugador" if n.para == "jugador" else "la cancha"} · '
                                 f'{store.fmt_fecha(n.creada.date())} {store.fmt_hora(n.creada)}').classes('text-xs muted')
                        ui.label(n.asunto).classes('font-bold')
                        ui.label(n.texto).classes('text-sm')

        with ui.tab_panels(tabs, value=t_res, animated=True).classes('w-full bg-transparent'):
            with ui.tab_panel(t_res).classes('p-0 gap-3 flex flex-col'):
                reservas_ui()
            with ui.tab_panel(t_gri).classes('p-0'):
                grilla_ui()
            with ui.tab_panel(t_can).classes('p-0 gap-3 flex flex-col'):
                canchas_ui()
            with ui.tab_panel(t_cfg).classes('p-0'):
                form_ui()
            with ui.tab_panel(t_not).classes('p-0 gap-2 flex flex-col'):
                notifs_ui()

        def tick(force: bool = False):
            if force or store.version != state['seen']:
                state['seen'] = store.version
                refrescar()

        ui.timer(2.0, tick)
