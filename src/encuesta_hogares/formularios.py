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

from . import bitacora, cierre, config


def _origen_es_propio(handler) -> bool:
    """¿La respuesta que llega viene de la página que sirve este mismo
    servidor, o de otro sitio?

    El servidor escucha en 127.0.0.1 con un puerto al azar, pero eso solo
    no alcanza: cualquier página web abierta en el navegador de la persona
    puede probar puertos de localhost y mandar una respuesta al formulario
    en su nombre (elegir un año, marcar métricas, o directamente cerrarle
    el flujo). El rango de puertos efímeros es lo bastante chico como para
    barrerlo desde JavaScript en segundos.

    El navegador manda `Origin` en todo POST, así que alcanza con exigir
    que sea el nuestro. Si no viene `Origin` (un cliente que no es un
    navegador, ej. los tests), se acepta: el riesgo que se está cerrando
    es específicamente el de una página de otro sitio.
    """
    origen = handler.headers.get("Origin")
    if origen is None:
        return True
    puerto = handler.server.server_address[1]
    return origen in (f"http://127.0.0.1:{puerto}", f"http://localhost:{puerto}")


def _rechazar_origen_ajeno(handler) -> bool:
    """Corta la respuesta con 403 si vino de otro sitio. Devuelve True si
    ya se respondió y quien llama tiene que abandonar el pedido."""
    if _origen_es_propio(handler):
        return False
    bitacora.registrar("formulario_origen_rechazado", origen=handler.headers.get("Origin"))
    handler.send_response(403)
    handler.send_header("Content-Length", "0")
    handler.end_headers()
    return True


# Las respuestas de estos formularios son unos pocos cientos de bytes (un
# año, una lista de números de métrica). Un tope generoso evita que un
# `Content-Length` enorme —malformado o malicioso— haga que el proceso
# intente reservar esa memoria de una.
_MAXIMO_CUERPO_EN_BYTES = 1_000_000


def _leer_cuerpo(handler) -> bytes | None:
    """Lee el cuerpo del POST validando su tamaño. Devuelve None (y ya
    respondió) si el pedido no sirve: antes, un `Content-Length` que no
    fuera un número tiraba un ValueError sin manejar dentro del hilo del
    servidor."""
    crudo = handler.headers.get("Content-Length", "0")
    try:
        largo = int(crudo)
    except (TypeError, ValueError):
        largo = -1
    if largo < 0 or largo > _MAXIMO_CUERPO_EN_BYTES:
        handler.send_response(400)
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return None
    return handler.rfile.read(largo)


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
.metrica { display: flex; align-items: flex-start; gap: 10px; padding: 7px 0 2px; cursor: pointer; }
.metrica input { margin-top: 4px; width: 18px; height: 18px; flex: none; cursor: pointer; }
.metrica .texto { font-size: 14px; line-height: 1.5; }
.metrica .explicacion { color: var(--gris); }
.metrica-fila { border-bottom: 1px solid #f0f2f4; }
.metrica-fila:last-child { border-bottom: none; }
.comparar-metrica {
  display: flex; align-items: center; gap: 6px; margin-left: 28px;
  padding: 0 0 8px; font-size: 12px; color: var(--gris); cursor: pointer;
}
.comparar-metrica input { width: 14px; height: 14px; cursor: pointer; }
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
        (7, "Clasificación de barrios por nivel de suscripción", "agrupa los barrios en cuatro niveles, de menor a mayor suscripción."),
    ]),
    "hogares": ("2 · Hogares", [
        (8, "Cuántos hogares son pobres o indigentes en Montevideo", "un resumen simple de contexto."),
        (9, "Jefatura de hogar femenina", "qué porcentaje de hogares tiene una jefa mujer, y cómo se relaciona con la pobreza del hogar."),
        (10, "Hacinamiento", "qué porcentaje de hogares tiene más de 2 personas por cuarto, según su nivel económico."),
        (11, "Tipos de hogar", "cuántos hogares son unipersonales, nucleares, extendidos, compuestos o sin núcleo."),
        (12, "Razón de dependencia demográfica", "cuántas personas menores de 15 o mayores de 65 hay por cada 100 en edad activa, comparado entre departamentos."),
        (13, "Hogares unipersonales de adultos mayores", "de los hogares de una sola persona, qué porcentaje corresponde a alguien de 65 años o más."),
    ]),
    "territorio": ("3 · Territorio", [
        (14, "Índice de desarrollo territorial por departamento", "un puntaje que combina pobreza, empleo, precariedad de vivienda y nivel económico en una sola mirada, ranking de los 19 departamentos."),
        (15, "Perfil territorial por departamento", "el detalle de cada componente del índice anterior, para entender por qué un departamento queda arriba o abajo."),
        (16, "Brecha territorial entre el departamento mejor y peor posicionado", "cuánto separa, en el índice, al departamento con mejor puntaje del que tiene el peor."),
    ]),
    "vivienda": ("4 · Vivienda", [
        (17, "Precariedad estructural de la vivienda", "qué porcentaje de hogares tiene al menos un problema estructural (humedad, goteras, grietas, etc.)."),
        (18, "Precariedad estructural según nivel económico", "si los hogares de nivel económico más bajo tienen más problemas estructurales."),
        (19, "Precariedad estructural por departamento", "en qué departamentos hay más y menos problemas estructurales de vivienda."),
        (20, "Brecha de precariedad entre el nivel económico más bajo y el más alto", "cuántos puntos porcentuales separan a esos dos grupos."),
        (21, "Carencias estructurales más frecuentes", "cuál es el problema de vivienda más común a nivel nacional, y cuáles le siguen."),
    ]),
}

