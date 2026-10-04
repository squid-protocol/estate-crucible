# estate-crucible. Stdlib Python 3.9+; the compile step needs cobc or Docker
# (GNUCOBOL_IMAGE, default gitgalaxy-gnucobol:3).
PYTHON ?= python3

.PHONY: generate check check-fast compile scale-smoke

generate:            ## rewrite estate/, key/ and horrors/ from generator/ and spec/
	$(PYTHON) -m generator

check:               ## regenerate + diff against the committed tree, key consistency, GnuCOBOL compile
	$(PYTHON) tools/check.py

check-fast:          ## the same without the compile step
	$(PYTHON) tools/check.py --no-compile

compile:             ## GnuCOBOL compile check only
	$(PYTHON) tools/compile.py

scale-smoke:         ## generate the medium preset into a scratch dir (determinism + scale dial)
	rm -rf .scale-a .scale-b
	$(PYTHON) -m generator --size medium --out .scale-a
	$(PYTHON) -m generator --size medium --out .scale-b
	diff -r .scale-a .scale-b && echo "medium preset is deterministic"
	rm -rf .scale-a .scale-b
