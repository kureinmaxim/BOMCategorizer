# Script to upload file to existing GitHub release
# Usage: .\upload_to_existing_release.ps1 -Token "your_github_token"

param(
    [Parameter(Mandatory=$true)]
    [string]$Token,
    
    [string]$Version = "4.4.2",
    [string]$Repo = "kureinmaxim/BOMCategorizer",
    [string]$SetupFile = "BOMCategorizerModernSetup.exe"
)

$tag = "v$Version"

Write-Host "Uploading file to existing release $tag for $Repo..." -ForegroundColor Cyan

# Check if file exists
if (-not (Test-Path $SetupFile)) {
    Write-Host "ERROR: File $SetupFile not found!" -ForegroundColor Red
    exit 1
}

$fileSize = (Get-Item $SetupFile).Length / 1MB
Write-Host "File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Yellow

# Get existing release
$headers = @{
    "Authorization" = "token $Token"
    "Accept" = "application/vnd.github.v3+json"
}

try {
    Write-Host "Getting release info..." -ForegroundColor Cyan
    $getReleaseUrl = "https://api.github.com/repos/$Repo/releases/tags/$tag"
    $release = Invoke-RestMethod -Uri $getReleaseUrl -Method Get -Headers $headers
    
    $releaseId = $release.id
    Write-Host "Found release! ID: $releaseId" -ForegroundColor Green
    
    # Check if asset already exists
    $existingAsset = $release.assets | Where-Object { $_.name -eq $SetupFile }
    if ($existingAsset) {
        Write-Host "WARNING: Asset $SetupFile already exists. Deleting old version..." -ForegroundColor Yellow
        $deleteUrl = "https://api.github.com/repos/$Repo/releases/assets/$($existingAsset.id)"
        Invoke-RestMethod -Uri $deleteUrl -Method Delete -Headers $headers | Out-Null
        Write-Host "Old asset deleted." -ForegroundColor Green
    }
    
    # Upload file
    Write-Host "Uploading file $SetupFile..." -ForegroundColor Cyan
    $uploadUrl = $release.upload_url -replace '\{.*$', "?name=$SetupFile"
    
    $uploadHeaders = @{
        "Authorization" = "token $Token"
        "Content-Type" = "application/octet-stream"
    }
    
    $filePath = Resolve-Path $SetupFile
    $uploadResponse = Invoke-RestMethod -Uri $uploadUrl -Method Post -Headers $uploadHeaders -InFile $filePath
    
    Write-Host "File uploaded successfully!" -ForegroundColor Green
    Write-Host "Download URL: $($uploadResponse.browser_download_url)" -ForegroundColor Cyan
    Write-Host "Release URL: $($release.html_url)" -ForegroundColor Cyan
    
} catch {
    Write-Host "ERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }
    exit 1
}

