@echo off
setlocal
where cl.exe >nul 2>nul
if errorlevel 1 call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /W4 /O2 verify.cpp /Fe:verify.exe /link d3d12.lib dxgi.lib
set "result=%errorlevel%"
popd
exit /b %result%
