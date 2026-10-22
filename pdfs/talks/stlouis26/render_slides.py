"""Compatibility entry point: render the editable Rmd with xaringan."""
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parent
rscript = shutil.which('Rscript')
if not rscript:
    candidates = sorted(Path('C:/Program Files/R').glob('R-*/bin/Rscript.exe'))
    if not candidates:
        raise SystemExit('Open stlouis26.Rproj in RStudio and Knit slides.Rmd, or put Rscript on PATH.')
    rscript = str(candidates[-1])
subprocess.run([rscript, '--vanilla', str(root / 'render.R')], cwd=root, check=True)