# Categoría aparte (no en _CATEGORIAS_METRICAS): solo existe para los años que
# tienen el archivo base_FIES_{año}.csv (ver config.datos_disponibles). El
# agente se la agrega a plantilla_catalogo() con incluir_fies=True cuando
# corresponde — nunca aparece si el año elegido no tiene esos datos.
_CATEGORIA_FIES = ("5 · Seguridad alimentaria (submuestra de hogares)", [
    (22, "Prevalencia de inseguridad alimentaria", "qué porcentaje de hogares está en inseguridad alimentaria moderada o severa, y cuántos en severa."),
    (23, "Inseguridad alimentaria por quintil de ingreso", "cómo varía entre el 20% de hogares con menos ingreso y el 20% con más."),
    (24, "Inseguridad alimentaria por región", "Montevideo comparado con el resto del país."),
    (25, "Diferencia entre el quintil más pobre y el más rico", "cuántos puntos porcentuales separan a esos dos grupos."),
    (26, "Inseguridad alimentaria severa por quintil de ingreso", "la misma comparación del punto 23, pero solo para el caso más grave."),
    (27, "Inseguridad alimentaria en hogares con menores de 18 años", "compara hogares con y sin menores de edad."),
    (28, "Inseguridad alimentaria en hogares con niños de 0 a 5 años", "la misma comparación, mirando solo a la primera infancia."),
])

# Igual que _CATEGORIA_FIES: solo existe para los años que tienen los 12
# archivos mensuales de empleo completos (ver config.datos_disponibles). A
# diferencia de FIES, esta categoría no se ofrece siempre que existe el
# dato — primero se le pregunta al usuario si la quiere, con
# plantilla_areas(), porque procesar los 12 meses es bastante más pesado
# que las demás categorías.
_CATEGORIA_EMPLEO = ("6 · Empleo", [
    (29, "Tasas de actividad, empleo y desempleo", "el panorama laboral general del año, promediado entre los 12 meses."),
    (30, "Brecha de género en el mercado laboral", "compara las tasas de actividad, empleo y desempleo entre hombres y mujeres."),
    (31, "Desempleo por departamento", "en qué departamentos la tasa de desempleo es más alta o más baja."),
    (32, "Informalidad laboral por sexo", "qué porcentaje de ocupados no aporta a la seguridad social, comparando hombres y mujeres."),
    (33, "Informalidad laboral por nivel educativo", "la misma comparación, según el nivel educativo del ocupado."),
    (34, "Subempleo por sexo", "qué porcentaje de ocupados querría trabajar más horas de las que tiene, comparando hombres y mujeres."),
    (35, "Desempleo juvenil (14 a 24 años) comparado con el resto", "si los jóvenes tienen una tasa de desempleo distinta al resto de la población activa."),
    (36, "Situación ocupacional por sector formal/informal", "si son más los empleados, cuentapropistas o empleadores en cada sector."),
])

