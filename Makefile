.PHONY: test demo derive

# Run the full test suite (stdlib unittest, no dependencies)
test:
	python3 -m unittest discover -s tests -v

# Same, but forces the built-in YAML-subset parser (no PyYAML)
test-no-pyyaml:
	VCS_NO_PYYAML=1 python3 -m unittest discover -s tests -v

# See the gate catch neuroslop in 10 seconds
demo:
	python3 scripts/run_all.py \
	  --input examples/01-ml-paper-latex/input \
	  --config examples/01-ml-paper-latex \
	  --artifacts examples/01-ml-paper-latex/artifacts || true

# Re-derive thresholds from the shipped corpus (should print 28/45/15.0)
derive:
	python3 scripts/derive_thresholds.py
