$ErrorActionPreference = "Stop"

$mysqlRoot = "C:\Users\Administrator\Desktop\project\mysql-8.4.11-winx64"
$mysqld = Join-Path $mysqlRoot "bin\mysqld.exe"
$config = Join-Path $mysqlRoot "my.ini"
function Test-MySqlPort {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $client.Connect("127.0.0.1", 3306)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

if (-not (Test-Path -LiteralPath $mysqld)) {
    throw "MySQL executable was not found: $mysqld"
}

if (Test-MySqlPort) {
    Write-Output "MySQL is already running on 127.0.0.1:3306."
    exit 0
}

$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $mysqld
$startInfo.UseShellExecute = $true
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.WorkingDirectory = $mysqlRoot
$startInfo.Arguments = "--defaults-file=`"$config`""
$process = [System.Diagnostics.Process]::Start($startInfo)
if ($null -eq $process) {
    throw "Unable to create the MySQL process."
}

for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Milliseconds 500
    if (Test-MySqlPort) {
        Write-Output "MySQL started on 127.0.0.1:3306."
        exit 0
    }
}

if (Test-Path -LiteralPath (Join-Path $mysqlRoot "mysql-error.log")) {
    Get-Content -Tail 30 -LiteralPath (Join-Path $mysqlRoot "mysql-error.log")
}
throw "MySQL did not start within 15 seconds."
