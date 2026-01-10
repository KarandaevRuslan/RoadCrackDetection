@echo off
setlocal EnableExtensions

rem ПАПКА — путь к папке, в которой ищем .xml (если не задано, берём текущую)
set "FOLDER=%~1"
if "%FOLDER%"=="" set "FOLDER=%CD%"

rem COUNT — переменная-счётчик количества найденных файлов
set /a COUNT=0

rem FOR /R — рекурсивно обходит папку и подпапки
rem %%F — переменная цикла, в неё по очереди попадает путь каждого найденного файла
for /R "%FOLDER%" %%F in (*.xml) do (
    set /a COUNT+=1
)

rem ENDLOCAL & SET — сохраняет значение COUNT после завершения setlocal
endlocal & set "COUNT=%COUNT%"

echo Folder: %FOLDER%
echo XML files (recursive): %COUNT%
exit /b 0
