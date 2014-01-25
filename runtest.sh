#!/bin/bash

UPAAS_CONFIG_DIR=tests DJANGO_SETTINGS_MODULE=upaas_admin.settings.tests coverage run --rcfile=.coveragerc `which py.test` -v --pep8 -p no:cov $@
if [ -z $1 ]; then
    coverage report
    coverage html -d htmlcov
fi
