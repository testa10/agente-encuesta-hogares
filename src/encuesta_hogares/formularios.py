"""Formularios locales en el navegador: la forma en que el agente le
"pregunta" cosas al usuario, en vez de hacerlo por chat.

Todo corre en la propia computadora del usuario — no hay ninguna cuenta de
por medio (ni Microsoft Forms ni nada externo), no sale a internet, no
depende de ningún servicio de terceros. `mostrar_formulario()` levanta un
servidor mínimo en localhost, abre el navegador con el HTML del paso que
corresponda, y bloquea hasta que el usuario lo completa — devuelve la
respuesta como un diccionario de Python.

Las funciones `plantilla_*` arman el HTML de cada paso del flujo (ver
.claude/agents/encuesta-hogares.md para cuándo se usa cada una).
"""

import http.server
import json
import re
import subprocess
import threading
import traceback
from pathlib import Path

from . import bitacora


def _nombre_desde_html(html: str) -> str:
    """Extrae el texto del primer <h1> del HTML para identificar el
    formulario en la bitácora, sin depender de que cada llamada a
    mostrar_formulario() le pase un nombre a mano."""
    coincidencia = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if not coincidencia:
        return "formulario"
    texto = re.sub(r"<[^>]+>", "", coincidencia.group(1)).strip()
    return texto[:60] if texto else "formulario"

_ESTILO = """
:root { --rojo: #d1495b; --verde: #66a182; --texto: #24292f; --gris: #57606a; }
* { box-sizing: border-box; }
body {
  font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  background: linear-gradient(135deg, #f6f8fa 0%, #eef1f4 100%);
  margin: 0; min-height: 100vh; display: flex; align-items: center;
  justify-content: center; padding: 24px; color: var(--texto);
}
.tarjeta {
  background: white; border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.08);
  max-width: 640px; width: 100%; padding: 40px;
}
h1 { font-size: 22px; margin: 0 0 8px; }
.subtitulo { color: var(--gris); font-size: 14px; margin-bottom: 20px; }
.emoji { font-size: 40px; margin-bottom: 8px; }
.valor {
  background: #f0fdf4; border-left: 3px solid var(--verde);
  padding: 12px 16px; border-radius: 6px; margin: 20px 0;
  font-size: 14px;
}
.problema {
  background: #fef2f2; border-left: 3px solid var(--rojo);
  border-radius: 8px; padding: 14px 18px; font-size: 14px;
  line-height: 1.6; margin-bottom: 16px;
}
.original {
  background: #f6f8fa; border-radius: 8px; padding: 14px 18px;
  font-size: 14px; color: var(--gris); margin-bottom: 16px;
}
.carpeta {
  background: #f0fdf4; border-left: 3px solid var(--verde);
  padding: 12px 16px; border-radius: 6px; margin: 20px 0;
  font-family: Consolas, monospace; font-size: 13px; word-break: break-all;
}
label { display: block; font-weight: 600; margin-top: 20px; margin-bottom: 8px; }
select, input[type=number], textarea {
  width: 100%; padding: 12px 14px; font-size: 15px;
  border: 2px solid #d0d7de; border-radius: 8px; font-family: inherit;
}
select:focus, input:focus, textarea:focus { outline: none; border-color: var(--verde); }
ol { line-height: 1.9; font-size: 15px; padding-left: 22px; }
.barra-acciones { display: flex; gap: 10px; margin-bottom: 20px; }
.barra-acciones button {
  flex: none; width: auto; padding: 8px 16px; font-size: 13px;
  font-weight: 600; border-radius: 6px; cursor: pointer;
  border: 1px solid #d0d7de; background: #f6f8fa; color: var(--texto);
}
.categoria { margin-bottom: 26px; }
.categoria h2 {
  font-size: 14px; color: var(--verde); text-transform: uppercase;
  letter-spacing: 0.03em; border-bottom: 2px solid #eef1f4;
  padding-bottom: 6px; margin-bottom: 10px;
}
.metrica { display: flex; align-items: flex-start; gap: 10px; padding: 7px 0; cursor: pointer; }
.metrica input { margin-top: 4px; width: 18px; height: 18px; flex: none; cursor: pointer; }
.metrica .texto { font-size: 14px; line-height: 1.5; }
.metrica .explicacion { color: var(--gris); }
.otra { background: #f6f8fa; border-radius: 10px; padding: 16px 20px; margin: 20px 0; }
.opcion {
  display: block; border: 2px solid #d0d7de; border-radius: 10px;
  padding: 14px 16px; margin-bottom: 12px; cursor: pointer;
}
.opcion:hover { border-color: var(--verde); }
.opcion input { margin-right: 10px; }
button[type=submit] {
  margin-top: 16px; width: 100%; padding: 14px; font-size: 16px;
  font-weight: 600; color: white; background: var(--verde);
  border: none; border-radius: 8px; cursor: pointer;
}
button[type=submit]:hover { background: #559874; }
.listo { text-align: center; padding: 60px 0; }
.listo .check { font-size: 48px; margin-bottom: 12px; }
.spinner {
  width: 40px; height: 40px; margin: 0 auto 16px;
  border: 4px solid #eef1f4; border-top: 4px solid var(--verde);
  border-radius: 50%; animation: girar 0.8s linear infinite;
}
@keyframes girar { to { transform: rotate(360deg); } }
.boton-accion {
  display: block; width: 100%; text-align: center; text-decoration: none;
  margin-top: 16px; padding: 14px; font-size: 16px; font-weight: 600;
  border: none; border-radius: 8px; cursor: pointer; font-family: inherit;
}
.boton-primario { color: white; background: var(--verde); }
.boton-primario:hover { background: #559874; }
.boton-secundario { color: white; background: var(--gris); }
.boton-secundario:hover { background: #46505a; }
"""

