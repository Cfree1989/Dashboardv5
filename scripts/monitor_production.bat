@echo off
REM Comprehensive Production Monitoring Script for 3D Print Management System
REM Provides real-time monitoring, alerting, and reporting capabilities

setlocal enabledelayedexpansion

REM Configuration
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "LOG_DIR=%PROJECT_ROOT%\logs"
set "ALERT_LOG=%LOG_DIR%\alerts.log"
set "METRICS_LOG=%LOG_DIR%\metrics.log"
set "HEALTH_LOG=%LOG_DIR%\health.log"

REM Create log directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Alert thresholds
set "CPU_THRESHOLD=80"
set "MEMORY_THRESHOLD=85"
set "DISK_THRESHOLD=90"
set "ERROR_RATE_THRESHOLD=5"
set "RESPONSE_TIME_THRESHOLD=1000"

REM Function to log messages with timestamp
:log_message
set "level=%~1"
set "message=%~2"
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "date=%%c-%%a-%%b"
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "time=%%a:%%b"
echo [%date% %time%] [%level%] %message% | tee -a "%LOG_DIR%\monitoring.log"
goto :eof

REM Function to send alerts
:send_alert
set "severity=%~1"
set "message=%~2"
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "date=%%c-%%a-%%b"
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "time=%%a:%%b"

REM Log alert
echo [%date% %time%] [%severity%] %message% >> "%ALERT_LOG%"

REM Color-coded console output
if "%severity%"=="CRITICAL" (
    echo [%date% %time%] CRITICAL: %message%
) else if "%severity%"=="WARNING" (
    echo [%date% %time%] WARNING: %message%
) else if "%severity%"=="INFO" (
    echo [%date% %time%] INFO: %message%
) else (
    echo [%date% %time%] %severity%: %message%
)

REM TODO: Add email/SMS alerting here
REM Example: curl -X POST "https://api.example.com/alerts" -d "message=%message%&severity=%severity%"
goto :eof

REM Function to check Docker services
:check_docker_services
call :log_message "INFO" "Checking Docker services..."

set "all_healthy=true"

REM Check backend service
docker ps --format "table {{.Names}}\t{{.Status}}" | findstr "backend.*healthy" >nul 2>&1
if %errorlevel% equ 0 (
    call :log_message "INFO" "Service backend is healthy"
) else (
    docker ps --format "table {{.Names}}\t{{.Status}}" | findstr "backend" >nul 2>&1
    if %errorlevel% equ 0 (
        call :log_message "WARNING" "Service backend is running but not healthy"
        set "all_healthy=false"
    ) else (
        call :log_message "CRITICAL" "Service backend is not running"
        call :send_alert "CRITICAL" "Service backend is not running"
        set "all_healthy=false"
    )
)

REM Check frontend service
docker ps --format "table {{.Names}}\t{{.Status}}" | findstr "frontend.*healthy" >nul 2>&1
if %errorlevel% equ 0 (
    call :log_message "INFO" "Service frontend is healthy"
) else (
    docker ps --format "table {{.Names}}\t{{.Status}}" | findstr "frontend" >nul 2>&1
    if %errorlevel% equ 0 (
        call :log_message "WARNING" "Service frontend is running but not healthy"
        set "all_healthy=false"
    ) else (
        call :log_message "CRITICAL" "Service frontend is not running"
        call :send_alert "CRITICAL" "Service frontend is not running"
        set "all_healthy=false"
    )
)

REM Check database service
docker ps --format "table {{.Names}}\t{{.Status}}" | findstr "db.*healthy" >nul 2>&1
if %errorlevel% equ 0 (
    call :log_message "INFO" "Service db is healthy"
) else (
    docker ps --format "table {{.Names}}\t{{.Status}}" | findstr "db" >nul 2>&1
    if %errorlevel% equ 0 (
        call :log_message "WARNING" "Service db is running but not healthy"
        set "all_healthy=false"
    ) else (
        call :log_message "CRITICAL" "Service db is not running"
        call :send_alert "CRITICAL" "Service db is not running"
        set "all_healthy=false"
    )
)

if "%all_healthy%"=="true" (
    call :log_message "INFO" "All Docker services are healthy"
) else (
    call :log_message "WARNING" "Some Docker services have issues"
)
goto :eof

REM Function to check system resources
:check_system_resources
call :log_message "INFO" "Checking system resources..."

REM Get CPU usage (simplified for Windows)
for /f "tokens=2 delims=," %%a in ('wmic cpu get loadpercentage /value ^| findstr "LoadPercentage"') do set "cpu_usage=%%a"
set "cpu_usage=%cpu_usage:LoadPercentage=%"

REM Get memory usage
for /f "tokens=2 delims=," %%a in ('wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value ^| findstr "TotalVisibleMemorySize"') do set "total_memory=%%a"
for /f "tokens=2 delims=," %%a in ('wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value ^| findstr "FreePhysicalMemory"') do set "free_memory=%%a"
set "total_memory=%total_memory:TotalVisibleMemorySize=%"
set "free_memory=%free_memory:FreePhysicalMemory=%"
set /a "used_memory=%total_memory%-%free_memory%"
set /a "memory_percent=%used_memory%*100/%total_memory%"

REM Get disk usage
for /f "tokens=3 delims= " %%a in ('dir C:\ ^| findstr "bytes free"') do set "disk_free=%%a"
for /f "tokens=2 delims= " %%a in ('dir C:\ ^| findstr "bytes free"') do set "disk_total=%%a"
set /a "disk_used=%disk_total%-%disk_free%"
set /a "disk_percent=%disk_used%*100/%disk_total%"

REM Check thresholds
if %cpu_usage% gtr %CPU_THRESHOLD% (
    call :send_alert "WARNING" "High CPU usage: %cpu_usage%%%"
)

