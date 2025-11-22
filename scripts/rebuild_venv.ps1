# rebuild_venv.ps1
# Скрипт пересоздаёт виртуальное окружение и запускает build_installer.py

Write-Host "=== Пересоздание виртуального окружения ===" -ForegroundColor Cyan

# Переход в каталог проекта
Set-Location "C:\Project\ProjectSnabjenie"

# Удаляем старое окружение, если есть
if (Test-Path ".\.venv") {
    Write-Host "Удаляю старое .venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .\.venv
}

# Проверяем, что python доступен
try {
    $pyVer = (python --version)
    Write-Host "Используется $pyVer" -ForegroundColor Green
} catch {
    Write-Host "Ошибка: Python не найден. Убедись, что он установлен и добавлен в PATH." -ForegroundColor Red
    exit 1
}

# Создаём новое окружение
Write-Host "Создаю новое .venv..." -ForegroundColor Yellow
python -m venv .venv

# Активируем
Write-Host "Активирую окружение..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Устанавливаем зависимости, если есть
if (Test-Path "requirements.txt") {
    Write-Host "Устанавливаю зависимости..." -ForegroundColor Yellow
    pip install --upgrade pip
    pip install -r requirements.txt
} else {
    Write-Host "Файл requirements.txt не найден, пропускаю установку зависимостей." -ForegroundColor DarkYellow
}

# Запускаем сборку
Write-Host "Запускаю build_installer.py..." -ForegroundColor Cyan
python build_installer.py

Write-Host "✅ Готово!" -ForegroundColor Green