_SCRIPT_LISTO = """
function mostrarListo() {
  document.getElementById('tarjeta').innerHTML = `
    <div class="listo">
      <div class="spinner"></div>
      <h1>Aguardá un momento...</h1>
      <p>Estamos procesando tu solicitud. Cuando esté listo el siguiente
      paso, se va a abrir solo en una pestaña nueva.</p>
    </div>`;
}
"""

_CATEGORIAS_METRICAS = [
    ("1 · Nivel económico y brecha digital", [
        (1, "Brecha digital por nivel económico", "compara, en una sola gráfica, el acceso a TV cable, internet, computadora y streaming según el nivel económico del hogar."),
        (2, "Acceso a TV cable por nivel económico", "qué porcentaje de hogares tiene TV cable en cada nivel económico."),
        (3, "Acceso a internet por nivel económico", "lo mismo, para la conexión a internet."),
        (4, "Acceso a celular por nivel económico", "lo mismo, para la tenencia de celular."),
        (5, "Diferencia entre el nivel económico más alto y el más bajo", "cuántos puntos porcentuales separan a esos dos grupos en el acceso a cada tecnología."),
    ]),
    ("2 · Pobreza", [
        (6, "Cuántos hogares son pobres o indigentes en Montevideo", "un resumen simple de contexto."),
        (7, "Acceso a TV cable según pobreza", "compara hogares pobres y no pobres."),
        (8, "Acceso a internet según pobreza", "lo mismo, para internet."),
        (9, "Acceso a celular según pobreza", "lo mismo, para celular."),
        (10, "Acceso a TV cable según indigencia", "la misma comparación, para hogares en situación de indigencia."),
    ]),
    ("3 · Territorio (barrios y país)", [
        (11, "Suscripción a TV cable por barrio", "qué barrios tienen más y menos hogares abonados."),
        (12, "Clasificación de barrios por nivel de suscripción", "agrupa los barrios en cuatro niveles."),
        (13, "Relación entre el barrio y el nivel económico", "si los barrios con más suscripción coinciden con los de mayor nivel económico."),
        (14, "Montevideo frente al resto del país", "cómo se compara con los demás departamentos."),
        (15, "Detalle de los barrios más y menos conectados", "una tabla puntual para consultar barrio por barrio."),
    ]),
    ("4 · Hogar y demografía", [
        (16, "Tamaño y composición del hogar según TV cable", "cantidad de personas, menores de 14 y ocupados, según conectividad."),
        (17, "Ingreso del hogar según conectividad a TV cable", "el ingreso típico del hogar (sin valor locativo), comparado entre hogares con y sin cable."),
        (18, "Tamaño y composición del hogar según internet", "la misma comparación del punto 16, pero según acceso a internet en vez de TV cable."),
        (19, "Situación ocupacional según TV cable", "ocupados/desocupados/inactivos, según conectividad."),
        (20, "Situación ocupacional según celular e internet", "la misma comparación, para esas tecnologías."),
    ]),
    ("5 · Vivienda y tecnología", [
        (21, "Condiciones de la vivienda según celular", "humedad, goteras, grietas, etc., según acceso a celular."),
        (22, "Condiciones de la vivienda según streaming", "lo mismo, según streaming."),
        (23, "Condiciones de la vivienda según internet", "lo mismo, según internet."),
        (24, "Qué tecnología marca más diferencia en la vivienda", "compara las tres tecnologías en una sola vista."),
        (25, "¿El streaming reemplaza a la TV cable?", "si conviven ambos servicios o no."),
    ]),
]

