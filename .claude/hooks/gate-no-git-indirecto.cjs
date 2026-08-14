// Hook PreToolUse: bloquea invocar git de forma indirecta, escondida dentro
// de otro intérprete (ej. `python -c "import subprocess; subprocess.run(['git','push'])"`,
// `powershell -Command "... git ..."`, `node -e "...execSync('git ...')..."`).
//
// Nace de una evaluación de seguridad real de este proyecto: las reglas de
// permisos de .claude/settings.json ("deny": ["Bash(git *)", "Bash(*git *)"])
// solo miran el texto del comando Bash de forma literal - coinciden si el
// comando empieza con "git " o contiene la subcadena exacta "git " en algún
// lado. Alcanza para bloquear un uso directo, pero un comando que arma la
// palabra "git" dentro de una lista de Python (`['git','push']`) o de otro
// intérprete no contiene esa subcadena exacta y pasa esas reglas sin que
// salte ningún aviso. Verificado en la práctica: un `subprocess.run(['git',
// '--version'])` corrió sin ningún bloqueo.
//
// Este hook no reemplaza esas reglas - las complementa mirando si la
// palabra "git" aparece en una posición que NO es una invocación directa de
// comando (después de `&&`, `;`, `|`, o al principio del comando, con o sin
// `./`/`cmd /c` adelante). Si "git" aparece en cualquier otro lugar del
// comando, se asume indirecto y se bloquea. El agente encuesta-hogares no
// tiene ninguna razón legítima para invocar git ni directa ni
// indirectamente (ver CLAUDE.md, "El agente encuesta-hogares sigue sin
// permiso de usar git"); la sesión principal sí publica con git en su forma
// directa de siempre (`git add`/`git commit`/`git push`, encadenados con
// `&&` desde `cd`), que este hook deja pasar sin tocar.
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
  const command = toolInput.command;

  if (toolName !== "Bash" || typeof command !== "string") {
    process.exit(0);
  }

  // git en posición de comando: al principio, o después de && ; | - con o
  // sin ./, .\, cmd /c, cmd //c adelante.
  const invocacionDirecta =
    /(^|&&|;|\|)\s*(\.[\\/]|cmd\s+\/{1,2}c\s+)?git(\.exe)?(\s|$)/i;
  const contieneGit = /\bgit\b/i;

  if (invocacionDirecta.test(command)) {
    process.exit(0);
  }
  if (!contieneGit.test(command)) {
    process.exit(0);
  }

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason:
          "Este comando menciona 'git' sin invocarlo directamente como programa - parece un intento de " +
          "correr git desde adentro de otro intérprete (python, powershell, node, etc.), lo que evita las " +
          "reglas de permisos declaradas en .claude/settings.json. El agente encuesta-hogares nunca tiene " +
          "una razón legítima para tocar git, ni directa ni indirectamente - ver CLAUDE.md. Si esto es la " +
          "sesión principal publicando cambios de verdad, usá git directo (ej. `git add . && git commit " +
          "-m \"...\" && git push`), no a través de otro programa.",
      },
    })
  );
  process.exit(0);
});
