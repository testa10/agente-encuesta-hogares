<#
Minimiza o restaura la ventana de consola de abrir_agente.bat por su
titulo, para que mientras se espera la respuesta del formulario de
arranque (que puede tardar) no haya una terminal a la vista compitiendo
con el formulario del navegador. Si no encuentra la ventana (por ejemplo,
Windows Terminal no siempre expone el mismo titulo que "title" del batch),
no hace nada - es un detalle cosmetico, nunca debe romper el arranque.
#>
param(
    [Parameter(Mandatory=$true)][string]$Titulo,
    [Parameter(Mandatory=$true)][ValidateSet("Minimizar", "Restaurar")][string]$Accion
)

Add-Type -Namespace Native -Name Win32 -MemberDefinition @"
[DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
[DllImport("user32.dll")] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
"@

$hwnd = [Native.Win32]::FindWindow($null, $Titulo)
if ($hwnd -ne [IntPtr]::Zero) {
    $nCmdShow = if ($Accion -eq "Minimizar") { 6 } else { 9 }  # SW_MINIMIZE / SW_RESTORE
    [Native.Win32]::ShowWindowAsync($hwnd, $nCmdShow) | Out-Null
}
