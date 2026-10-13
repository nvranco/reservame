"""Estado en memoria de la demo: canchas, reservas y notificaciones simuladas.

Todo vive en variables de módulo. Si el servicio se reinicia, vuelven los datos
de ejemplo (ver `seed`). No hay base de datos.
"""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from urllib.parse import quote

try:
    from zoneinfo import ZoneInfo

    _TZ = ZoneInfo('America/Argentina/Buenos_Aires')
except Exception:  # sin tzdata
    _TZ = None

HORAS = list(range(16, 24))  # turnos de 1 h: 16:00 a 24:00
DIAS_VISIBLES = 7

PENDIENTE, CONFIRMADA, CANCELADA = 'Pendiente', 'Confirmada', 'Cancelada'
ESTADOS = (PENDIENTE, CONFIRMADA, CANCELADA)
TRANSICIONES = {
    PENDIENTE: (CONFIRMADA, CANCELADA),
    CONFIRMADA: (CANCELADA,),
    CANCELADA: (),
}
MOTIVOS = {
    'jugador': 'el jugador',
    'cancha': 'la cancha',
    'falta_sena': 'falta de seña',
}


def ahora() -> datetime:
    """Hora actual en Argentina, sin zona (naive)."""
    if _TZ is not None:
        return datetime.now(_TZ).replace(tzinfo=None)
    return datetime.utcnow() - timedelta(hours=3)


# ---------------------------------------------------------------- modelos

@dataclass
class Cancha:
    slug: str
    nombre: str
    direccion: str
    sena: int  # seña por hora, en ARS
    alias: str
    whatsapp: str
    plazo_horas: int = 2  # plazo de validación (y de cancelación del jugador)


@dataclass
class Reserva:
    id: int
    slug: str
    fecha: date
    hora: int
    nombre: str
    telefono: str
    estado: str
    origen: str  # 'web' | 'manual'
    creada: datetime
    cancelada_por: str | None = None


@dataclass
class Notificacion:
    id: int
    canal: str  # 'Mail' | 'WhatsApp'
    para: str  # 'jugador' | 'cancha'
    slug: str
    reserva_id: int | None
    asunto: str
    texto: str
    creada: datetime


canchas: dict[str, Cancha] = {}
reservas: dict[int, Reserva] = {}
bloqueos: dict[str, set[tuple[date, int]]] = {}
notificaciones: list[Notificacion] = []
version = 0  # sube con cada cambio; las pantallas lo miran para refrescarse

_ids = itertools.count(1)
_nids = itertools.count(1)


def _bump() -> None:
    global version
    version += 1


# ---------------------------------------------------------------- formato

_DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
_MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


def ars(n: int | float) -> str:
    return '$ ' + f'{int(n):,}'.replace(',', '.')


def dia_corto(d: date) -> str:
    return _DIAS[d.weekday()]


def fmt_fecha(d: date) -> str:
    hoy = ahora().date()
    if d == hoy:
        return 'Hoy ' + f'{d.day} {_MESES[d.month - 1]}'
    if d == hoy + timedelta(days=1):
        return 'Mañana ' + f'{d.day} {_MESES[d.month - 1]}'
    return f'{_DIAS[d.weekday()].capitalize()} {d.day} {_MESES[d.month - 1]}'


def fmt_fecha_plana(d: date) -> str:
    return f'{_DIAS[d.weekday()]} {d.day} de {_MESES[d.month - 1]}'


def fmt_turno(hora: int) -> str:
    return f'{hora % 24:02d}:00 a {(hora + 1) % 24:02d}:00'


def fmt_hora(dt: datetime) -> str:
    return dt.strftime('%H:%M')


def tel_wa(tel: str) -> str:
    """Normaliza un teléfono argentino al formato de wa.me (54 9 ...)."""
    d = re.sub(r'\D', '', tel).lstrip('0')
    if d.startswith('54'):
        return d
    if d.startswith('15'):
        d = d[2:]
    return '549' + d


def fechas() -> list[date]:
    hoy = ahora().date()
    return [hoy + timedelta(days=i) for i in range(DIAS_VISIBLES)]


# ---------------------------------------------------------------- consultas

def reserva_activa(slug: str, fecha: date, hora: int) -> Reserva | None:
    for r in reservas.values():
        if r.slug == slug and r.fecha == fecha and r.hora == hora and r.estado != CANCELADA:
            return r
    return None


