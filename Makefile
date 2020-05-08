.PHONY: format lint test

format:
	yapf --recursive -i --style ./style.ini ./tool ./searchcode ./cleancode

lint:
	pylint --disable=all --enable=E ./tool ./searchcode ./cleancode
