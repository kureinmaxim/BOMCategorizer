# Script to create GitHub release with file attachment
# Usage: .\create_release.ps1 -Token "your_github_token"

param(
    [Parameter(Mandatory=$true)]
    [string]$Token,
    
    [string]$Version = "4.4.2",
    [string]$Repo = "kureinmaxim/BOMCategorizer",
    [string]$SetupFile = "BOMCategorizerModernSetup.exe"
)

$tag = "v$Version"
$releaseName = "Release $Version"
$releaseBody = "BOM Categorizer Modern Edition $Version`n`nWindows installer file."

Write-Host "Creating release $tag for $Repo..." -ForegroundColor Cyan

# Check if file exists
if (-not (Test-Path $SetupFile)) {
    Write-Host "ERROR: File $SetupFile not found!" -ForegroundColor Red
    exit 1
}

$fileSize = (Get-Item $SetupFile).Length / 1MB
Write-Host "File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Yellow

# Create release via GitHub API
$headers = @{
    "Authorization" = "token $Token"
    "Accept" = "application/vnd.github.v3+json"
}

$releaseData = @{
    tag_name = $tag
    name = $releaseName
    body = $releaseBody
    draft = $false
    prerelease = $false
} | ConvertTo-Json

try {
    Write-Host "Sending request to create release..." -ForegroundColor Cyan
    $createUrl = "https://api.github.com/repos/$Repo/releases"
    $response = Invoke-RestMethod -Uri $createUrl -Method Post -Headers $headers -Body $releaseData -ContentType "application/json"
    
    $releaseId = $response.id
    Write-Host "Release created! ID: $releaseId" -ForegroundColor Green
    
    # Upload file
    Write-Host "Uploading file $SetupFile..." -ForegroundColor Cyan
    $uploadUrl = $response.upload_url -replace '\{.*$', "?name=$SetupFile"
    
    $uploadHeaders = @{
        "Authorization" = "token $Token"
        "Content-Type" = "application/octet-stream"
    }
    
    # GitHub API requires binary file upload
    $filePath = Resolve-Path $SetupFile
    $uploadResponse = Invoke-RestMethod -Uri $uploadUrl -Method Post -Headers $uploadHeaders -InFile $filePath
    
    Write-Host "File uploaded successfully!" -ForegroundColor Green
    Write-Host "Release URL: $($response.html_url)" -ForegroundColor Cyan
    
} catch {
    Write-Host "ERROR creating release:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }
    exit 1
}
