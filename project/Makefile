PYTHON ?= python

.PHONY: install check test notebook

install:
	$(PYTHON) -m pip install -r requirements.txt

check:
	$(PYTHON) -m compileall -q src

test:
	$(PYTHON) -m unittest discover -s tests -v

notebook:
	$(PYTHON) -m jupyter lab
