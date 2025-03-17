MD_DIR   := .
OUT_DIR  := out
LATEX_ENGINE := xelatex
PANDOC_OPTS := \
    --pdf-engine=$(LATEX_ENGINE) \
    --variable=documentclass:article \
    --variable=mainfont:"DejaVu Serif" \
    --variable=sansfont:"DejaVu Sans" \
    --variable=monofont:"DejaVu Sans Mono" \
    --variable=lang:ru-RU \
    --toc
MD_SOURCES := $(wildcard $(MD_DIR)/*.md)
PDFS := $(patsubst $(MD_DIR)/%.md,$(OUT_DIR)/%.pdf,$(MD_SOURCES))
COMBINED_PDF := $(OUT_DIR)/combined.pdf

.PHONY: all
all: $(COMBINED_PDF)

$(COMBINED_PDF): $(PDFS)
	@echo "Generating combined PDF $@ from $(words $^) markdown files"
	@pandoc $(MD_SOURCES) -o $@ $(PANDOC_OPTS)

$(OUT_DIR)/%.pdf: $(MD_DIR)/%.md | $(OUT_DIR)
	@echo "Generating PDF $@ from $<"
	@pandoc $< -o $@ $(PANDOC_OPTS)

$(OUT_DIR):
	@mkdir -p $@

.PHONY: clean clean-pdf clean-md
clean:
	@rm -f $(OUT_DIR)
