PYTHON ?= python

.PHONY: install check notebook

install:
	$(PYTHON) -m pip install -r requirements.txt

check:
	$(PYTHON) -m compileall -q src

notebook:
	$(PYTHON) -m jupyter lab
