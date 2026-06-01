@echo off
setlocal EnableExtensions

rem %1 — путь к папке, структуру которой нужно вывести
if "%~1"=="" (
  echo Использование: %~nx0 "C:\Path\To\Folder"
  exit /b 1
)

set "ROOT=%~1"

rem Проверка, что папка существует
if not exist "%ROOT%\" (
  echo Ошибка: папка не найдена: "%ROOT%"
  exit /b 2
)

rem Вывод структуры папок (без файлов) в консоль
echo Структура папок для: "%ROOT%"
tree "%ROOT%" /A

endlocal
exit /b 0