# Categoría aparte (no en _CATEGORIAS_METRICAS): solo existe para los años que
# tienen el archivo base_FIES_{año}.csv (ver config.datos_disponibles). El
# agente se la agrega a plantilla_catalogo() con incluir_fies=True cuando
# corresponde — nunca aparece si el año elegido no tiene esos datos.
_CATEGORIA_FIES = ("6 · Seguridad alimentaria (submuestra de hogares)", [
    (26, "Prevalencia de inseguridad alimentaria", "qué porcentaje de hogares está en inseguridad alimentaria moderada o severa, y cuántos en severa."),
    (27, "Inseguridad alimentaria por quintil de ingreso", "cómo varía entre el 20% de hogares con menos ingreso y el 20% con más."),
    (28, "Inseguridad alimentaria por región", "Montevideo comparado con el resto del país."),
    (29, "Diferencia entre el quintil más pobre y el más rico", "cuántos puntos porcentuales separan a esos dos grupos."),
    (30, "Inseguridad alimentaria severa por quintil de ingreso", "la misma comparación del punto 27, pero solo para el caso más grave."),
    (31, "Inseguridad alimentaria en hogares con menores de 18 años", "compara hogares con y sin menores de edad."),
    (32, "Inseguridad alimentaria en hogares con niños de 0 a 5 años", "la misma comparación, mirando solo a la primera infancia."),
])

# Igual que _CATEGORIA_FIES: solo existe para los años que tienen los 12
# archivos mensuales de empleo completos (ver config.datos_disponibles). A
# diferencia de FIES, esta categoría no se ofrece siempre que existe el
# dato — primero se le pregunta al usuario si la quiere, con
# plantilla_areas(), porque procesar los 12 meses es bastante más pesado
# que las demás categorías.
_CATEGORIA_EMPLEO = ("7 · Empleo", [
    (33, "Tasas de actividad, empleo y desempleo", "el panorama laboral general del año, promediado entre los 12 meses."),
    (34, "Brecha de género en el mercado laboral", "compara las tasas de actividad, empleo y desempleo entre hombres y mujeres."),
    (35, "Desempleo por departamento", "en qué departamentos la tasa de desempleo es más alta o más baja."),
    (36, "Informalidad laboral por sexo", "qué porcentaje de ocupados no aporta a la seguridad social, comparando hombres y mujeres."),
    (37, "Informalidad laboral por nivel educativo", "la misma comparación, según el nivel educativo del ocupado."),
    (38, "Subempleo por sexo", "qué porcentaje de ocupados querría trabajar más horas de las que tiene, comparando hombres y mujeres."),
    (39, "Desempleo juvenil (14 a 24 años) comparado con el resto", "si los jóvenes tienen una tasa de desempleo distinta al resto de la población activa."),
    (40, "Situación ocupacional por sector formal/informal", "si son más los empleados, cuentapropistas o empleadores en cada sector."),
])

