.PHONY: init test dist release docs clean

init:
	pip install -r requirements.txt

test:
	py.test

dist: clean
	python setup.py sdist

release: test clean
	python setup.py sdist upload

docs:
	$(MAKE) -C docs html

clean:
	rm -rf audiodiff.egg-info
	rm -rf build
	rm -rf dist
	rm -rf docs/_build
	find . -type f -name '*.pyc' -exec rm {} \;
	find . -type d -name '__pycache__' -maxdepth 1 -exec rm -rf {} \;
