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

from __future__ import annotations

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
.boton-salir {
  display: block; width: 100%; text-align: center; margin-top: 10px;
  padding: 10px; font-size: 13px; font-weight: 600; color: var(--gris);
  background: none; border: none; cursor: pointer; text-decoration: underline;
  font-family: inherit;
}
.boton-salir:hover { color: var(--rojo); }
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

# Botón presente en todos los pasos del formulario guiado (bienvenida hasta
# revisión de métrica propuesta) para que alguien que no quiere seguir
# pueda salir en el momento, en vez de que el agente quede esperando hasta
# 30 minutos a que la pestaña, cerrada sin contestar, llegue al timeout.
# No se usa en plantilla_arranque (ya tiene su propio botón "Salir del
# agente") ni en plantilla_finalizacion (ya es la pantalla de cierre, con
# sus propias dos opciones).
_BOTON_SALIR = '<button type="button" class="boton-salir" onclick="salirDelFlujo()">Salir sin terminar el informe</button>'

_SCRIPT_SALIR = """
function salirDelFlujo() {
  if (!confirm('¿Seguro que querés salir sin terminar el informe? Se pierde lo que elegiste en esta pantalla.')) return;
  fetch('/', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({salir_del_flujo: true})}).then(() => {
    document.getElementById('tarjeta').innerHTML = `
      <div class="listo">
        <div class="check">👋</div>
        <h1>Listo, no se generó ningún informe.</h1>
        <p>Ya podés cerrar esta pestaña.</p>
      </div>`;
  });
}
"""

# Diccionario, no lista: cada bloque tiene una clave estable
# ("brecha_digital", "hogares", etc.) que usan plantilla_areas() y
# plantilla_catalogo() para saber cuáles eligió el usuario — ninguno se
# incluye por defecto, todos son opt-in (ver plantilla_areas).
_CATEGORIAS_METRICAS = {
    "brecha_digital": ("1 · Brecha Digital", [
        (1, "Brecha digital por nivel económico", "compara, en una sola gráfica, el acceso a TV cable, internet, computadora y streaming según el nivel económico del hogar."),
        (2, "Brecha digital por cohorte generacional", "compara el acceso a cada tecnología entre generaciones (baby boomers, generación X, millennials, etc.), según la edad del jefe/a de hogar."),
        (3, "Calidad de la conexión a internet por nivel económico", "no es solo tener o no tener: compara sin conexión, solo por celular, o banda ancha fija, entre niveles económicos."),
        (4, "Brecha digital según jefatura de hogar", "compara el acceso a cada tecnología entre hogares con jefe hombre y jefa mujer."),
        (5, "Índice de acceso digital por nivel económico", "un puntaje de 0 a 4 (cuántas de las cuatro tecnologías tiene el hogar), comparado entre niveles económicos."),
        (6, "Adopción de tablets del Plan Ibirapitá", "en hogares con jefe/a de 65 años o más, qué porcentaje tiene una tablet de este programa estatal de inclusión digital."),
        (7, "Suscripción a TV cable por barrio", "qué barrios de Montevideo tienen más y menos hogares abonados — la dimensión geográfica de la brecha digital."),
        (8, "Clasificación de barrios por nivel de suscripción", "agrupa los barrios en cuatro niveles, de menor a mayor suscripción."),
        (9, "Relación entre el barrio y el nivel económico", "si los barrios con más suscripción coinciden con los de mayor nivel económico."),
        (10, "Montevideo frente al resto del país", "cómo se compara la penetración de TV cable con los demás departamentos."),
        (11, "¿El streaming reemplaza a la TV cable?", "si conviven ambos servicios o no."),
    ]),
    "hogares": ("2 · Hogares", [
        (12, "Cuántos hogares son pobres o indigentes en Montevideo", "un resumen simple de contexto."),
        (13, "Jefatura de hogar femenina", "qué porcentaje de hogares tiene una jefa mujer, y cómo se relaciona con la pobreza del hogar."),
        (14, "Hacinamiento", "qué porcentaje de hogares tiene más de 2 personas por cuarto, según su nivel económico."),
        (15, "Tipos de hogar", "cuántos hogares son unipersonales, nucleares, extendidos, compuestos o sin núcleo."),
        (16, "Razón de dependencia demográfica", "cuántas personas menores de 15 o mayores de 65 hay por cada 100 en edad activa, comparado entre departamentos."),
        (17, "Hogares unipersonales de adultos mayores", "de los hogares de una sola persona, qué porcentaje corresponde a alguien de 65 años o más."),
    ]),
    "territorio": ("3 · Territorio", [
        (18, "Índice de desarrollo territorial por departamento", "un puntaje que combina pobreza, empleo, precariedad de vivienda y nivel económico en una sola mirada, ranking de los 19 departamentos."),
        (19, "Perfil territorial por departamento", "el detalle de cada componente del índice anterior, para entender por qué un departamento queda arriba o abajo."),
        (20, "Brecha territorial entre el departamento mejor y peor posicionado", "cuánto separa, en el índice, al departamento con mejor puntaje del que tiene el peor."),
    ]),
    "vivienda": ("4 · Vivienda", [
        (21, "Precariedad estructural de la vivienda", "qué porcentaje de hogares tiene al menos un problema estructural (humedad, goteras, grietas, etc.)."),
        (22, "Precariedad estructural según nivel económico", "si los hogares de nivel económico más bajo tienen más problemas estructurales."),
        (23, "Precariedad estructural por departamento", "en qué departamentos hay más y menos problemas estructurales de vivienda."),
        (24, "Brecha de precariedad entre el nivel económico más bajo y el más alto", "cuántos puntos porcentuales separan a esos dos grupos."),
        (25, "Carencias estructurales más frecuentes", "cuál es el problema de vivienda más común a nivel nacional, y cuáles le siguen."),
    ]),
}