# Igual que _CATEGORIA_EMPLEO: solo se ofrece si el usuario la eligió en
# plantilla_areas(). No incluye percepción de seguridad (v1) — no hay
# diccionario de valores publicado para esa variable, ver
# .claude/agents/encuesta-hogares.md.
_CATEGORIA_SEGURIDAD = ("8 · Seguridad y victimización", [
    (41, "Prevalencia de victimización por tipo de delito", "qué porcentaje de personas sufrió cada tipo de delito en el mes anterior a la entrevista (no es una cifra anual)."),
    (42, "Victimización general por sexo", "haber sufrido al menos un delito en el mes anterior a la entrevista, comparando hombres y mujeres."),
    (43, "Victimización general por departamento", "lo mismo, Montevideo comparado con el resto del país."),
    (44, "Tasa de comunicación a la policía por tipo de delito", "de quienes fueron víctimas, cuántos avisaron a la policía de algún modo."),
    (45, "Tasa de denuncia formal por tipo de delito", "de quienes fueron víctimas, cuántos hicieron la denuncia presencial en la comisaría."),
    (46, "Brecha entre comunicación informal y denuncia formal", "cuántos avisan a la policía pero no llegan a denunciar formalmente — la \"cifra negra\"."),
    (47, "Casos con violencia por tipo de delito", "de quienes fueron víctimas, en cuántos casos los autores amenazaron o ejercieron violencia."),
])


def mostrar_formulario(html: str, timeout: float | None = 1800) -> dict:
    """Sirve `html` en localhost, abre el navegador, y bloquea hasta que el
    usuario lo completa. Devuelve lo que haya mandado el formulario.
    """
    nombre = _nombre_desde_html(html)
    resultado: dict = {}
    evento = threading.Event()
    html_bytes = html.encode("utf-8")

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/favicon"):
                self.send_response(204)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)

        def do_POST(self):
            largo = int(self.headers.get("Content-Length", 0))
            cuerpo = self.rfile.read(largo)
            resultado.update(json.loads(cuerpo))
            respuesta = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(respuesta)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(respuesta)
            evento.set()

        def log_message(self, format, *args):
            pass

    bitacora.registrar("formulario_mostrado", nombre=nombre)
    try:
        # ThreadingHTTPServer: el navegador puede abrir mas de una conexion a
        # la vez. Un servidor de una sola conexion por vez se traba en ese
        # caso (visto en la practica con el formulario del catalogo de
        # metricas).
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler) as httpd:
            puerto = httpd.server_address[1]
            hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
            hilo.start()
            url = f"http://127.0.0.1:{puerto}/"
            # os.startfile()/webbrowser.open() resultaron poco confiables en
            # algunos entornos; "cmd /c start" es lo mas robusto en Windows.
            subprocess.run(["cmd", "/c", "start", "", url], check=False)
            completado = evento.wait(timeout=timeout)
            httpd.shutdown()
    except Exception as e:
        bitacora.registrar("formulario_error", nombre=nombre, mensaje=str(e), traceback=traceback.format_exc())
        raise

    bitacora.registrar("formulario_timeout" if not completado else "formulario_respondido", nombre=nombre)

    return resultado


