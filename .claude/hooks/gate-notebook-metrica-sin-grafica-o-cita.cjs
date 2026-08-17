// Hook PreToolUse: hace cumplir, a nivel de herramienta, la regla de
// docs/CONVENCIONES_DE_GRAFICAS.md y .claude/agents/encuesta-hogares.md paso 5
// ("ninguna métrica queda solo como número... y cada gráfica lleva su
// justificación con fundamento, citando el principio o la fuente").
//
// Nace del mismo problema que ya resolvieron gate-notebook-sin-duplicados.cjs
// y gate-notebook-graficas-faltantes.cjs: una regla escrita en prosa, por sí
// sola, no se cumplió en el 100% de las ~44 celdas de un informe real (3
// métricas quedaron sin ninguna gráfica, y las justificaciones existentes
// eran solo una frase intuitiva, sin cita). Con tantas celdas casi
// idénticas por corrida, depender de que el modelo se acuerde en cada una
// no alcanza — por eso este chequeo corre antes de CUALQUIER ejecución de
// `jupyter nbconvert --execute`, sobre el notebook real, y bloquea si
// encuentra el patrón.
//
// Solo revisa celdas de métrica (encabezado "### N. Título", que es el que
// emite notebook_builder, o "#### Métrica N — ..."), no las secciones de
// infraestructura fija (introducción, Preparación de datos, presentación de
// cada tema, Panorama general, nota metodológica, Resumen analítico final)
// — esas no están numeradas como métrica y tienen su propio criterio, ya
// cubierto en otras partes de la metodología.
//
// El encabezado "### N. Título" se agregó al arreglar un fallo silencioso:
// el hook solo reconocía "#### Métrica N", que es como se escribían las
// celdas cuando se escribían a mano. Desde que las arma notebook_builder
// salen como "### N. Título", así que el hook encontraba cero métricas y
// dejaba pasar cualquier notebook — verde por no mirar nada. Se detectó
// corriendo el regex contra un notebook generado de verdad.
//
// La deteccion de "esto es un nbconvert --execute sobre tal notebook" vive
// en _lib_notebook_ejecutado.cjs (compartida con los otros dos hooks de
// notebook) - ver ese archivo para el bug real que motivo separarla.
const { resolverNotebookEjecutado } = require("./_lib_notebook_ejecutado.cjs");
const path = require("path");
const { registrar } = require("./_lib_bitacora.cjs");

const AUTORES_CONOCIDOS = [
  "Cleveland",
  "McGill",
  "Tufte",
  "Knaflic",
  "Few",
  // Ware (percepción) y Wilke (proporciones) ya estaban citados en
  // docs/CONVENCIONES_DE_GRAFICAS.md, pero faltaban acá: sus citas no
  // llevan año, así que tampoco las salvaba el patrón genérico de abajo.
  "Ware",
  "Wilke",
  "Nightingale",
  "Data Visualization Society",
  "Hofmann",
  "Wickham",
  "Kafadar",
  "Weissgerber",
  "storytellingwithdata",
];

function tieneCitaConFundamento(texto) {
  const tieneAutorConocido = AUTORES_CONOCIDOS.some((autor) => texto.includes(autor));
  if (tieneAutorConocido) return true;
  // Patrón genérico "(Autor, 1984)" / "(Autor & Otro, 1984)" para cubrir
  // fuentes que no estén en la lista de arriba.
  const patronGenerico = /\([A-ZÀ-Ý][\wÀ-ÿ.]+(?:\s*(?:&|y|et al\.?)\s*[A-ZÀ-Ý][\wÀ-ÿ.]+)?,?\s*\d{4}\)/;
  return patronGenerico.test(texto);
}

function fuente(cell) {
  return Array.isArray(cell.source) ? cell.source.join("") : cell.source || "";
}

let raw = "";
process.stdin.on("data", (chunk) => (raw += chunk));
process.stdin.on("end", () => {
  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    process.exit(0);
  }

  const toolName = input.tool_name;
  const toolInput = input.tool_input || {};
  const comando = toolInput.command;

  if (toolName !== "Bash" || typeof comando !== "string") {
    process.exit(0);
  }

  const resultado = resolverNotebookEjecutado(comando);
  if (!resultado) {
    process.exit(0);
  }
  const { ruta: rutaNotebook, nb } = resultado;

  const cells = nb.cells || [];
  // "#### Métrica 8 — ..." (celdas escritas a mano) y "### 8. ..." (las que
  // arma notebook_builder).
  // Uno o dos dígitos, no más: así "### 2019 vs 2025" (una comparación entre
  // años escrita a mano) no se cuela como si fuera la métrica 2019.
  const encabezadoMetrica = /^#{2,4}\s*(?:M[ée]trica\s+)?(\d{1,2})[.\s—-]/;
  // Un encabezado de nivel 2 cierra la métrica en curso: es la presentación
  // del tema siguiente o la nota metodológica, no parte de esta métrica.
  const encabezadoDeSeccion = /^##\s+(?!\d)/;

  const metricas = [];
  let actual = null;

  cells.forEach((cell) => {
    if (cell.cell_type === "markdown") {
      const texto = fuente(cell);
      const primeraLinea = texto.split("\n").find((l) => l.trim().length > 0) || "";
      const nuevoEncabezado = primeraLinea.match(encabezadoMetrica);

      if (nuevoEncabezado) {
        if (actual) metricas.push(actual);
        actual = { numero: nuevoEncabezado[1], markdown: [texto], tieneGrafica: false };
        return;
      }
      if (encabezadoDeSeccion.test(primeraLinea)) {
        if (actual) metricas.push(actual);
        actual = null;
        return;
      }
      if (actual) actual.markdown.push(texto);
      return;
    }
    if (cell.cell_type === "code" && actual) {
      if (/viz\.plot_\w+\(/.test(fuente(cell))) {
        actual.tieneGrafica = true;
      }
    }
  });
  if (actual) metricas.push(actual);

  const violaciones = [];
  metricas.forEach((m) => {
    const problemas = [];
    if (!m.tieneGrafica) problemas.push("sin ninguna gráfica (viz.plot_...)");
    if (!tieneCitaConFundamento(m.markdown.join("\n"))) problemas.push("sin cita/fuente en la justificación");
    if (problemas.length > 0) {
      violaciones.push(`Métrica ${m.numero}: ${problemas.join(" y ")}`);
    }
  });

  if (violaciones.length === 0) {
    process.exit(0);
  }

  registrar("hook_bloqueo", { hook: "notebook-metrica-sin-grafica-o-cita", ...{ violaciones: violaciones.length, notebook: path.basename(rutaNotebook) } });
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason:
          `El notebook "${rutaNotebook}" tiene ${violaciones.length} métrica(s) que incumplen ` +
          `docs/CONVENCIONES_DE_GRAFICAS.md: ${violaciones.join("; ")}. Cada métrica necesita su gráfica (nunca solo un número ` +
          `o tabla de texto — para una diferencia entre dos grupos, usá visualization.plot_dumbbell) y su celda de ` +
          `markdown tiene que citar el principio o la fuente que respalda el tipo de gráfica elegido. Corregí esas ` +
          `celdas con nbformat antes de volver a ejecutar el notebook.`,
      },
    })
  );
  process.exit(0);
});
