// Hook PreToolUse: hace cumplir, a nivel de herramienta (no solo de texto
// de instrucciones), la regla innegociable de .claude/agents/encuesta-hogares.md
// de que el formulario de bienvenida (formularios.plantilla_bienvenida) es
// siempre la primera accion de la conversacion. Antes de esa llamada por
// Bash, solo se permite leer docs/METODOLOGIA.md; cualquier otro
// Bash/Read/Glob/Grep se bloquea con un motivo que el modelo puede leer y
// corregir en el momento, en vez de depender de que respete la instruccion
// por su cuenta.
const fs = require("fs");
const os = require("os");
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

  const sessionId = input.session_id || "sin-sesion";
  const marker = path.join(os.tmpdir(), `encuesta-hogares-bienvenida-${sessionId}.marker`);

  if (fs.existsSync(marker)) {
    process.exit(0);
  }

  const toolName = input.tool_name;
  const toolInput = input.tool_input || {};

  if (
    toolName === "Bash" &&
    typeof toolInput.command === "string" &&
    toolInput.command.includes("plantilla_bienvenida")
  ) {
    fs.writeFileSync(marker, "");
    process.exit(0);
  }

  if (
    toolName === "Read" &&
    typeof toolInput.file_path === "string" &&
    toolInput.file_path.toLowerCase().includes("metodologia.md")
  ) {
    process.exit(0);
  }

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason:
          "Regla innegociable del proyecto: antes de llamar por Bash a " +
          "formularios.plantilla_bienvenida(), no se puede usar ninguna otra " +
          "herramienta (la unica excepcion es leer docs/METODOLOGIA.md con " +
          "Read). Mostá el formulario de bienvenida primero.",
      },
    })
  );
  process.exit(0);
});