def mostrar_finalizacion(pdf_path: str = "", html_path: str = "", timeout: float | None = 1800) -> dict:
    """Último paso: pantalla de agradecimiento con links que abren el PDF
    y/o el HTML del informe. A diferencia de `start` desde la terminal (poco
    confiable — se vio en la práctica que podía fallar en silencio), estos
    links los sirve este mismo servidor local, así que abrirlos es un click
    normal del navegador. Bloquea hasta que el usuario elige una opción.

    El resultado trae `{"accion": "terminar"}` o `{"accion": "nuevo_informe"}`
    — este último significa que el agente tiene que reiniciar el flujo desde
    el paso 1 (ver .claude/agents/encuesta-hogares.md), no terminar la
    conversación.
    """
    resultado: dict = {}
    evento = threading.Event()
    html = plantilla_finalizacion(pdf_disponible=bool(pdf_path), html_disponible=bool(html_path))
    html_bytes = html.encode("utf-8")

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/favicon"):
                self.send_response(204)
                self.end_headers()
                return
            if self.path == "/informe.pdf" and pdf_path:
                self._servir_archivo(pdf_path, "application/pdf")
                return
            if self.path == "/informe.html" and html_path:
                self._servir_archivo(html_path, "text/html; charset=utf-8")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)

        def _servir_archivo(self, ruta: str, content_type: str):
            datos = Path(ruta).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(datos)))
            self.send_header("Content-Disposition", f'inline; filename="{Path(ruta).name}"')
            self.end_headers()
            self.wfile.write(datos)

        def do_POST(self):
            largo = int(self.headers.get("Content-Length", 0))
            cuerpo = self.rfile.read(largo)
            resultado.update(json.loads(cuerpo))
            respuesta = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(respuesta)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(respuesta)
            evento.set()

        def log_message(self, format, *args):
            pass

    bitacora.registrar("finalizacion_mostrada", pdf_disponible=bool(pdf_path), html_disponible=bool(html_path))
    try:
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler) as httpd:
            puerto = httpd.server_address[1]
            hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
            hilo.start()
            url = f"http://127.0.0.1:{puerto}/"
            subprocess.run(["cmd", "/c", "start", "", url], check=False)
            completado = evento.wait(timeout=timeout)
            httpd.shutdown()
    except Exception as e:
        bitacora.registrar("finalizacion_error", mensaje=str(e), traceback=traceback.format_exc())
        raise

    bitacora.registrar("finalizacion_timeout" if not completado else "finalizacion_respondida")

    return resultado


def plantilla_finalizacion(pdf_disponible: bool, html_disponible: bool) -> str:
    """Último paso: agradecimiento + botones que abren el/los informe(s)."""
    botones = []
    if pdf_disponible:
        botones.append(
            '<a class="boton-accion boton-primario" href="/informe.pdf" target="_blank">'
            "📄 Abrir el informe en PDF</a>"
        )
    if html_disponible:
        botones.append(
            '<a class="boton-accion boton-primario" href="/informe.html" target="_blank">'
            "🌐 Abrir el informe en el navegador</a>"
        )
    botones_html = "\n".join(botones)
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Informe listo</title>
<style>{_ESTILO}</style></head><body>
<div class="tarjeta" id="tarjeta">
  <div class="emoji">✅</div>
  <h1>Tu informe fue creado con éxito</h1>
  <p class="subtitulo">Gracias por usar el agente de la Encuesta Continua de
  Hogares. Podés abrir tu informe con los botones de abajo, las veces que
  quieras.</p>
  {botones_html}
  <form id="form" style="margin-top:24px; display:flex; flex-direction:column; gap:10px;">
    <button type="submit" name="accion" value="nuevo_informe" class="boton-accion boton-secundario">🔄 Crear un nuevo informe</button>
    <button type="submit" name="accion" value="terminar" class="boton-accion boton-primario">Listo, gracias →</button>
  </form>
