St. Louis 2026 — xaringan project

Open stlouis26.Rproj in RStudio, open slides.Rmd, and click Knit.
slides.Rmd is the source of truth. Edit the slide text there.
The two Python entry points now run the same R renderer and preserve your edits.

From this folder in R:
  rmarkdown::render("slides.Rmd", encoding = "UTF-8")

From a terminal:
  Rscript --vanilla render.R

Present by opening slides.html in a browser. Keep libs, assets, styles.css,
xaringan.css and slides.html together when copying the presentation.
The deck has local JavaScript, fonts, figures and math, and works offline.

Keys: Left/Right or Space to navigate; P for presenter mode; C to open the
audience window; F for full screen; ? for the keyboard shortcut help.
The opening builds step by step. The headline result has two steps.
Links to backup slides, FAQ answers, and return destinations stay in this deck.
Use the browser Print command to export the xaringan layout to PDF.

Text and tables are native slide content. Original figures and screenshots are
separate image files in assets/david-figures. Original PDFs and the TeX source
are retained in sources. The earlier exact-page deck is retained under versions.
David's original speaking notes are also retained in david_speaker_notes.pdf.
