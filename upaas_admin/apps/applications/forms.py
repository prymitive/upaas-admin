# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from dns.resolver import query, NXDOMAIN, NoAnswer

from upaas.config.metadata import MetadataConfig

from crispy_forms.layout import HTML

from django import forms
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from upaas_admin.common.forms import (CrispyForm, CrispyMongoForm,
                                      InlineCrispyMongoForm)
from upaas_admin.apps.applications.models import Application


log = logging.getLogger(__name__)


class _MetadataForm(object):

    def clean_metadata(self):
        metadata = self.cleaned_data['metadata']
        try:
            meta = metadata.read()
            MetadataConfig.from_string(meta)
            metadata = meta
        except Exception, e:
            raise forms.ValidationError(_(u"%s" % e))
        return metadata


class RegisterApplicationForm(CrispyMongoForm, _MetadataForm):

    submit_label = 'Register'
    form_action = reverse_lazy('app_register')
    layout = ['name', 'metadata']

    class Meta:
        document = Application
        fields = ('name',)

    metadata = forms.FileField()

    def clean_name(self):
        name = self.cleaned_data['name']
        if ' ' in name:
            raise forms.ValidationError(_(u"Name cannot contain spaces"))
        if self.owner.applications.filter(name=name).first():
            raise forms.ValidationError(_(
                u"Application with name {name} already registered").format(
                name=name))
        return self.cleaned_data['name']


class UpdateApplicationMetadataForm(CrispyMongoForm, _MetadataForm):

    submit_label = 'Update'
    layout = ['metadata']

    class Meta:
        document = Application
        fields = ('metadata',)

    metadata = forms.FileField()


class UpdateApplicationMetadataInlineForm(InlineCrispyMongoForm,
                                          _MetadataForm):

    submit_label = 'Update'
    layout = [
        HTML(u"<b>%s:</b>" % _(u"New metadata")),
        'metadata'
    ]

    class Meta:
        document = Application
        fields = ('metadata',)

    metadata = forms.FileField()


class BuildPackageForm(CrispyForm):

    submit_label = 'Build'
    submit_icon_class = 'fa fa-cog'
    layout = ['force_fresh']

    force_fresh = forms.BooleanField(required=False)


class StopApplicationForm(CrispyForm):

    submit_label = 'Stop'
    submit_icon_class = 'fa fa-stop'
    layout = ['confirm']

    confirm = forms.BooleanField(required=True)


class RollbackApplicationForm(CrispyForm):

    submit_label = 'Rollback'
    submit_icon_class = 'fa fa-undo'
    layout = ['confirm']

    confirm = forms.BooleanField(required=True)


class ApplicatiomMetadataFromPackageForm(CrispyForm):

    submit_label = 'Save'
    submit_icon_class = 'fa fa-undo'
    layout = ['confirm']

    confirm = forms.BooleanField(required=True)


class DeletePackageForm(CrispyForm):

    submit_label = 'Delete'
    submit_css_class = 'btn-danger'
    submit_icon_class = 'fa fa-trash-o'
    layout = ['confirm']

    confirm = forms.BooleanField(required=True)


class AssignApplicatiomDomainForm(CrispyForm):

    submit_label = 'Assign'
    layout = ['domain']

    domain = forms.CharField(required=True)

    def clean_domain(self):
        domain = self.cleaned_data['domain']
        try:
            txt_records = query(domain, 'TXT')
        except NXDOMAIN:
            raise forms.ValidationError(_(
                u"Domain {domain} does not exist").format(domain=domain))
        except NoAnswer:
            raise forms.ValidationError(_(
                u"No TXT record for domain {domain}").format(domain=domain))
        except Exception, e:
            log.error(_(u"Exception during '{domain}' verification: "
                        u"{e}").format(domain=domain, e=e))
            raise forms.ValidationError(_(
                u"Unhandled exception during domain verification, please try "
                u"again later"))
        else:
            if Application.objects(domains__name=domain):
                raise forms.ValidationError(_(u"Domain {domain} was already "
                                              u"assigned").format(
                    domain=domain))
            if self.needs_validation:
                for record in txt_records:
                    if self.app.domain_validation_code in record.strings:
                        self.domain_validated = True
                        return domain
                raise forms.ValidationError(_(
                    u"No verification code in TXT record for {domain}").format(
                    domain=domain))
            else:
                return domain


class RemoveApplicatiomDomainForm(CrispyForm):

    submit_label = 'Remove'
    submit_css_class = 'btn-danger'
    submit_icon_class = 'fa fa-trash-o'
    layout = ['domain', 'confirm']

    domain = forms.CharField(widget=forms.HiddenInput(), required=True)
    confirm = forms.BooleanField(required=True)