</div>
<script>
document.getElementById('form').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const accion = e.submitter ? e.submitter.value : 'terminar';
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{accion: accion}})}});
  const esNuevo = accion === 'nuevo_informe';
  document.getElementById('tarjeta').innerHTML = `
    <div class="listo">
      <div class="check">${{esNuevo ? '🔄' : '🙏'}}</div>
      <h1>${{esNuevo ? 'Preparando un nuevo informe…' : '¡Gracias!'}}</h1>
      <p>${{esNuevo
        ? 'Ya te vamos a abrir el primer formulario en una pestaña nueva.'
        : 'Ya podés cerrar esta pestaña.'}}</p>
    </div>`;
}});
</script></body></html>"""


def plantilla_arranque() -> str:
    """Pantalla de arranque de `abrir_agente.bat`, antes de levantar Claude
    Code: elegir entre empezar o salir con dos botones, sin escribir nada.
    La usa `arranque.py`, no el agente — es lo primero que ve el usuario,
    incluso antes de que exista una conversación.
    """
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Agente de la Encuesta de Hogares</title>
<style>{_ESTILO}</style></head><body>
<div class="tarjeta" id="tarjeta">
  <div class="emoji">👋</div>
  <h1>Bienvenido a su agente de IA especializado en Encuesta de Hogares</h1>
  <p class="subtitulo">Elija una opción para continuar.</p>
  <button type="button" class="boton-accion boton-primario" onclick="elegir('empezar')">Empezar con la encuesta de hogares</button>
  <button type="button" class="boton-accion boton-secundario" onclick="elegir('salir')">Salir del agente</button>
</div>
<script>
async function elegir(accion) {{
  document.getElementById('tarjeta').innerHTML = `
    <div class="listo">
      <div class="spinner"></div>
      <h1>${{accion === 'empezar' ? 'Iniciando…' : 'Cerrando…'}}</h1>
      <p>${{accion === 'empezar' ? 'Ya te vamos a abrir el primer formulario en una pestaña nueva.' : 'Si esta pestaña no se cierra sola, cerrala vos.'}}</p>
    </div>`;
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{accion: accion}})}});
  if (accion === 'salir') {{
    // Los navegadores solo dejan cerrar por script una pestaña que el
    // propio script abrió; esta "reapertura" es el truco habitual para
    // que igual lo permitan cuando la pestaña la abrió `cmd /c start`. No
    // funciona en todos los navegadores — por eso el texto de arriba
    // avisa que puede haber que cerrarla a mano.
    window.open('', '_self');
    window.close();
  }}
}}
</script></body></html>"""


def plantilla_bienvenida(anio_sugerido: str = "") -> str:
    """Paso 1: bienvenida + selección del año."""
    opcion_sugerida = (
        f'<option value="{anio_sugerido}" selected>{anio_sugerido}</option>'
        if anio_sugerido else ""
    )
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Encuesta Continua de Hogares — Agente de Análisis</title>
<style>{_ESTILO}</style></head><body>
<div class="tarjeta" id="tarjeta">
  <div class="emoji">👋</div>
  <h1>Encuesta Continua de Hogares</h1>
  <p>Soy el agente que convierte los datos crudos de la Encuesta Continua
  de Hogares del INE Uruguay en un informe claro y profesional.</p>
  <div class="valor">
    Vos elegís el año. Yo me encargo de cargar los datos, armar las
    gráficas, revisar que cada resultado tenga sentido estadístico, y
    entregarte un informe listo para leer o compartir — sin que tengas
    que tocar código ni saber estadística.
  </div>
  <form id="form">
    <label for="anio">¿Con qué año de la ECH arrancamos?</label>
    <input type="number" id="anio" name="anio" min="1996" max="2100"
      placeholder="ej. 2024" {"value=" + chr(34) + anio_sugerido + chr(34) if anio_sugerido else ""} required>
    <button type="submit">Empezar →</button>
  </form>
