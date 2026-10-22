"""Render the current xaringan source; does not regenerate or replace its content."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('render_slides.py')), run_name='__main__')
