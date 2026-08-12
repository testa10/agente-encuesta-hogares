// Hook PostToolUse: complementa gate-notebook-sin-duplicados.cjs (que
// corre ANTES de ejecutar el notebook y mira solo el código fuente) con un
// chequeo que solo se puede hacer DESPUÉS de ejecutar: ¿alguna celda que
// llama a una función viz.plot_...() terminó sin producir ningún output?
// Eso pasa si la celda se comió una excepción en silencio o si la función
// devolvió algo que nunca se llegó a mostrar - un informe con una gráfica
// "invisible" es un fallo real, distinto del de duplicación, y hasta ahora
// solo se detectaba si alguien lo notaba a ojo revisando las ~48 celdas.
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

  const celdasSinOutput = [];
  (nb.cells || []).forEach((cell, i) => {
    if (cell.cell_type !== "code") return;
    const fuente = Array.isArray(cell.source) ? cell.source.join("") : cell.source || "";
    if (!/viz\.plot_\w+\(/.test(fuente)) return;

    const outs = cell.outputs || [];
    const tieneAlgo = outs.some((o) => {
      if (o.output_type === "error") return false; // un error no cuenta como output valido
      if (o.output_type === "stream") return (o.text || "").toString().trim().length > 0;
      return true; // execute_result / display_data con datos
    });
    if (!tieneAlgo) {
      celdasSinOutput.push(i);
    }
  });

  if (celdasSinOutput.length === 0) {
    process.exit(0);
  }

  process.stdout.write(
    JSON.stringify({
      decision: "block",
      reason:
        `El notebook "${rutaNotebook}" tiene ${celdasSinOutput.length} celda(s) que llaman a una función ` +
        `viz.plot_...() pero no produjeron ningún output visible: celdas ${celdasSinOutput.join(", ")}. ` +
        `Eso significa que esa gráfica quedaría ausente del informe final sin que nadie lo note. Revisá esas ` +
        `celdas (¿se tragó una excepción? ¿falta el .show() o la referencia a la figura?) antes de continuar.`,
    })
  );
  process.exit(0);
});
