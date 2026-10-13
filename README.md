# ⚽ Reservame (demo)

Demo web de **Reservame**: reservar canchas de fútbol con seña, sin coordinar por WhatsApp.
Pensada para mostrarla: datos de ejemplo hardcodeados, todo en memoria y todo simulado.

**Stack:** Python + [NiceGUI](https://nicegui.io). Un solo servicio, sin base de datos.

## Qué hace

**Jugador** (`/cancha/la-redonda`, `/cancha/el-potrero`, `/cancha/los-pibes`)
1. Elige primero la **cancha** del complejo (cada una con su tipo y su seña).
2. Ve la grilla de horarios libres y ocupados de los próximos 7 días.
3. Elige un horario, deja nombre y teléfono y reserva.
4. Pantalla final con los pasos: botón **Abrir WhatsApp** (mensaje prefijado, visible), transferir la seña al alias de la cancha y esperar la validación dentro del plazo (por defecto 2 h). El comprobante lo manda el jugador por WhatsApp; la app no lo toca.
5. Puede cancelar su reserva dentro del plazo.

**Admin** (`/admin`, botón "Entrar como admin", sin contraseña)
- Un complejo con **varias canchas**: agregar, editar (nombre, tipo, seña por hora), activar o desactivar cada una. Cada cancha tiene su propia grilla.
- Editar el complejo: nombre, dirección, alias, WhatsApp y plazo de validación.
- Link público del complejo con botón para copiar.
- Reservas con estados **Pendiente → Confirmada → Cancelada** (la cancelada es final).
- Reservas manuales y bloqueo de horarios desde la grilla.
- Lista de avisos simulados (mails y WhatsApp). Al cancelar una reserva, el jugador recibe un aviso simulado que ve en su pantalla.

**Simulación:** abrí el link de la cancha en otra pestaña o en el celular y reservá; el admin lo ve en ~2 segundos, y lo que cambie el admin se refleja en la pantalla del jugador.

Sin login real, sin pasarela de pagos, sin envío real de mails ni de WhatsApp. Si el servicio se reinicia, vuelven los datos de ejemplo.

## Correr en local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```
Abrí http://localhost:8080 (o definí `PORT`).

## Deploy en Railway

1. Subí el repo a GitHub.
2. En Railway: **New Project → Deploy from GitHub repo** y elegí este repo. Nixpacks detecta Python con `requirements.txt` y usa el `Procfile` (`python -m app.main`), que escucha en `$PORT`.
3. En **Settings → Networking → Generate Domain** pedí el dominio público (ej. `reservame.up.railway.app`).
4. Dejá una sola réplica: el estado vive en la memoria del proceso.

## Estructura

```
app/main.py         arranque (ui.run, PORT)
app/store.py        modelo, reglas de estado, avisos simulados y datos de ejemplo
app/theme.py        tema verde cancha y componentes compartidos
app/pages/          home, admin y vista del jugador
```