if %memory_percent% gtr %MEMORY_THRESHOLD% (
    call :send_alert "WARNING" "High memory usage: %memory_percent%%%"
)

if %disk_percent% gtr %DISK_THRESHOLD% (
    call :send_alert "CRITICAL" "High disk usage: %disk_percent%%%"
)

REM Log metrics
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "date=%%c-%%a-%%b"
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "time=%%a:%%b"
echo %date% %time%,cpu:%cpu_usage%,memory:%memory_percent%,disk:%disk_percent% >> "%METRICS_LOG%"
goto :eof

REM Function to check application health
:check_application_health
call :log_message "INFO" "Checking application health..."

REM Check ping endpoint
curl -f -s "http://localhost:5000/api/v1/monitoring/ping" >nul 2>&1
if %errorlevel% equ 0 (
    call :log_message "INFO" "Application ping successful"
) else (
    call :send_alert "CRITICAL" "Application ping failed"
    goto :eof
)

REM Check status endpoint
for /f "delims=" %%a in ('curl -s "http://localhost:5000/api/v1/monitoring/status" 2^>nul ^| findstr "status"') do set "status_response=%%a"
if "%status_response%"=="" set "status_response={\"status\":\"unhealthy\"}"

REM Extract status (simplified parsing)
echo %status_response% | findstr "healthy" >nul 2>&1
if %errorlevel% equ 0 (
    call :log_message "INFO" "Application status: healthy"
) else (
    echo %status_response% | findstr "degraded" >nul 2>&1
    if %errorlevel% equ 0 (
        call :log_message "WARNING" "Application status: degraded"
        call :send_alert "WARNING" "Application is in degraded state"
    ) else (
        call :log_message "CRITICAL" "Application status: unknown"
        call :send_alert "CRITICAL" "Application is unhealthy"
    )
)

REM Log health status
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "date=%%c-%%a-%%b"
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "time=%%a:%%b"
echo %date% %time%,app_status:healthy,overall_health:healthy >> "%HEALTH_LOG%"
goto :eof

REM Function to generate monitoring report
:generate_report
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "date=%%c%%a%%b"
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "time=%%a%%b"
set "report_file=%LOG_DIR%\monitoring_report_%date%_%time%.txt"

call :log_message "INFO" "Generating monitoring report..."

(
echo === 3D Print Management System - Monitoring Report ===
echo Generated: %date% %time%
echo ==================================================
echo.
echo === System Resources ===
echo CPU Usage: %cpu_usage%%%
echo Memory Usage: %memory_percent%%%
echo Disk Usage: %disk_percent%%%
echo.
echo === Docker Services ===
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo === Application Health ===
curl -s "http://localhost:5000/api/v1/monitoring/status"
echo.
echo === Recent Alerts ===
if exist "%ALERT_LOG%" (
    powershell "Get-Content '%ALERT_LOG%' | Select-Object -Last 20"
) else (
    echo No alerts found
)
echo.
echo === Performance Metrics ===
curl -s "http://localhost:5000/api/v1/monitoring/metrics/application"
echo.
echo === Database Metrics ===
curl -s "http://localhost:5000/api/v1/monitoring/metrics/database"
echo.
echo === Storage Metrics ===
curl -s "http://localhost:5000/api/v1/monitoring/metrics/storage"
) > "%report_file%"

call :log_message "INFO" "Monitoring report generated: %report_file%"
echo Monitoring report generated: %report_file%
goto :eof

REM Function to show help
:show_help
echo Usage: %0 [OPTION]
echo.
echo Options:
echo   -h, --help          Show this help message
echo   -c, --check         Run a single health check
echo   -r, --report        Generate monitoring report
echo   -w, --watch         Run continuous monitoring
echo   -i, --interval SEC  Set monitoring interval in seconds (default: 30)
echo.
echo Examples:
echo   %0 --check          Run one-time health check
echo   %0 --watch          Run continuous monitoring
echo   %0 --watch --interval 60  Run monitoring every 60 seconds
goto :eof

REM Main monitoring function
:run_monitoring
set "interval=%~1"
if "%interval%"=="" set "interval=30"

call :log_message "INFO" "Starting monitoring with %interval%s interval"
call :send_alert "INFO" "Monitoring started"

:monitoring_loop
call :log_message "INFO" "Running monitoring cycle..."

call :check_docker_services
call :check_system_resources
call :check_application_health

call :log_message "INFO" "Monitoring cycle completed"

timeout /t %interval% /nobreak >nul
goto monitoring_loop

REM Main script logic
if "%1"=="" (
    REM Default: run single check
    call :log_message "INFO" "Running single health check..."
    call :check_docker_services
    call :check_system_resources
    call :check_application_health
    call :log_message "INFO" "Health check completed"
    goto :eof
)

if "%1"=="-h" goto show_help
if "%1"=="--help" goto show_help
if "%1"=="-c" goto single_check
if "%1"=="--check" goto single_check
if "%1"=="-r" goto generate_report
if "%1"=="--report" goto generate_report
if "%1"=="-w" goto start_monitoring
if "%1"=="--watch" goto start_monitoring
if "%1"=="-i" goto start_monitoring_interval
if "%1"=="--interval" goto start_monitoring_interval

echo Error: Unknown option %1
call :show_help
exit /b 1

:single_check
call :log_message "INFO" "Running single health check..."
call :check_docker_services
call :check_system_resources
call :check_application_health
call :log_message "INFO" "Health check completed"
goto :eof

:start_monitoring
call :run_monitoring
goto :eof

:start_monitoring_interval
if "%2"=="" (
    echo Error: No interval specified
    call :show_help
    exit /b 1
)
call :run_monitoring %2
goto :eof