def estado_slot(slug: str, fecha: date, hora: int) -> tuple[str, Reserva | None]:
    """('pasado' | 'ocupado' | 'bloqueado' | 'libre', reserva)."""
    if datetime.combine(fecha, datetime.min.time()) + timedelta(hours=hora) <= ahora():
        return 'pasado', None
    r = reserva_activa(slug, fecha, hora)
    if r:
        return 'ocupado', r
    if (fecha, hora) in bloqueos.get(slug, set()):
        return 'bloqueado', None
    return 'libre', None


def reservas_de(slug: str) -> list[Reserva]:
    rs = [r for r in reservas.values() if r.slug == slug]
    return sorted(rs, key=lambda r: (r.fecha, r.hora))


def notificaciones_de(slug: str, reserva_id: int | None = None, para: str | None = None) -> list[Notificacion]:
    out = [n for n in notificaciones if n.slug == slug]
    if reserva_id is not None:
        out = [n for n in out if n.reserva_id == reserva_id]
    if para:
        out = [n for n in out if n.para == para]
    return sorted(out, key=lambda n: n.creada, reverse=True)


def vence(r: Reserva) -> datetime:
    return r.creada + timedelta(hours=canchas[r.slug].plazo_horas)


def puede_cancelar_jugador(r: Reserva) -> bool:
    return r.estado != CANCELADA and ahora() < vence(r)


def mensaje_whatsapp(r: Reserva) -> str:
    c = canchas[r.slug]
    return (
        f'Hola! Reservé la cancha {c.nombre} para el {fmt_fecha_plana(r.fecha)} '
        f'de {fmt_turno(r.hora)}hs. '
        f'Soy {r.nombre} ({r.telefono}). Reserva #{r.id}. '
        f'Voy a transferir la seña de {ars(c.sena)} al alias {c.alias} '
        f'y te mando el comprobante por acá.'
    )


def link_whatsapp(r: Reserva) -> str:
    return f'https://wa.me/{canchas[r.slug].whatsapp}?text={quote(mensaje_whatsapp(r))}'


# ---------------------------------------------------------------- acciones

def _notificar(canal: str, para: str, r: Reserva, asunto: str, texto: str) -> None:
    notificaciones.append(
        Notificacion(next(_nids), canal, para, r.slug, r.id, asunto, texto, ahora())
    )


def _avisar(r: Reserva, para: str, asunto: str, texto: str) -> None:
    """Un aviso simulado por mail y otro por WhatsApp."""
    _notificar('Mail', para, r, asunto, texto)
    _notificar('WhatsApp', para, r, asunto, texto)


def _cuando(r: Reserva) -> str:
    return f'{fmt_fecha(r.fecha)}, {fmt_turno(r.hora)}hs'


def crear_reserva(slug: str, fecha: date, hora: int, nombre: str, telefono: str,
                  origen: str = 'web') -> Reserva:
    estado, _ = estado_slot(slug, fecha, hora)
    if estado != 'libre':
        raise ValueError('Ese horario ya no está disponible.')
    c = canchas[slug]
    manual = origen == 'manual'
    r = Reserva(next(_ids), slug, fecha, hora, nombre.strip(), telefono.strip(),
                CONFIRMADA if manual else PENDIENTE, origen, ahora())
    reservas[r.id] = r
    if not manual:
        _avisar(r, 'cancha', f'Nueva reserva pendiente de {r.nombre}',
                f'{r.nombre} ({r.telefono}) reservó {_cuando(r)}. Seña esperada: {ars(c.sena)}. '
                f'Validá la transferencia dentro de {c.plazo_horas} h.')
        _notificar('Mail', 'jugador', r, f'Recibimos tu reserva en {c.nombre}',
                   f'Reservaste {_cuando(r)}. Transferí {ars(c.sena)} al alias {c.alias} '
                   f'y mandá el comprobante por WhatsApp.')
    _bump()
    return r