# Categoría aparte (no en _CATEGORIAS_METRICAS): solo existe para los años que
# tienen el archivo base_FIES_{año}.csv (ver config.datos_disponibles). El
# agente se la agrega a plantilla_catalogo() con incluir_fies=True cuando
# corresponde — nunca aparece si el año elegido no tiene esos datos.
_CATEGORIA_FIES = ("5 · Seguridad alimentaria (submuestra de hogares)", [
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
_CATEGORIA_EMPLEO = ("6 · Empleo", [
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
_CATEGORIA_SEGURIDAD = ("7 · Seguridad y victimización", [
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
  {_BOTON_SALIR}
</div>
<script>
{_SCRIPT_LISTO}
{_SCRIPT_SALIR}
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
  {_BOTON_SALIR}
</div>
<script>
{_SCRIPT_LISTO}
{_SCRIPT_SALIR}
document.getElementById('form').addEventListener('submit', async (e) => {{
  e.preventDefault();
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{confirmado: true}})}});
  mostrarListo();
}});
</script></body></html>"""


def plantilla_areas(fies_disponible: bool, empleo_disponible: bool, seguridad_disponible: bool) -> str:
    """Paso 3.5: qué bloques temáticos quiere el usuario en el informe.

    **Ningún bloque viene marcado por defecto ni se asume — ni siquiera
    Brecha Digital o Hogares.** Antes, esos dos (más Territorio y Vivienda)
    se incluían siempre en el catálogo sin preguntar, dando por sentado que
    a cualquiera le interesa la penetración tecnológica; ahora son una
    elección más, al mismo nivel que FIES/Empleo/Seguridad — nadie ve nada
    de ningún bloque que no haya marcado acá primero.

    Brecha Digital, Hogares, Territorio y Vivienda siempre se ofrecen como
    opción (dependen únicamente de los datos de Hogares, que ya se validó
    que existen en el paso 3). FIES/Empleo/Seguridad solo se ofrecen si
    `config.datos_disponibles(anio)` los tiene para el año elegido — pasale
    esos tres flags tal cual salen de ahí.
    """
    opciones = [
        ("brecha_digital", "Brecha Digital",
         "acceso, calidad de conexión y uso de tecnología (TV cable, internet, computadora, streaming) en los hogares."),
        ("hogares", "Hogares",
         "composición del hogar, pobreza, jefatura, hacinamiento — sin ninguna variable de tecnología."),
        ("territorio", "Territorio",
         "un índice que combina pobreza, empleo, vivienda y nivel económico para comparar el desarrollo de los 19 departamentos."),
        ("vivienda", "Vivienda",
         "condiciones estructurales de la vivienda (humedad, goteras, grietas, etc.), sin relación con la tenencia de tecnología."),
    ]
    if fies_disponible:
        opciones.append((
            "fies", "Seguridad alimentaria",
            "inseguridad alimentaria en los hogares (submuestra), según ingreso y composición del hogar.",
        ))
    if empleo_disponible:
        opciones.append(("empleo", "Empleo", "actividad, desempleo, informalidad y subempleo."))
    if seguridad_disponible:
        opciones.append((
            "seguridad", "Seguridad y victimización",
            "percepción de seguridad y hechos delictivos sufridos por el hogar.",
        ))

    opciones_html = "\n".join(
        f'<label class="metrica"><input type="checkbox" name="area" value="{valor}">'
        f'<span class="texto"><b>{nombre}</b> — <span class="explicacion">{explicacion}</span></span></label>'
        for valor, nombre, explicacion in opciones
    )
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>¿Qué querés incluir en el informe?</title>
<style>{_ESTILO}</style></head><body>
<div class="tarjeta" id="tarjeta">
  <h1>¿Qué querés incluir en el informe?</h1>
  <p class="subtitulo">Marcá los temas que te interesen — podés elegir uno,
  varios, o todos. Ninguno viene marcado de antemano.</p>
  <form id="form">
    {opciones_html}
    <button type="submit">Continuar →</button>
  </form>
  {_BOTON_SALIR}
</div>
<script>
{_SCRIPT_LISTO}
{_SCRIPT_SALIR}
document.getElementById('form').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const areas = Array.from(document.querySelectorAll('input[name=area]:checked')).map(cb => cb.value);
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{areas: areas}})}});
  mostrarListo();
}});
</script></body></html>"""


def plantilla_catalogo(
    incluir_brecha_digital: bool = False,
    incluir_hogares: bool = False,
    incluir_territorio: bool = False,
    incluir_vivienda: bool = False,
    incluir_fies: bool = False,
    incluir_empleo: bool = False,
    incluir_seguridad: bool = False,
) -> str:
    """Paso 5: catálogo de métricas por categoría + propuesta libre. El informe
    final siempre se entrega en PDF y HTML — no se pregunta preferencia acá.

    **Todos los parámetros son opt-in y ninguno tiene que ver con qué datos
    existen, sino con qué bloques eligió el usuario en `plantilla_areas()`**
    (que ya filtró FIES/Empleo/Seguridad por disponibilidad real — acá ya no
    hace falta volver a chequear eso). Si un bloque no fue elegido, su
    categoría ni aparece: no es una opción marcable que quede vacía,
    directamente no existe en el formulario. Ver
    .claude/agents/encuesta-hogares.md.
    """
    bloques = []
    barra = '<div class="barra-acciones"><button type="button" onclick="marcarTodas(true)">Seleccionar todas</button><button type="button" onclick="marcarTodas(false)">Ninguna</button></div>'
    categorias = []
    if incluir_brecha_digital:
        categorias.append(_CATEGORIAS_METRICAS["brecha_digital"])
    if incluir_hogares:
        categorias.append(_CATEGORIAS_METRICAS["hogares"])
    if incluir_territorio:
        categorias.append(_CATEGORIAS_METRICAS["territorio"])
    if incluir_vivienda:
        categorias.append(_CATEGORIAS_METRICAS["vivienda"])
    if incluir_fies:
        categorias.append(_CATEGORIA_FIES)
    if incluir_empleo:
        categorias.append(_CATEGORIA_EMPLEO)
    if incluir_seguridad:
        categorias.append(_CATEGORIA_SEGURIDAD)
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
  <div class="subtitulo">Estas son las métricas de los temas que elegiste. Marcá las que te interesen — ninguna viene tildada de antemano.</div>
  {barra}
  <form id="form">
    {catalogo_html}
    <div class="otra">
      <label style="margin-top:0;">¿Hay alguna otra métrica que se te ocurra y no esté en la lista?</label>
      <textarea id="otra_metrica" placeholder="Nombre y una breve explicación de qué mostraría (opcional)"></textarea>
    </div>
    <button type="submit">Confirmar selección →</button>
  </form>
  {_BOTON_SALIR}
</div>
<script>
{_SCRIPT_LISTO}
{_SCRIPT_SALIR}
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
  {_BOTON_SALIR}
</div>
<script>
{_SCRIPT_LISTO}
{_SCRIPT_SALIR}
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
