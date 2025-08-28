# PowerShell script to load .env variables and run toolbox.exe
# .\run_toolbox.ps1

# Load environment variables from .env file
Get-Content .env | ForEach-Object {
    if ($_ -match '^[^#][^=]*=') {
        $parts = $_ -split '=', 2
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

# Run toolbox.exe with the tools.yaml file | ./toolbox.exe --tools-file "tools.yaml"
Start-Process -NoNewWindow -Wait -FilePath "./toolbox.exe" -ArgumentList "--tools-file", "tools.yaml"