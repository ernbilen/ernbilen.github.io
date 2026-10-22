args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
if (length(script)) setwd(dirname(normalizePath(script)))
stopifnot(requireNamespace("xaringan", quietly = TRUE),
          requireNamespace("rmarkdown", quietly = TRUE))
rmarkdown::render("slides.Rmd", encoding = "UTF-8", quiet = FALSE)
