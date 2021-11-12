NAME := ldap2db
FOLDERS := ./app/ ./tests/

.DEFAULT_GOAL := help


.PHONY: help
help:
	@echo "Available make commands:"
	@echo ""
	@echo "  install     install packages and prepare environment"
	@echo "  clean       remove all temporary files"
	@echo "  lint        run the code linters"
	@echo "  format      reformat code"
	@echo "  test        run all the tests"
	@echo "  coverage    run tests and generate coverage report"
	@echo "  server      start uvicorn development server and serve application locally"
	@echo "  debug			 start server in debugging mode for auto restarting after code changes etc."
	@echo "  dockerrun   run docker image and serve web application in docker (normally only needed if there are deploy issues)"
	@echo ""


.PHONY: install
install:
	mkdir -p python_env; \
	python3 -m venv python_env; \
	. python_env/bin/activate; \
	python3 -m pip install --upgrade pip; \
	python3 -m pip install -r requirements.txt; \
	python3 -m pip install -r requirements-test.txt


.PHONY: clean
clean:
	find . -type d -name "__pycache__" | xargs rm -rf {}; \
	rm -rf .coverage htmlcov


.PHONY: lint
lint:
	@. python_env/bin/activate; \
	flake8 --max-line-length=120 --exclude=.git,python_env,__pycache__


.PHONY: format
format:
	@. python_env/bin/activate; \
	autopep8 --in-place -r app; \
	autopep8 --in-place -r tests;

.PHONY: test
test:
	@. python_env/bin/activate; \
	python -m pytest -vv


.PHONY: dockerrun
dockerrun:
	make -f Makefile-docker build && make -f Makefile-docker app


.PHONY: coverage
coverage:
	@. python_env/bin/activate; \
	python -m pytest --cov-config=.coveragerc --cov . .  --cov-report html --cov-report term


.PHONY: server
server:
	@cat "app/static/ascii_logo.txt"
	@echo "                 Server/benchmark mode, running on http://localhost:8080 \n\n"
	@. python_env/bin/activate; \
	uwsgi -i uwsgi.ini

.PHONY: debug
debug:
	@cat "app/static/ascii_logo.txt"
	@echo "                 Develop and debugging mode, running on http://localhost:8080 \n\n"
	@. python_env/bin/activate; \
	python debug.py

