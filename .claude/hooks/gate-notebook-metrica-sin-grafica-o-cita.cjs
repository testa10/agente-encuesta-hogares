// Hook PreToolUse: hace cumplir, a nivel de herramienta, la regla de
// docs/METODOLOGIA.md sección 9 y .claude/agents/encuesta-hogares.md paso 5
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
// Solo revisa celdas de métrica del catálogo (encabezado "#### Métrica N —
// ..."), no las secciones de infraestructura fija (Preparación de datos,
// Panorama general, Distribución por barrio, Composición de hogares,
// Resumen analítico final) — esas no están numeradas como métrica y tienen
// su propio criterio, ya cubierto en otras partes de la metodología.
const fs = require("fs");
const path = require("path");

const AUTORES_CONOCIDOS = [
  "Cleveland",
  "McGill",
  "Tufte",
  "Knaflic",
  "Few",
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
  if (!comando.includes("nbconvert") || !comando.includes("--execute")) {
    process.exit(0);
  }

  const match = comando.match(/["']?([^"'\s]+\.ipynb)["']?/);
  if (!match) {
    process.exit(0);
  }

  let rutaNotebook = match[1];
  if (!path.isAbsolute(rutaNotebook)) {
    rutaNotebook = path.join(process.cwd(), rutaNotebook);
  }
  if (!fs.existsSync(rutaNotebook)) {
    process.exit(0);
  }

  let nb;
  try {
    nb = JSON.parse(fs.readFileSync(rutaNotebook, "utf-8"));
  } catch {
    process.exit(0);
  }

  const cells = nb.cells || [];
  const encabezadoMetrica = /^#{2,4}\s*M[ée]trica\s+(\d+)/;

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

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason:
          `El notebook "${rutaNotebook}" tiene ${violaciones.length} métrica(s) que incumplen la sección 9 de ` +
          `docs/METODOLOGIA.md: ${violaciones.join("; ")}. Cada métrica necesita su gráfica (nunca solo un número ` +
          `o tabla de texto — para una diferencia entre dos grupos, usá visualization.plot_dumbbell) y su celda de ` +
          `markdown tiene que citar el principio o la fuente que respalda el tipo de gráfica elegido. Corregí esas ` +
          `celdas con nbformat antes de volver a ejecutar el notebook.`,
      },
    })
  );
  process.exit(0);
});