</div>
<script>
{_SCRIPT_LISTO}
document.getElementById('form').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const anio = document.getElementById('anio').value;
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{anio: anio}})}});
  mostrarListo();
}});
</script></body></html>"""


def plantilla_datos(anio: str, carpeta: str, ficha_url: str = "") -> str:
    """Pasos 2+3: instrucciones de descarga + confirmación, en una sola pantalla."""
    link_ficha = (
        f'<li>Entrá a <a href="{ficha_url}" target="_blank">la ficha de la ECH {anio} en el sitio del INE</a>.</li>'
        if ficha_url else
        f'<li>Buscá "Encuesta Continua de Hogares, Año {anio}" en el catálogo del INE.</li>'
    )
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Preparar los datos — ECH {anio}</title>
<style>{_ESTILO}</style></head><body>
<div class="tarjeta" id="tarjeta">
  <h1>Ubicar los datos de {anio}</h1>
  <div class="subtitulo">Ya te abrí la carpeta de destino en el Explorador de Windows.</div>
  <ol>
    {link_ficha}
    <li>Aceptá los términos y condiciones (eso lo hacés vos personalmente).</li>
    <li>Descargá la base en formato <b>SPSS (.SAV)</b> — viene en un .RAR.</li>
    <li>Extraelo con 7-Zip o WinRAR.</li>
    <li>Copiá los dos archivos <b>.sav</b> (Hogares y Personas) a esta carpeta:</li>
  </ol>
  <div class="carpeta">{carpeta}</div>
  <form id="form">
    <button type="submit">Ya guardé los dos archivos ahí →</button>
  </form>
</div>
<script>
{_SCRIPT_LISTO}
document.getElementById('form').addEventListener('submit', async (e) => {{
  e.preventDefault();
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{confirmado: true}})}});
  mostrarListo();
}});
</script></body></html>"""


def plantilla_areas(empleo_disponible: bool, seguridad_disponible: bool) -> str:
    """Paso 3.5 (opcional): antes del catálogo, si además de Hogares (que
    siempre se incluye) hay datos de Empleo y/o Seguridad para el año
    elegido, preguntale al usuario cuáles quiere sumar — selección
    múltiple, puede elegir ninguna, una o las dos. Solo llamar a esta
    función si `empleo_disponible or seguridad_disponible` es True; si
    ninguna está disponible, saltar directo al catálogo (no mostrar un
    formulario vacío).
    """
    opciones = []
    if empleo_disponible:
        opciones.append(
            '<label class="metrica"><input type="checkbox" name="area" value="empleo">'
            '<span class="texto"><b>Empleo</b> — <span class="explicacion">'
            "actividad, desempleo, informalidad y subempleo.</span></span></label>"
        )
    if seguridad_disponible:
        opciones.append(
            '<label class="metrica"><input type="checkbox" name="area" value="seguridad">'
            '<span class="texto"><b>Seguridad y victimización</b> — <span class="explicacion">'
            "percepción de seguridad y hechos delictivos sufridos por el hogar.</span></span></label>"
        )
    opciones_html = "\n".join(opciones)
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>¿Qué más querés incluir en el informe?</title>
<style>{_ESTILO}</style></head><body>
<div class="tarjeta" id="tarjeta">
  <h1>¿Querés sumar algo más al informe?</h1>
  <p class="subtitulo">El panorama de Hogares siempre se incluye. Para este
  año también hay datos de estas áreas — marcá las que te interesen (podés
  elegir varias, o ninguna).</p>
  <form id="form">
    {opciones_html}
    <button type="submit">Continuar →</button>
  </form>
