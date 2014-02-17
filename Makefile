.PHONY: clean cleanbuild test dist docs

all: clean test

clean:
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -name '__pycache__' -depth -exec rm -rf {} \;

cleanbuild:
	rm -rf build
	rm -rf dist
	rm -rf *.egg
	rm -rf *.egg-info

test:
	py.test

dist: cleanbuild
	python setup.py sdist

docs:
	SPHINX_RUNNING=1 $(MAKE) -C docs html
