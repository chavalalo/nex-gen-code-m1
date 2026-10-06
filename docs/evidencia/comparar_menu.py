"""Ejecuta el menu de una version de src/ con entradas fijas e imprime la salida.

Uso: python docs/evidencia/comparar_menu.py <ruta_src> <datos.json> > salida.txt
Se usa para comparar byte a byte la version original contra la refactorizada.
"""
import builtins, io, os, sys, tempfile, contextlib
src = os.path.abspath(sys.argv[1]); sys.path.insert(0, src)
os.chdir(tempfile.mkdtemp())
import shutil; shutil.copy(sys.argv[2], "datos_ejemplo.json")
entradas = iter(["4","7","2","A001","6","VIP9","2","A003","1","","2","A002","50","",
  "2","B002","9","","3","A001","3","3","ZZ","1","1","D1","Dulce","x","9.5","1",
  "1","A001","Dup","1","1","5","6","4","7","0","8"])
builtins.input = lambda m="": next(entradas)
import main
out = io.StringIO()
with contextlib.redirect_stdout(out):
    main.menu()
texto = out.getvalue()
import re
print(texto)
print(open("datos_ejemplo.json").read().count('"folio"'), "ventas guardadas")
