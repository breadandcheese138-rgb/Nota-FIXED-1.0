# Nota para Windows

Bloc de notas de escritorio ligero, local y open source.

## Ejecutar desde el codigo

Necesitas Python 3.9 o posterior con Tkinter.

```powershell
py app.py
```

## Crear el ejecutable

Abre PowerShell en esta carpeta y ejecuta:

```powershell
./build_windows.ps1
```

El ejecutable se crea en `release\Nota-Windows.exe`.

Tambien puedes ejecutar el workflow de GitHub Actions en `.github/workflows/build.yml`; el runner de Windows generara el `.exe` automaticamente.

## Comandos

- `Ctrl+N`: nueva nota
- `Ctrl+O`: abrir archivo
- `Ctrl+S`: guardar
- `Ctrl+Shift+S`: guardar como
- `Ctrl+W`: cerrar pestana
- `Ctrl+F`: buscar
- `Ctrl+T`: cambiar tema

La aplicacion permite elegir entre tema claro y oscuro. Las notas se guardan como texto UTF-8.

## Licencia

MIT
