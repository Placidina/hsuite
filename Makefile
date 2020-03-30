# WARN: gmake syntax

SDIST_DIR ?= 'dist'
PYTHON=python

.PHONY: all
all: clean python

.PHONY: clean
clean:
	@echo "Cleaning up distutils stuff"
	rm -rf build
	rm -rf dist
	rm -rf lib/hsuite.egg-info/
	@echo "Cleaning up byte compiled python stuff"
	find . -type f -regex ".*\.py[co]$$" -delete
	find . -type d -name "__pycache__" -delete

.PHONY: python
python:
	$(PYTHON) setup.py build

.PHONY: sdist_check
sdist_check:
	$(PYTHON) -c 'import setuptools, sys; sys.exit(int(not (tuple(map(int, setuptools.__version__.split("."))) > (39, 2, 0))))'
	$(PYTHON) packaging/sdist/check-link-behavior.py

.PHONY: sdist
sdist: sdist_check clean
	_HSUITE_SDIST_FROM_MAKEFILE=1 $(PYTHON) setup.py sdist --dist-dir=$(SDIST_DIR)