$log = "C:\Users\JECT\Videos\YURI PROJECTS\experimento\runner_wsl.log"

Write-Host "Copiando archivos a WSL..."
wsl -d Debian --user ject cp /mnt/c/Users/JECT/Videos/YURI\ PROJECTS/experimento/runner.sh /home/ject/proyecto/runner.sh
wsl -d Debian --user ject cp /mnt/c/Users/JECT/Videos/YURI\ PROJECTS/experimento/cleanup.sh /home/ject/proyecto/experimento/cleanup.sh

Write-Host "Limpiando entorno..."
wsl -d Debian --user ject bash /home/ject/proyecto/experimento/cleanup.sh
wsl -d Debian --user ject rm -rf /home/ject/proyecto/experimento/resultados
wsl -d Debian --user ject mkdir -p /home/ject/proyecto/experimento/resultados

Write-Host "Lanzando experimento..."
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "wsl.exe"
$psi.Arguments = "-d Debian --user ject bash /home/ject/proyecto/runner.sh"
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.WorkingDirectory = "C:\Users\JECT\Videos\YURI PROJECTS\experimento"

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
$proc.Start() | Out-Null

$outFile = [System.IO.StreamWriter]::new($log)
$proc.OutputDataReceived.Add({
    $outFile.WriteLine($EventArgs.Data)
    $outFile.Flush()
})
$proc.ErrorDataReceived.Add({
    $outFile.WriteLine("ERR: $($EventArgs.Data)")
    $outFile.Flush()
})
$proc.BeginOutputReadLine()
$proc.BeginErrorReadLine()

Write-Host "Runner lanzado con PID $($proc.Id)"
Write-Host "Log: $log"
