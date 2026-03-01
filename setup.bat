@echo off
setlocal enabledelayedexpansion
REM Banking App — one-command Docker setup (Windows)

echo === Banking App Setup ===

REM Check Docker is available
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not in PATH.
    exit /b 1
)

REM Create .env from example if it doesn't exist
if not exist .env (
    copy .env.example .env >nul
    REM Generate a random JWT secret using Python
    for /f %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set "SECRET=%%i"
    python -c "import sys; data=open('.env').read(); open('.env','w').write(data.replace('change-me-generate-with-openssl-rand-hex-32','!SECRET!'))"
    echo Created .env with generated JWT secret.
) else (
    echo .env already exists, skipping.
)

REM Build and start
echo Building and starting containers...
docker compose up --build -d

echo.
echo === Setup complete ===
echo App running at: http://localhost:8000
echo API docs at:    http://localhost:8000/docs
echo.
echo To stop:  docker compose down
echo To logs:  docker compose logs -f

endlocal
