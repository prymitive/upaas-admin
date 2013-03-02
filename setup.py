#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from setuptools import setup, find_packages


setup(
    name='upaas_admin',
    version='0.1',
    description="",
    author="Łukasz Mierzwa",
    author_email='l.mierzwa@gmail.com',
    url='',
    packages=find_packages(),
    package_data={'upaas_admin': ['static/*.*', 'templates/*.*']},
    scripts=['manage.py'],
)
