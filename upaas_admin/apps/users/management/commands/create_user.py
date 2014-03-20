# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from optparse import make_option

from upaas_admin.apps.users.models import User


class Command(BaseCommand):

    help = 'Create new user account'

    option_list = BaseCommand.option_list + (
        make_option('--login', dest='login', help='New user login'),
        make_option('--firstname', dest='firstname',
                    help='New user first name'),
        make_option('--lastname', dest='lastname', help='New user last name'),
        make_option('--email', dest='email', help='New user email address'),
        make_option('--admin', action='store_true', dest='admin',
                    default=False,
                    help='Give administrator privileges to new user'),
        make_option('--password', dest='password', help='New user password'))

    def handle(self, *args, **options):
        for name in ['login', 'firstname', 'lastname', 'email']:
            if not options.get(name):
                raise CommandError("--%s option must be set" % name)

        password = options.get('password')
        if not password:
            try:
                password1 = getpass('Password: ')
                password2 = getpass('Password (repeat): ')
                while password1 != password2:
                    self.stdout.write('Password mismatch!\n')
                    password1 = getpass('Password: ')
                    password2 = getpass('Password (repeat): ')
            except KeyboardInterrupt:
                self.stdout.write('\nCtrl+c pressed, aborting\n')
                return
            else:
                password = password1

        user = User(username=options['login'],
                    first_name=options['firstname'],
                    last_name=options['lastname'],
                    email=options['email'],
                    is_superuser=options['admin'])
        user.set_password(password)
        user.save()
        self.stdout.write('%s user account created '
                          'successfully\n' % user.username)
