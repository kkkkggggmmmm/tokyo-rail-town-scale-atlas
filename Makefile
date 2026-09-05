PYTHON ?= python3

.PHONY: verify-fast verify-locked verify-g3

verify-fast:
	$(PYTHON) scripts/validate_phase0.py

verify-locked:
	$(PYTHON) scripts/validate_phase1_lock.py
	$(PYTHON) scripts/validate_phase1_identity.py

verify-g3:
	$(PYTHON) scripts/validate_phase1_g3.py