# Igual que _CATEGORIA_EMPLEO: solo se ofrece si el usuario la eligió en
# plantilla_areas(). No incluye percepción de seguridad (v1) — no hay
# diccionario de valores publicado para esa variable, ver
# .claude/agents/encuesta-hogares.md.
_CATEGORIA_SEGURIDAD = ("7 · Seguridad y victimización", [
    (37, "Prevalencia de victimización por tipo de delito", "qué porcentaje de personas sufrió cada tipo de delito en el mes anterior a la entrevista (no es una cifra anual)."),
    (38, "Victimización general por sexo", "haber sufrido al menos un delito en el mes anterior a la entrevista, comparando hombres y mujeres."),
    (39, "Victimización general por departamento", "lo mismo, Montevideo comparado con el resto del país."),
    (40, "Tasa de comunicación a la policía por tipo de delito", "de quienes fueron víctimas, cuántos avisaron a la policía de algún modo."),
    (41, "Tasa de denuncia formal por tipo de delito", "de quienes fueron víctimas, cuántos hicieron la denuncia presencial en la comisaría."),
    (42, "Brecha entre comunicación informal y denuncia formal", "cuántos avisan a la policía pero no llegan a denunciar formalmente — la \"cifra negra\"."),
    (43, "Casos con violencia por tipo de delito", "de quienes fueron víctimas, en cuántos casos los autores amenazaron o ejercieron violencia."),
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
            if _rechazar_origen_ajeno(self):
                return
            cuerpo = _leer_cuerpo(self)
            if cuerpo is None:
                return
            resultado.update(json.loads(cuerpo))
            respuesta = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(respuesta)))
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

    # Se guarda tambien lo que la persona respondio de verdad (no solo que
    # respondio) - antes, un desajuste entre lo que alguien creia haber
    # marcado y lo que terminaba en el informe (ej. tildar "Vivienda" y que
    # el informe final trajera otro bloque en su lugar) era indiagnosticable
    # despues del hecho: la bitacora solo decia "se respondio", nunca con
    # que contenido.
    if completado:
        bitacora.registrar("formulario_respondido", nombre=nombre, respuesta=resultado)
    else:
        bitacora.registrar("formulario_timeout", nombre=nombre)

    if not completado:
        # Nadie respondió dentro del timeout (la persona cerró la pestaña,
        # se fue, o lo que sea) - devolver {} tal cual hacía esto antes era
        # un riesgo real: el chequeo estándar que sigue a cualquier
        # mostrar_formulario() es `respuesta.get("salir_del_flujo")`, que
        # con un dict vacío da None (no True) y no dispara la salida
        # prolija - el siguiente acceso a un campo esperado (ej.
        # `respuesta["anio"]`) tiraba un KeyError sin manejar, exactamente
        # el tipo de falla cruda que este proyecto entero existe para
        # evitarle a alguien sin conocimientos técnicos. Devolver
        # salir_del_flujo=True hace que ese mismo chequeo, ya presente
        # después de cada formulario, también cubra este caso sin
        # necesitar ningún cambio en el resto del flujo.
        cierre.cerrar_consola(motivo="timeout_formulario")
        return {"salir_del_flujo": True, "motivo": "timeout"}

    # Salir sin terminar el informe: acá se termina la conversación (ver
    # .claude/agents/encuesta-hogares.md), así que también se cierra la
    # consola. Se hace acá y no en las instrucciones del agente a
    # propósito: es el mismo criterio que los hooks del proyecto — una
    # regla que depende de que el modelo se acuerde de cumplirla en cada
    # corrida no se cumple siempre, y esta en particular es la que dejaba
    # una ventana abierta en la cara de alguien que ya se quiso ir.
    if resultado.get("salir_del_flujo"):
        cierre.cerrar_consola(motivo="salir_del_flujo")

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
            if _rechazar_origen_ajeno(self):
                return
            cuerpo = _leer_cuerpo(self)
            if cuerpo is None:
                return
            resultado.update(json.loads(cuerpo))
            respuesta = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(respuesta)))
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

    if completado:
        bitacora.registrar("finalizacion_respondida", respuesta=resultado)
    else:
        bitacora.registrar("finalizacion_timeout")

    if not completado:
        # Mismo riesgo que en mostrar_formulario(): devolver {} dejaba que
        # el siguiente `respuesta["accion"]` tirara un KeyError sin
        # manejar. Acá no existe "salir_del_flujo" (esta pantalla ya es el
        # final) - el equivalente seguro es tratarlo como si la persona
        # hubiera elegido terminar, que es exactamente lo que ya sabe
        # manejar el paso 8 del agente.
        cierre.cerrar_consola(motivo="timeout_finalizacion")
        return {"accion": "terminar", "motivo": "timeout"}

    # "terminar" es el final real del flujo — el usuario ya tiene su
    # informe y apretó "Listo, gracias". "nuevo_informe" NO cierra nada:
    # ahí el agente reinicia desde el paso 1 en la misma conversación, así
    # que la consola tiene que seguir viva.
    if resultado.get("accion") == "terminar":
        cierre.cerrar_consola(motivo="terminar")

    return resultado


