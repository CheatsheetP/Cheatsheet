.PHONY: format lint test

format:
	yapf --recursive -i --style ./style.ini ./tool ./searchcode ./controller

lint:
	pylint --disable=all --enable=E ./tool ./searchcode
