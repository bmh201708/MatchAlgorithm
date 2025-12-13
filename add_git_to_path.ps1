# Add Git and GitHub CLI to PATH environment variable
# Run this script as Administrator if needed

$gitPath = "C:\Program Files\Git\cmd"
$ghPath = "C:\Program Files\GitHub CLI"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathsToAdd = @()

# Check Git path
if ($currentPath -notlike "*$gitPath*") {
    $pathsToAdd += $gitPath
    Write-Host "Git path needs to be added: $gitPath" -ForegroundColor Yellow
} else {
    Write-Host "Git path already exists in PATH" -ForegroundColor Green
}

# Check GitHub CLI path
if ($currentPath -notlike "*$ghPath*") {
    $pathsToAdd += $ghPath
    Write-Host "GitHub CLI path needs to be added: $ghPath" -ForegroundColor Yellow
} else {
    Write-Host "GitHub CLI path already exists in PATH" -ForegroundColor Green
}

# Add missing paths
if ($pathsToAdd.Count -gt 0) {
    $newPath = $currentPath + ";" + ($pathsToAdd -join ";")
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "`nThe following paths have been added to PATH:" -ForegroundColor Green
    $pathsToAdd | ForEach-Object { Write-Host "  - $_" -ForegroundColor Cyan }
    Write-Host "`nPlease restart PowerShell or VS Code for changes to take effect" -ForegroundColor Yellow
} else {
    Write-Host "`nAll paths already exist in PATH, no changes needed" -ForegroundColor Green
}
