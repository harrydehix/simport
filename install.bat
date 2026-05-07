@echo off

echo Installing vibes-song-importer as a CLI using uv...
:: 'uv tool install' is the recommended way to install CLI tools via uv globally.
:: Alternatively, 'uv pip install -e .' installs it into the active virtual environment.
uv tool install --editable .

echo.
echo Installation finished! You can now use the 'simport' command.
pause
