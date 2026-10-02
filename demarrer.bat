@echo off
setlocal
title ScolaPay - demo
cd /d "%~dp0"

echo.
echo  ===== ScolaPay : demarrage de la demo =====
echo.

rem 1. Trouver Python 3.10 ou plus recent
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PY=python"
if not defined PY goto nopython

rem 2. Environnement Python et dependances
if not exist ".venv\Scripts\python.exe" (
  echo Creation de l'environnement Python...
  %PY% -m venv .venv || goto erreur
)
echo Installation des dependances (la premiere fois : 1 a 2 minutes)...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt || goto erreur

rem 3. Configuration, base de donnees et ecole de demonstration
if not exist ".env" copy ".env.example" ".env" >nul
".venv\Scripts\python.exe" manage.py migrate --noinput || goto erreur
".venv\Scripts\python.exe" manage.py demo --password "Demo-ScolaPay-2026" --si-absente || goto erreur

echo.
echo  ScolaPay demarre : le navigateur va s'ouvrir sur http://127.0.0.1:8000
echo  Identifiant : directeur.demo  (ou caisse.demo)
echo  Mot de passe : Demo-ScolaPay-2026
echo  LAISSEZ CETTE FENETRE OUVERTE. Pour arreter : fermez-la.
echo.
start "" /min cmd /c "timeout /t 4 /nobreak >nul & start http://127.0.0.1:8000/"
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
pause
exit /b 0

:nopython
echo [ERREUR] Python 3.10 ou plus recent est introuvable.
echo Installez-le depuis https://www.python.org/downloads/
echo IMPORTANT : cochez "Add python.exe to PATH" pendant l'installation,
echo puis relancez ce fichier.
echo.
pause
exit /b 1

:erreur
echo.
echo [ERREUR] Le demarrage a echoue. Copiez le message ci-dessus et envoyez-le a Claude.
echo.
pause
exit /b 1
