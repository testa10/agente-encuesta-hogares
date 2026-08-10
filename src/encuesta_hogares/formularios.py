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
import subprocess
import threading

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
.pdf { background: #f0fdf4; border-left: 3px solid var(--verde); border-radius: 8px; padding: 16px 20px; margin: 20px 0; }
.pdf .opciones { display: flex; gap: 20px; margin-top: 8px; }
.pdf .opciones label { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: normal; margin: 0; cursor: pointer; }
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
"""

_SCRIPT_LISTO = """
function mostrarListo() {
  document.getElementById('tarjeta').innerHTML = `
    <div class="listo">
      <div class="spinner"></div>
      <h1>Aguardá un momento...</h1>
      <p>Estamos procesando tu solicitud. Cuando esté listo el siguiente
      paso, se va a abrir solo en una pestaña nueva — podés cerrar esta.</p>
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


def mostrar_formulario(html: str, timeout: float | None = 1800) -> dict:
    """Sirve `html` en localhost, abre el navegador, y bloquea hasta que el
    usuario lo completa. Devuelve lo que haya mandado el formulario.
    """
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

    # ThreadingHTTPServer: el navegador puede abrir mas de una conexion a la
    # vez. Un servidor de una sola conexion por vez se traba en ese caso
    # (visto en la practica con el formulario del catalogo de metricas).
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler) as httpd:
        puerto = httpd.server_address[1]
        hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
        hilo.start()
        url = f"http://127.0.0.1:{puerto}/"
        # os.startfile()/webbrowser.open() resultaron poco confiables en
        # algunos entornos; "cmd /c start" es lo mas robusto en Windows.
        subprocess.run(["cmd", "/c", "start", "", url], check=False)
        evento.wait(timeout=timeout)
        httpd.shutdown()

    return resultado


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


def plantilla_catalogo() -> str:
    """Paso 5: catálogo de 25 métricas por categoría + propuesta libre + preferencia de PDF."""
    bloques = []
    barra = '<div class="barra-acciones"><button type="button" onclick="marcarTodas(true)">Seleccionar todas</button><button type="button" onclick="marcarTodas(false)">Ninguna</button></div>'
    for titulo, metricas in _CATEGORIAS_METRICAS:
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
    <div class="pdf">
      <label style="margin-top:0;">¿Querés además un informe en PDF, descargado automáticamente a tu carpeta de Descargas?</label>
      <div class="opciones">
        <label><input type="radio" name="pdf" value="si" checked> Sí (recomendado)</label>
        <label><input type="radio" name="pdf" value="no"> No, con el HTML alcanza</label>
      </div>
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
  const pdf = document.querySelector('input[name=pdf]:checked').value === 'si';
  await fetch('/', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{metricas: metricas, otra_metrica: otra, pdf: pdf}})}});
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
