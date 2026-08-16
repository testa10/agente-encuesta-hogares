// Hook PreToolUse: ninguna cifra del "Resumen analitico final" puede estar
// escrita a mano - toda tiene que existir de verdad en la salida ejecutada
// del notebook.
//
// Nace del unico lugar del informe donde el modelo TRANSCRIBE numeros a
// prosa. Todo el resto del informe calcula con pandas y muestra el
// resultado; el resumen final, en cambio, es texto que el modelo escribe
// citando porcentajes. Aunque los saque con Python (que es lo que mandan
// sus instrucciones), entre leerlos y escribirlos hay un paso a mano sin
// ningun control - y es la parte que mas gente lee.
//
// El chequeo es directo: cada cifra que aparece en el resumen tiene que
// encontrarse en algun output ya ejecutado del notebook. Si el modelo
// invento un numero, lo recordo mal, o lo copio de otra metrica, no va a
// coincidir con nada y esto bloquea antes de generar el informe.
//
// Deliberadamente NO se exige coincidencia exacta de decimales: el resumen
// redondea ("cerca del 40%") y eso es buena redaccion, no un error. Una
// cifra se acepta si algun numero real del notebook, redondeado a la misma
// cantidad de decimales, le da igual. Se ignoran los años (1900-2100) y los
// numeros enteros sueltos, que casi siempre son referencias a metricas o
// cantidades de categorias, no estadisticas.
const path = require("path");
const { resolverNotebookEjecutado } = require("./_lib_notebook_ejecutado.cjs");
const { registrar } = require("./_lib_bitacora.cjs");

const ENCABEZADO_RESUMEN = /resumen anal[ií]tico/i;

function textoDeCelda(cell) {
  return Array.isArray(cell.source) ? cell.source.join("") : cell.source || "";
}

function textoDeOutputs(cell) {
  let texto = "";
  for (const out of cell.outputs || []) {
    if (out.text) texto += Array.isArray(out.text) ? out.text.join("") : out.text;
    const plano = out.data && out.data["text/plain"];
    if (plano) texto += Array.isArray(plano) ? plano.join("") : plano;
  }
  return texto;
}

/** Numeros "de estadistica": con decimales, o enteros con % pegado. */
function cifrasDe(texto) {
  const encontradas = [];
  const patron = /(\d+(?:[.,]\d+)?)\s*%|(\d+[.,]\d+)/g;
  let m;
  while ((m = patron.exec(texto)) !== null) {
    const crudo = (m[1] !== undefined ? m[1] : m[2]).replace(",", ".");
    const valor = Number(crudo);
    if (!Number.isFinite(valor)) continue;
    if (Number.isInteger(valor) && valor >= 1900 && valor <= 2100) continue; // años
    const decimales = crudo.includes(".") ? crudo.split(".")[1].length : 0;
    encontradas.push({ texto: m[0].trim(), valor, decimales });
  }
  return encontradas;
}

function numerosDe(texto) {
  const valores = [];
  const patron = /\d+(?:[.,]\d+)?/g;
  let m;
  while ((m = patron.exec(texto)) !== null) {
    const valor = Number(m[0].replace(",", "."));
    if (Number.isFinite(valor)) valores.push(valor);
  }
  return valores;
}

function redondear(valor, decimales) {
  const factor = 10 ** decimales;
  return Math.round(valor * factor) / factor;
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

  const toolInput = input.tool_input || {};
  if (input.tool_name !== "Bash") process.exit(0);

  // resolverNotebookEjecutado recibe el COMANDO (no el input entero) y ya
  // devuelve el notebook parseado, no solo su ruta.
  const encontrado = resolverNotebookEjecutado(toolInput.command);
  if (!encontrado) process.exit(0);

  const rutaNotebook = encontrado.ruta;
  const celdas = encontrado.nb.cells || [];
  // Todos los numeros que el notebook de verdad calculo y mostro.
  const reales = [];
  for (const cell of celdas) {
    if (cell.cell_type === "code") reales.push(...numerosDe(textoDeOutputs(cell)));
  }
  if (reales.length === 0) process.exit(0); // notebook sin ejecutar todavia

  // Las celdas de markdown desde el encabezado del resumen en adelante.
  let dentroDelResumen = false;
  const sospechosas = [];
  for (const cell of celdas) {
    if (cell.cell_type !== "markdown") continue;
    const texto = textoDeCelda(cell);
    if (ENCABEZADO_RESUMEN.test(texto)) {
      dentroDelResumen = true;
      continue;
    }
    if (!dentroDelResumen) continue;
    for (const cifra of cifrasDe(texto)) {
      const existe = reales.some((real) => redondear(real, cifra.decimales) === cifra.valor);
      if (!existe) sospechosas.push(cifra.texto);
    }
  }

  if (sospechosas.length === 0) process.exit(0);

  const lista = [...new Set(sospechosas)].join(", ");
  registrar("hook_bloqueo", {
    hook: "resumen-cifras-inventadas",
    cifras: [...new Set(sospechosas)],
    notebook: path.basename(rutaNotebook),
  });
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason:
          `El "Resumen analítico final" cita cifras que no aparecen en ningún resultado ` +
          `ejecutado del notebook: ${lista}. Es el único lugar del informe donde los números ` +
          `se escriben a mano, así que un error de transcripción ahí no lo detecta nada más. ` +
          `Sacá cada número del resultado real (con Python, no de memoria) y volvé a escribir ` +
          `esa parte del resumen — si el número es correcto pero está redondeado a menos ` +
          `decimales de los que muestra el notebook, igual tiene que coincidir al redondear.`,
      },
    })
  );
  process.exit(0);
});
