// Deja constancia en la bitacora cuando un hook BLOQUEA una herramienta.
//
// Nace de un hueco de observabilidad real: en una corrida de produccion el
// notebook se ejecuto TRES veces (83s + 98s + 83s = 4m25s, contra los ~83s
// de una sola pasada). La explicacion mas probable era que los hooks de
// notebook hubieran bloqueado y forzado correcciones -es justo para lo que
// existen-, pero no se pudo confirmar: los hooks no dejaban ningun rastro.
// Sin saber si esos 3 minutos son calidad bien invertida o retrabajo
// evitable, no se puede decidir si optimizarlos.
//
// Escribe en el mismo archivo JSONL que usa src/encuesta_hogares/bitacora.py
// (append de una linea por evento), asi el dueno del proyecto ve los
// bloqueos en la misma linea de tiempo que los formularios y los tiempos de
// cada paso, sin tener que cruzar dos fuentes.
const fs = require("fs");
const path = require("path");

// El .cjs vive en <proyecto>/.claude/hooks/, asi que la raiz esta dos
// niveles arriba. No se usa CLAUDE_PROJECT_DIR a proposito: esa variable
// llego vacia en produccion y dejo los seis hooks del proyecto sin correr
// durante dias (ver el historial de .claude/settings.json).
const RAIZ = path.resolve(__dirname, "..", "..");

// ENCUESTA_HOGARES_BITACORA permite redirigir el log a otro archivo. Existe
// para los tests: sin esto, cualquier test que corra un hook de verdad
// escribe en la bitacora REAL de quien tenga el proyecto en esa carpeta, y
// deja entradas indistinguibles de una corrida suya - justo en el archivo
// que existe para reconstruir que le paso. Es el mismo problema que ya
// habia obligado a redirigir bitacora.LOG_PATH del lado de Python.
// En produccion la variable no existe y se usa la ruta de siempre.
const LOG = process.env.ENCUESTA_HOGARES_BITACORA || path.join(RAIZ, "logs", "bitacora.jsonl");

function registrar(tipo, detalle) {
  try {
    fs.mkdirSync(path.dirname(LOG), { recursive: true });
    const linea = {
      timestamp: new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00"),
      tipo,
      ...detalle,
    };
    fs.appendFileSync(LOG, JSON.stringify(linea) + "\n", "utf-8");
  } catch {
    // Igual que bitacora.registrar() en Python: un fallo al escribir el
    // log nunca puede tirar abajo el flujo real de la persona. La bitacora
    // es de apoyo, jamas la causa de un problema nuevo.
  }
}

/** Registra el bloqueo y devuelve el JSON que Claude Code espera. */
function denegar(hook, motivo, detalle = {}) {
  registrar("hook_bloqueo", { hook, ...detalle });
  return JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: motivo,
    },
  });
}

module.exports = { registrar, denegar };
