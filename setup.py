#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from setuptools import setup, find_packages

try:
    from pip.req import parse_requirements
    required = {'install_requires': [str(r.req) for r in parse_requirements(
        'requirements.txt')]}
except ImportError:
    required = {}


setup(
    name='upaas-admin',
    version='0.3-dev',
    license='GPLv3',
    description="UPaaS admin API and UI",
    author="Łukasz Mierzwa",
    author_email='l.mierzwa@gmail.com',
    url='',
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    scripts=['upaas_admin/upaas_admin'],
    **required
)
