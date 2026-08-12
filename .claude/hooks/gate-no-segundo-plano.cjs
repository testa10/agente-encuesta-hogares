// Hook PreToolUse: bloquea cualquier Bash corrido con run_in_background:true.
//
// Nace de un incidente real: el agente mostro la pantalla final
// (mostrar_finalizacion) en segundo plano por su cuenta - nada se lo
// pedia - y despues, para leer el resultado de esa tarea de fondo, tuvo
// un problema de codificacion y termino inventando un comando
// `powershell -Command "Get-Content ... -Encoding Byte"` para inspeccionar
// los bytes. Ese comando no esta en la lista de permisos del proyecto, asi
// que le mostro al usuario (alguien sin conocimientos tecnicos) un prompt
// de aprobacion de terminal - exactamente lo que todo este flujo de
// formularios existe para evitar.
//
// El patron correcto ya existe y funciona: correr todo en primer plano
// con un timeout largo (1800000ms) en la propia llamada Bash. Este hook
// no depende de que el modelo se acuerde de evitar el modo segundo plano -
// lo bloquea directamente.
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

  if (toolName !== "Bash" || toolInput.run_in_background !== true) {
    process.exit(0);
  }

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason:
          "Este proyecto nunca corre comandos Bash en segundo plano (run_in_background) - ni siquiera " +
          "formularios.mostrar_formulario()/mostrar_finalizacion(), que bloquean mucho tiempo esperando a la " +
          "persona. La forma correcta es correrlo en primer plano con un timeout largo (1800000ms) en la " +
          "propia llamada Bash. Correr en segundo plano obliga despues a leer el resultado desde un archivo " +
          "de salida interno de Claude Code, lo que en la practica llevo a inventar un comando de terminal " +
          "fuera de la lista de permisos (powershell) para inspeccionarlo, y eso le mostro al usuario un " +
          "prompt de aprobacion que este flujo entero existe para evitar. Repetí la llamada sin " +
          "run_in_background.",
      },
    })
  );
  process.exit(0);
});
