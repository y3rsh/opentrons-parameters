CMD ?= -m pip list
MAC_APP_PYTHON ?= /Applications/Opentrons.app/Contents/Resources/python/bin/python3 
.PHONY: mac-python
mac-python: 
	@echo "Running python from Opentrons.app"
	$(MAC_APP_PYTHON) $(CMD)

.PHONY: format
format:
	@echo "Running black"
	black **/*.py
	@echo "Running ruff"
	ruff check **/*.py --fix
