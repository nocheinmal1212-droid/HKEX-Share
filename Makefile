PYTHON ?= tools/eval-format-tools/.venv/bin/python

.PHONY: evidence-check evidence-local-check
evidence-check:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v
evidence-local-check:
	PYTHONPATH=src:tools/eval-format-tools $(PYTHON) eval/milestone1/validate.py
