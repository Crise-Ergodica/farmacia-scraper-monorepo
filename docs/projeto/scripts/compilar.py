"""Compilação limpa do PI, com bibliografia e estabilização de referências.
Da raiz: python3 docs/projeto/scripts/compilar.py
TECTONIC_BIN e TECTONIC_BUNDLE permitem indicar runtime/bundle alternativos.
O diretório de build é temporário; o log da compilação é preservado na saída.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
OUT = REPO / 'output/pdf'
OUT.mkdir(parents=True, exist_ok=True)
tectonic = os.environ.get('TECTONIC_BIN') or shutil.which('tectonic')
latexmk = shutil.which('latexmk')
with tempfile.TemporaryDirectory(prefix='pi-build-') as directory:
    build = Path(directory)
    # Cópia isolada evita ler auxiliares antigos ou escrever nos fontes.
    src = build / 'src'
    shutil.copytree(PROJECT, src, ignore=shutil.ignore_patterns('*.aux','*.log','*.toc','*.lof','*.loq','*.bbl','*.blg'))
    if tectonic:
        cmd = [str(Path(tectonic).resolve()), 'main.tex', '--keep-logs', '--keep-intermediates']
        if os.environ.get('TECTONIC_BUNDLE'):
            cmd += ['--bundle', os.environ['TECTONIC_BUNDLE']]
    elif latexmk:
        cmd = [latexmk, '-pdf', '-interaction=nonstopmode', '-halt-on-error', 'main.tex']
    else:
        raise SystemExit('Instale um runtime LaTeX (Tectonic ou TeX Live com latexmk).')
    completed = subprocess.run(cmd, cwd=src, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT/'preco-bao-compilacao.txt').write_text(completed.stdout)
    for suffix in ('log','blg','aux','toc','lof','loq'):
        file = src/f'main.{suffix}'
        if file.exists():
            shutil.copy2(file, OUT/f'preco-bao.{suffix}')
    if completed.returncode:
        raise SystemExit(f'Falha de compilação ({completed.returncode}); consulte output/pdf/preco-bao-compilacao.txt.')
    shutil.copy2(src/'main.pdf', OUT/'preco-bao-revisao-parcial.pdf')
print(OUT/'preco-bao-revisao-parcial.pdf')
