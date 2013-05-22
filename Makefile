.PHONY: init test docs release

init:
	pip install -r requirements.txt

test:
	py.test

release: test
	python setup.py sdist upload

docs:
	$(MAKE) -C docs html
