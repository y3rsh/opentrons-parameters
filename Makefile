CMD ?= -m pip list
MAC_APP_PYTHON ?= /Applications/Opentrons.app/Contents/Resources/python/bin/python3
WIN_APP_PYTHON ?= "C:\Program Files\Opentrons\resources\python\python.exe"

.PHONY: mac-python
mac-python: 
	@echo "Running python from Opentrons.app"
	@echo "MAC_APP_PYTHON: $(MAC_APP_PYTHON)"
	$(MAC_APP_PYTHON) $(CMD)

.PHONY: win-python
win-python:
	@echo "Running python from Opentrons.exe"
	@echo "WIN_APP_PYTHON: $(WIN_APP_PYTHON)"
	$(WIN_APP_PYTHON) $(CMD)

.PHONY: format
format:
	@echo "Running black"
	black **/*.py
	@echo "Running ruff"
	ruff check **/*.py --fix
