#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from setuptools import setup, find_packages
from pip.req import parse_requirements


required = parse_requirements('requirements.txt')


setup(
    name='upaas-admin',
    version='0.1-dev',
    license='GPLv3',
    description="",
    author="Łukasz Mierzwa",
    author_email='l.mierzwa@gmail.com',
    url='',
    packages=find_packages(),
    package_data={'upaas_admin': ['static/*.*', 'templates/*.*']},
    scripts=['upaas_admin/manage.py'],
    install_requires=[str(r.req) for r in required],
)
