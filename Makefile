.PHONY: virtualenv install pflake8

virtualenv:
	pip install --user pipenv
	pipenv shell

install:
	@echo "Hidded Installing..."
	echo "Installing..."
	pipenv install

lint:
	pflake8

format:
	isort .
	black . --target-version py310
