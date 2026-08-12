// Hook PreToolUse: hace cumplir, a nivel de herramienta (no solo de texto
// de instrucciones), la regla de .claude/agents/encuesta-hogares.md sobre
// no duplicar graficas ("terminá con fig.show(), nunca con fig solo").
//
// Nace de que esa regla, aunque ya estaba escrita, no se cumplio en una
// corrida real: de 18 celdas con grafica, 14 terminaron con la variable
// "pelada" (ej. "fig") despues de asignarla con viz.plot_...(...), y cada
// una duplico su imagen en el informe final. Con ~48 celdas casi
// identicas por corrida, depender de que el modelo se acuerde en cada una
// no alcanza - por eso este chequeo corre antes de CUALQUIER ejecucion de
// `jupyter nbconvert --execute`, sobre el notebook real, y bloquea si
// encuentra el patron - en vez de descubrirlo recien en el informe final
// entregado al usuario.
const fs = require("fs");
const path = require("path");

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
    // No se pudo identificar el archivo del comando - no bloqueamos a
    // ciegas, mejor dejar pasar que romper un comando legitimo por un
    // parseo de texto que no cubre algun formato nuevo.
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

  const violaciones = [];
  (nb.cells || []).forEach((cell, i) => {
    if (cell.cell_type !== "code") return;
    const fuente = Array.isArray(cell.source) ? cell.source.join("") : cell.source || "";
    const lineas = fuente
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);
    if (lineas.length === 0) return;

    const ultima = lineas[lineas.length - 1];
    const esVariableSola = /^[A-Za-z_][A-Za-z0-9_]*$/.test(ultima);
    if (!esVariableSola) return;

    const patronAsignacion = new RegExp("^" + ultima.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\s*=\\s*viz\\.");
    const fueAsignadaPorViz = lineas.some((l) => patronAsignacion.test(l));
    if (fueAsignadaPorViz) {
      violaciones.push({ celda: i, variable: ultima });
    }
  });

  if (violaciones.length === 0) {
    process.exit(0);
  }

  const detalle = violaciones.map((v) => `celda ${v.celda} (variable "${v.variable}")`).join(", ");
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason:
          `El notebook "${rutaNotebook}" tiene ${violaciones.length} celda(s) que van a duplicar su gráfica ` +
          `en el output: ${detalle}. Cada una termina con la variable sola después de asignarla con ` +
          `viz.plot_...(...) - eso duplica la imagen (ver .claude/agents/encuesta-hogares.md, paso 5.2). ` +
          `Editá esas celdas con nbformat para que terminen en "<variable>.show()" (Plotly) o sin volver a ` +
          `nombrar la variable (matplotlib), y recién ahí volvé a ejecutar el notebook.`,
      },
    })
  );
  process.exit(0);
});