</div>
<script>
{_SCRIPT_LISTO}
document.getElementById('form').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const areas = Array.from(document.querySelectorAll('input[name=area]:checked')).map(cb => cb.value);
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{areas: areas}})}});
  mostrarListo();
}});
</script></body></html>"""


def plantilla_catalogo(incluir_fies: bool = False, incluir_empleo: bool = False, incluir_seguridad: bool = False) -> str:
    """Paso 5: catálogo de métricas por categoría + propuesta libre. El informe
    final siempre se entrega en PDF y HTML — no se pregunta preferencia acá.

    `incluir_fies` agrega la categoría de seguridad alimentaria — solo debe
    ser True si `config.datos_disponibles(anio)["fies"]` es True para el año
    elegido. `incluir_empleo`/`incluir_seguridad` agregan Empleo y
    Seguridad/Victimización — solo deben ser True si el usuario las eligió
    en `plantilla_areas()` (no alcanza con que el dato exista, acá sí hay
    que preguntar antes, por lo pesado que es procesar los datos). Ver
    .claude/agents/encuesta-hogares.md. Si no corresponde, la categoría ni
    aparece: no es una opción que el usuario pueda marcar y quede vacía,
    directamente no existe en el formulario.
    """
    bloques = []
    barra = '<div class="barra-acciones"><button type="button" onclick="marcarTodas(true)">Seleccionar todas</button><button type="button" onclick="marcarTodas(false)">Ninguna</button></div>'
    categorias = (
        _CATEGORIAS_METRICAS
        + ([_CATEGORIA_FIES] if incluir_fies else [])
        + ([_CATEGORIA_EMPLEO] if incluir_empleo else [])
        + ([_CATEGORIA_SEGURIDAD] if incluir_seguridad else [])
    )
    for titulo, metricas in categorias:
        items = "\n".join(
            f'<label class="metrica"><input type="checkbox" name="m" value="{num}">'
            f'<span class="texto"><b>{nombre}</b> — <span class="explicacion">{explicacion}</span></span></label>'
            for num, nombre, explicacion in metricas
        )
        bloques.append(f'<div class="categoria"><h2>{titulo}</h2>{items}</div>')
    catalogo_html = "\n".join(bloques)

    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Elegí las métricas de tu informe</title>
<style>{_ESTILO}</style></head><body>
<div class="tarjeta" id="tarjeta" style="max-width:760px;">
  <h1>Elegí las métricas de tu informe</h1>
  <div class="subtitulo">Los datos básicos (barrio, composición del hogar) ya van incluidos siempre. Marcá lo que te interese agregar.</div>
  {barra}
  <form id="form">
    {catalogo_html}
    <div class="otra">
      <label style="margin-top:0;">¿Hay alguna otra métrica que se te ocurra y no esté en la lista?</label>
      <textarea id="otra_metrica" placeholder="Nombre y una breve explicación de qué mostraría (opcional)"></textarea>
    </div>
    <button type="submit">Confirmar selección →</button>
  </form>
</div>
<script>
{_SCRIPT_LISTO}
function marcarTodas(valor) {{
  document.querySelectorAll('input[name=m]').forEach(cb => cb.checked = valor);
}}
document.getElementById('form').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const metricas = Array.from(document.querySelectorAll('input[name=m]:checked')).map(cb => parseInt(cb.value));
  const otra = document.getElementById('otra_metrica').value.trim();
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{metricas: metricas, otra_metrica: otra}})}});
  mostrarListo();
}});
</script></body></html>"""


def plantilla_revision(propuesta: str, problema: str, alternativa: str) -> str:
    """Paso 7: revisión de una métrica propuesta por el usuario, con tres salidas."""
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Revisión de tu métrica propuesta</title>
<style>{_ESTILO}</style></head><body>
<div class="tarjeta" id="tarjeta">
  <h1>Revisé tu métrica propuesta</h1>
  <div class="original"><b>Tu propuesta:</b> "{propuesta}"</div>
  <div class="problema">⚠️ {problema}</div>
  <div class="valor">✅ <b>Alternativa que sí funciona:</b> {alternativa}</div>
  <form id="form">
    <label class="opcion"><input type="radio" name="decision" value="aceptar" checked>
      <b>Sí, usá esa alternativa</b></label>
    <label class="opcion"><input type="radio" name="decision" value="nueva">
      <b>Tengo otra idea distinta</b>, dejame proponer de nuevo</label>
    <label class="opcion"><input type="radio" name="decision" value="descartar">
      <b>Dejalo afuera del informe</b>, no hace falta esta métrica</label>
    <textarea id="texto_nueva" placeholder="Escribí tu nueva propuesta..." style="display:none;"></textarea>
    <button type="submit">Confirmar →</button>
  </form>
</div>
<script>
{_SCRIPT_LISTO}
document.querySelectorAll('input[name=decision]').forEach(r => {{
  r.addEventListener('change', () => {{
    document.getElementById('texto_nueva').style.display =
      (r.value === 'nueva' && r.checked) ? 'block' : 'none';
  }});
}});
document.getElementById('form').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const decision = document.querySelector('input[name=decision]:checked').value;
  const nueva_propuesta = document.getElementById('texto_nueva').value.trim();
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{decision: decision, nueva_propuesta: nueva_propuesta}})}});
  mostrarListo();
}});
</script></body></html>"""
