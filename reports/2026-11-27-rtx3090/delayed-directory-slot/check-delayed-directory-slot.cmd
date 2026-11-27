@echo off
setlocal
where cl >nul 2>nul
if errorlevel 1 (
  for /f "usebackq delims=" %%V in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do call "%%V\VC\Auxiliary\Build\vcvars64.bat" >nul
)
where cl >nul 2>nul || exit /b 2
set "auditdir=%TEMP%\VI-delayed-slot-%RANDOM%-%RANDOM%"
mkdir "%auditdir%" || exit /b 2
pushd "%auditdir%" || exit /b 2
cl /nologo /std:c++17 /EHsc /O2 "%~dp0delayed-directory-slot.cpp" /link d3d12.lib dxgi.lib d3dcompiler.lib
if errorlevel 1 exit /b 2
delayed-directory-slot.exe
set "result=%errorlevel%"
popd
exit /b %result%
