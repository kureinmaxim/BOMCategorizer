# PowerShell скрипт для скачивания шрифтов DejaVu Sans
# Используется для подготовки проекта перед сборкой инсталлятора

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Скачивание шрифтов DejaVu Sans" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Создаем папку fonts если её нет
if (-not (Test-Path "fonts")) {
    New-Item -ItemType Directory -Path "fonts" | Out-Null
    Write-Host "✓ Создана папка fonts" -ForegroundColor Green
}

# URL шрифтов
$baseUrl = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf"
$fonts = @{
    "DejaVuSans.ttf" = "$baseUrl/DejaVuSans.ttf"
    "DejaVuSans-Bold.ttf" = "$baseUrl/DejaVuSans-Bold.ttf"
}

# Скачиваем каждый шрифт
foreach ($font in $fonts.GetEnumerator()) {
    $fileName = $font.Key
    $url = $font.Value
    $outputPath = "fonts\$fileName"
    
    Write-Host "Скачивание $fileName..." -NoNewline
    
    try {
        # Проверяем, существует ли уже файл
        if (Test-Path $outputPath) {
            Write-Host " [УЖЕ СУЩЕСТВУЕТ]" -ForegroundColor Yellow
            continue
        }
        
        # Скачиваем файл
        Invoke-WebRequest -Uri $url -OutFile $outputPath -UseBasicParsing
        
        # Проверяем размер файла
        $fileSize = (Get-Item $outputPath).Length
        if ($fileSize -gt 0) {
            $fileSizeKB = [math]::Round($fileSize / 1KB, 2)
            Write-Host " ✓ ($fileSizeKB KB)" -ForegroundColor Green
        } else {
            Write-Host " ✗ Ошибка: файл пустой" -ForegroundColor Red
            Remove-Item $outputPath -Force
        }
    }
    catch {
        Write-Host " ✗ Ошибка" -ForegroundColor Red
        Write-Host "  $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Проверяем результат
$requiredFiles = @("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
$allPresent = $true

foreach ($file in $requiredFiles) {
    $path = "fonts\$file"
    if (Test-Path $path) {
        Write-Host "✓ $file" -ForegroundColor Green
    } else {
        Write-Host "✗ $file - НЕ НАЙДЕН" -ForegroundColor Red
        $allPresent = $false
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allPresent) {
    Write-Host "✓ Все шрифты успешно скачаны!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Теперь можно:" -ForegroundColor Cyan
    Write-Host "  1. Собрать инсталлятор (шрифты будут включены автоматически)" -ForegroundColor White
    Write-Host "  2. Запустить check_pdf_fonts.py для проверки" -ForegroundColor White
} else {
    Write-Host "✗ Не все шрифты скачаны. Попробуйте:" -ForegroundColor Red
    Write-Host "  1. Проверить подключение к интернету" -ForegroundColor White
    Write-Host "  2. Скачать вручную с https://dejavu-fonts.github.io/" -ForegroundColor White
    Write-Host "  3. Поместить файлы в папку fonts\" -ForegroundColor White
}

Write-Host ""
Write-Host "Нажмите Enter для выхода..."
$null = Read-Host

