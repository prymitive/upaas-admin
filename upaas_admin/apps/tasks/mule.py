# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.core.management import call_command


if __name__ == '__main__':
    call_command('mule_builder')