def plantilla_finalizacion(pdf_disponible: bool, html_disponible: bool) -> str:
    """Paso 8 (último): agradecimiento + botones que abren el/los informe(s)."""
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
  <h1>Bienvenido a tu agente de IA especializado en Encuesta de Hogares</h1>
  <p class="subtitulo">Elegí una opción para continuar.</p>
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


def plantilla_datos(anio: str, ficha_url: str = "") -> str:
    """Paso 2: instrucciones de descarga + confirmación, en una sola pantalla
    (la validación del paso 3 corre después, como código, sin formulario
    propio).

    La carpeta de destino se calcula acá adentro con `config.DATA_DIR`
    — nunca la recibe como parámetro de texto libre. Nace de un caso
    real: la instrucción le pedía a quien arma el notebook que "use la
    ruta real y absoluta, no un placeholder" al llamar a esta función,
    pero en una corrida real igual terminó mostrándose `data/2025`
    (relativa, con barras de Unix) en vez de la ruta real de Windows —
    un error de que alguien se olvide de calcularla bien no puede pasar
    si la función ya no le da esa responsabilidad a quien la llama.

    El formato de los archivos que ofrece el INE cambió más de una vez
    (`.sav` hasta 2023, un `.csv` combinado desde 2024, y en 2025 un
    paquete bastante más grande con varios `.csv`/`.xlsx`) — las
    instrucciones ya no prometen "dos archivos .sav": piden bajar y
    copiar todo lo que el catálogo ofrezca para Hogares, sin adivinar el
    formato exacto de antemano. El paso 3 (validación de estructura) es
    el que de verdad confirma después qué llegó y qué falta.
    """
    carpeta = str(config.DATA_DIR / str(anio))
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
    <li>Descargá los archivos de microdatos de <b>Hogares</b> que te ofrezca el catálogo — el formato y la cantidad de archivos varían según el año (puede ser un <b>.RAR</b> con archivos <b>.SAV</b>, uno o más <b>.CSV</b>, o una combinación). Si tenés dudas de cuáles bajar, descargá todo lo que aparezca en la sección de microdatos.</li>
    <li>Si algo vino comprimido (.RAR/.ZIP), extraelo con 7-Zip o WinRAR.</li>
    <li>Copiá <b>todos</b> los archivos que bajaste a esta carpeta — no hace falta que filtres cuáles sirven, eso se revisa automáticamente en el paso siguiente:</li>
  </ol>
  <div class="carpeta">{carpeta}</div>
  <form id="form">
    <button type="submit">Ya guardé los archivos ahí →</button>
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
         "composición del hogar, pobreza, jefatura, hacinamiento."),
        ("territorio", "Territorio",
         "un índice que combina pobreza, empleo, vivienda y nivel económico para comparar el desarrollo de los 19 departamentos."),
        ("vivienda", "Vivienda",
         "condiciones estructurales de la vivienda (humedad, goteras, grietas, etc.)."),
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
    """Paso 4: catálogo de métricas por categoría + propuesta libre. El informe
    final siempre se entrega en PDF y HTML — no se pregunta preferencia acá.

    **Todos los parámetros son opt-in y ninguno tiene que ver con qué datos
    existen, sino con qué bloques eligió el usuario en `plantilla_areas()`**
    (que ya filtró FIES/Empleo/Seguridad por disponibilidad real — acá ya no
    hace falta volver a chequear eso). Si un bloque no fue elegido, su
    categoría ni aparece: no es una opción marcable que quede vacía,
    directamente no existe en el formulario.

    **También trae la opción de comparar métricas puntuales con otros
    años** (`comparar_anios` en la respuesta — lista de enteros, vacía si
    no se pidió comparación; ej. `[2019, 2024, 2025]`). Nace de una
    sugerencia real registrada en la bitácora: antes había que escribirlo
    a mano en "otra métrica" cada vez; ahora es una opción de primera
    clase del catálogo, y admite cualquier cantidad de años (no solo
    uno). Ver .claude/agents/encuesta-hogares.md.

    **La comparación es por métrica, no todo o nada**: además de
    `comparar_anios` (los años, compartidos), la respuesta trae
    `metricas_comparadas` — el subconjunto de `metricas` que la persona
    marcó específicamente para comparar (lista de enteros, vacía si
    ninguna). Nace de una pregunta real: antes, tildar "comparar" aplicaba
    a *todas* las métricas elegidas en el catálogo, sin poder elegir solo
    alguna. El propio formulario ya filtra `metricas_comparadas` a
    números que también estén en `metricas` — no hace falta re-validar
    esa parte.
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
            f'<div class="metrica-fila">'
            f'<label class="metrica"><input type="checkbox" name="m" value="{num}">'
            f'<span class="texto"><b>{nombre}</b> — <span class="explicacion">{explicacion}</span></span></label>'
            f'<label class="comparar-metrica" style="display:none;">'
            f'<input type="checkbox" name="comparar_m" value="{num}"> comparar esta métrica entre años'
            f'</label></div>'
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
    <div class="comparar">
      <label class="metrica" style="margin-top:1rem;">
        <input type="checkbox" id="comparar_check">
        <span class="texto"><b>¿Comparar alguna métrica con otros años?</b> — <span class="explicacion">elegí los años acá abajo, y después marcá, en cada métrica que te interese, la casilla "comparar esta métrica entre años" — no hace falta que sean todas.</span></span>
      </label>
      <div id="comparar_anios_wrap" style="display:none; margin-top:0.5rem;">
        <label>¿Con qué años? (separados por coma)</label>
        <input type="text" id="comparar_anios" placeholder="ej. 2019, 2024, 2025">
      </div>
    </div>
    <div id="error_seleccion" style="display:none; color:#d1495b; margin-top:0.5rem; font-weight:600;">
      Elegí al menos una métrica del catálogo, o escribí una propuesta en "¿Hay alguna otra métrica...?", antes de continuar.
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
document.getElementById('comparar_check').addEventListener('change', (e) => {{
  document.getElementById('comparar_anios_wrap').style.display = e.target.checked ? 'block' : 'none';
  // Los checkboxes "comparar esta métrica entre años" (uno por fila) solo
  // se muestran una vez que se activó la comparación en general - antes
  // de eso, no tiene sentido decidir métrica por métrica algo que ni
  // siquiera está encendido.
  document.querySelectorAll('.comparar-metrica').forEach(el => {{
    el.style.display = e.target.checked ? 'flex' : 'none';
    if (!e.target.checked) el.querySelector('input').checked = false;
  }});
}});
document.getElementById('form').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const metricas = Array.from(document.querySelectorAll('input[name=m]:checked')).map(cb => parseInt(cb.value));
  const otra = document.getElementById('otra_metrica').value.trim();
  // "Comparar entre años" solo tiene sentido si hay al menos una métrica
  // elegida (se aplica "a cada métrica elegida", nunca a todo el
  // catálogo) - sin este chequeo, se podía confirmar con el catálogo
  // vacío y años para comparar marcados, un caso ambiguo que quedaba
  // librado a que el agente lo interpretara bien.
  if (metricas.length === 0 && otra === '') {{
    document.getElementById('error_seleccion').style.display = 'block';
    return;
  }}
  document.getElementById('error_seleccion').style.display = 'none';
  const compararCheck = document.getElementById('comparar_check').checked;
  // Separa por coma (o espacio, por si alguien no usa comas) y se queda
  // solo con los tokens que son un año de 4 dígitos - cualquier otra cosa
  // escrita ahí se descarta acá mismo, en vez de mandarla tal cual al agente.
  const comparar_anios = compararCheck
    ? [...new Set(document.getElementById('comparar_anios').value
        .split(/[,\\s]+/)
        .map(t => t.trim())
        .filter(t => /^[0-9]{{4}}$/.test(t))
        .map(t => parseInt(t)))]
      .sort((a, b) => a - b)
    : [];
  // Solo cuentan las métricas que además están en la lista principal -
  // si alguien tildó "comparar" en una fila y después destildó esa misma
  // métrica (o usó "Ninguna"), la casilla de comparar puede quedar
  // marcada pero oculta; filtrar acá evita mandar un número de
  // comparación para una métrica que ni siquiera va en el informe.
  const metricas_comparadas = compararCheck
    ? Array.from(document.querySelectorAll('input[name=comparar_m]:checked'))
        .map(cb => parseInt(cb.value))
        .filter(num => metricas.includes(num))
    : [];
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      metricas: metricas, otra_metrica: otra,
      comparar_anios: comparar_anios, metricas_comparadas: metricas_comparadas,
    }})}});
  mostrarListo();
}});
</script></body></html>"""


def plantilla_revision(propuesta: str, problema: str, alternativa: str) -> str:
    """Paso 6: revisión de una métrica propuesta por el usuario, con tres salidas."""
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
    const esNueva = r.value === 'nueva' && r.checked;
    const textoNueva = document.getElementById('texto_nueva');
    textoNueva.style.display = esNueva ? 'block' : 'none';
    // Requerido solo mientras está visible: si alguien elige "tengo otra
    // idea" y confirma sin escribir nada, antes se mandaba una propuesta
    // vacía sin que nadie lo notara - con esto el navegador no deja
    // enviar el formulario hasta que escriba algo.
    textoNueva.required = esNueva;
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
