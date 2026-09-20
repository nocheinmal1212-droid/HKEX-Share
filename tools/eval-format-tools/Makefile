PYTHON ?= python3
ROOT := ../..
export PYTHONPATH := $(abspath $(ROOT)/src):$(CURDIR)

.PHONY: fmt fmt-check schema-check test check local-check
fmt:
	$(PYTHON) -m eval_formatter $(ROOT)
fmt-check:
	$(PYTHON) -m eval_formatter --check $(ROOT)
schema-check:
	$(PYTHON) -m eval_intake.schema_check --root $(ROOT)
test:
	$(PYTHON) -m unittest discover -s tests -v
check: fmt-check schema-check test
local-check:
	cd $(ROOT) && PYTHONPATH=src:tools/eval-format-tools tools/eval-format-tools/.venv/bin/python -m eval_intake --root . validate --manifest eval/manifests/hkex-2025-48.json --locations eval/locations/hkex-2025-48.r3.json --splits eval/splits/hkex-2025-48.r3.json --records eval/records/hkex-2025-48/corrupted.r3.jsonl --review eval/reviews/hkex-2025-48/owner-approval.json
