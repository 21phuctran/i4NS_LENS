@echo off
REM i4NS LENS Quick Start Script for Windows
REM This script helps you get started quickly

echo ========================================
echo i4NS LENS - Quick Start
echo ========================================
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not installed. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo Docker and Docker Compose are installed
echo.

REM Create data directories
echo Creating data directories...
if not exist "data\doctrines" mkdir data\doctrines
if not exist "data\mission_logs" mkdir data\mission_logs
if not exist "data\vector_store" mkdir data\vector_store
if not exist "logs" mkdir logs
echo Data directories created
echo.

REM Check for doctrine documents
dir /b data\doctrines 2>nul | findstr "^" >nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: No doctrine documents found in data\doctrines\
    echo.
    echo Sample doctrine will be created on first run.
    echo You can also add your own doctrine PDFs or text files to data\doctrines\
    echo.
)

REM Build and start
echo Building and starting i4NS LENS...
echo This may take a few minutes on first run...
echo.

docker-compose up --build -d

echo.
echo ========================================
echo i4NS LENS is starting!
echo ========================================
echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check health (simple approach for Windows)
echo Checking service health...
curl -s http://localhost:8000/api/health >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Services are healthy
    echo.
    echo i4NS LENS is ready!
    echo.
    echo Access the application at:
    echo   Frontend: http://localhost:8000
    echo   API Docs: http://localhost:8000/docs
    echo.
    echo To view logs:
    echo   docker-compose logs -f
    echo.
    echo To stop:
    echo   docker-compose down
) else (
    echo Services may still be starting...
    echo Check status with: docker-compose logs -f
    echo.
    echo Access at: http://localhost:8000
)

echo.
echo For more information, see README.md and SETUP.md
echo.
pause
