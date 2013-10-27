#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from setuptools import setup, find_packages

try:
    from pip.req import parse_requirements
    required = parse_requirements('requirements.txt')
except ImportError:
    required = []


setup(
    name='upaas-admin',
    version='0.1-dev28',
    license='GPLv3',
    description="UPaaS admin API and UI",
    author="Łukasz Mierzwa",
    author_email='l.mierzwa@gmail.com',
    url='',
    packages=find_packages(),
    include_package_data=True,
    scripts=['upaas_admin/upaas_admin'],
    install_requires=[str(r.req) for r in required],
)