def cambiar_estado(rid: int, nuevo: str, motivo: str = 'cancha') -> Reserva:
    r = reservas[rid]
    if nuevo not in TRANSICIONES[r.estado]:
        raise ValueError(f'No se puede pasar de {r.estado} a {nuevo}.')
    c = canchas[r.slug]
    r.estado = nuevo
    if nuevo == CONFIRMADA:
        _avisar(r, 'jugador', f'Reserva confirmada en {c.nombre}',
                f'¡Listo {r.nombre}! La cancha validó tu seña. Te esperamos {_cuando(r)}.')
    elif nuevo == CANCELADA:
        r.cancelada_por = motivo
        if motivo == 'jugador':
            _avisar(r, 'cancha', f'{r.nombre} canceló su reserva',
                    f'{r.nombre} canceló {_cuando(r)}. El horario volvió a quedar libre.')
            _notificar('Mail', 'jugador', r, 'Cancelaste tu reserva',
                       f'Tu reserva en {c.nombre} para {_cuando(r)} quedó cancelada.')
        else:
            why = 'por falta de seña' if motivo == 'falta_sena' else 'por la cancha'
            _avisar(r, 'jugador', f'Tu reserva en {c.nombre} fue cancelada',
                    f'Hola {r.nombre}, tu reserva de {_cuando(r)} fue cancelada {why}. '
                    f'Podés reservar otro horario desde el link de la cancha.')
    _bump()
    return r


def bloquear(slug: str, fecha: date, hora: int) -> None:
    if estado_slot(slug, fecha, hora)[0] != 'libre':
        raise ValueError('Solo se pueden bloquear horarios libres.')
    bloqueos.setdefault(slug, set()).add((fecha, hora))
    _bump()


def desbloquear(slug: str, fecha: date, hora: int) -> None:
    bloqueos.get(slug, set()).discard((fecha, hora))
    _bump()


def actualizar_cancha(slug: str, **campos) -> None:
    c = canchas[slug]
    for k, v in campos.items():
        setattr(c, k, v)
    _bump()


# ---------------------------------------------------------------- datos de ejemplo

def seed() -> None:
    canchas.clear(); reservas.clear(); bloqueos.clear(); notificaciones.clear()
    for c in (
        Cancha('la-redonda', 'La Redonda', 'Av. Libertador 1234, Vicente López', 8000,
               'laredonda.fc', '5491155501234'),
        Cancha('el-potrero', 'El Potrero', 'San Martín 890, Ramos Mejía', 6000,
               'potrero.canchas', '5491155505678'),
        Cancha('los-pibes', 'Los Pibes F5', 'Av. Cabildo 2150, Belgrano, CABA', 7500,
               'lospibes.futbol', '5491155509012'),
    ):
        canchas[c.slug] = c
        bloqueos[c.slug] = set()

    hoy = ahora().date()
    nombres = [('Martín Gómez', '11 5523 4411'), ('Lucas Pérez', '11 6120 8832'),
               ('Facundo Ríos', '11 4455 9087'), ('Sofía Mansilla', '11 3377 2210'),
               ('Tomás Acuña', '11 5098 7766'), ('Camila Ferrer', '11 2244 6655')]
    plan = {
        'la-redonda': [(1, 20, CONFIRMADA), (1, 21, PENDIENTE), (2, 19, CONFIRMADA),
                       (2, 22, PENDIENTE), (3, 20, CANCELADA), (4, 21, CONFIRMADA)],
        'el-potrero': [(1, 19, CONFIRMADA), (2, 20, PENDIENTE), (3, 21, CONFIRMADA),
                       (5, 18, PENDIENTE)],
        'los-pibes': [(1, 22, CONFIRMADA), (2, 21, CONFIRMADA), (3, 19, PENDIENTE)],
    }
    for slug, filas in plan.items():
        for i, (off, hora, estado) in enumerate(filas):
            nom, tel = nombres[(i + len(slug)) % len(nombres)]
            r = crear_reserva(slug, hoy + timedelta(days=off), hora, nom, tel)
            if estado == CONFIRMADA:
                cambiar_estado(r.id, CONFIRMADA)
            elif estado == CANCELADA:
                cambiar_estado(r.id, CANCELADA, 'falta_sena')
            r.creada = ahora() - timedelta(minutes=20 + 7 * i if estado == PENDIENTE else 600 + 90 * i)
    # un par de reservas manuales y bloqueos
    crear_reserva('la-redonda', hoy + timedelta(days=2), 21, 'Torneo del barrio', '11 5000 1111', 'manual')
    crear_reserva('el-potrero', hoy + timedelta(days=4), 20, 'Peña de los jueves', '11 5000 2222', 'manual')
    bloqueos['la-redonda'] |= {(hoy + timedelta(days=5), h) for h in (16, 17, 18)}
    bloqueos['los-pibes'].add((hoy + timedelta(days=3), 20))
    bloqueos['el-potrero'].add((hoy + timedelta(days=1), 23))
    # escalonar las horas de las notificaciones de ejemplo
    for i, n in enumerate(reversed(notificaciones)):
        n.creada = ahora() - timedelta(minutes=9 * i + 3)
    _bump()


seed()
