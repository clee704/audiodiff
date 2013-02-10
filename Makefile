.PHONY: init test docs

init:
	pip install -r requirements.txt

test:
	py.test

docs:
	$(MAKE) -C docs html
