.PHONY: init test

init:
	pip install -r requirements.txt

test:
	py.test
