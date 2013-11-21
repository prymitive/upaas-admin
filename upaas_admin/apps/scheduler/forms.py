# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django import forms
from django.utils.translation import ugettext_lazy as _

from upaas_admin.common.forms import CrispyMongoForm
from upaas_admin.apps.scheduler.models import ApplicationRunPlan


class ApplicationRunPlanForm(CrispyMongoForm):

    submit_label = 'Start'
    submit_icon_class = 'fa fa-play'
    #FIXME patch crispy form-horizontal to support checkboxes
    form_class = ''
    label_class = ''
    field_class = ''
    layout = ['instances_min', 'instances_max', 'workers_max']

    class Meta:
        document = ApplicationRunPlan
        exclude = ('application', 'backends')

    def clean(self):
        instances_min = self.cleaned_data.get('instances_min')
        instances_max = self.cleaned_data.get('instances_max')
        workers = self.cleaned_data.get('workers_max')

        if instances_min is None or instances_max is None or workers is None:
            return self.cleaned_data

        if instances_min > instances_max:
            raise forms.ValidationError(_(u"Minimum instances count cannot be "
                                          u"higher than maximum"))

        instances_used = self.user.limits_usage['instances']
        instances_limit = self.user.limits['instances']
        if instances_limit:
            instances_available = instances_limit - instances_used
            if instances_min > instances_available:
                raise forms.ValidationError(_(
                    u"Only {available} instances available, cannot set "
                    u"{minimum} as minimum ").format(
                    available=instances_available, minimum=instances_min))
            if instances_max > instances_available:
                raise forms.ValidationError(_(
                    u"Only {available} instances available, cannot set "
                    u"{maximum} as maximum ").format(
                    available=instances_available, maximum=instances_max))

        workers_used = self.user.limits_usage['workers']
        workers_limit = self.user.limits['workers']
        if workers_limit:
            workers_available = workers_limit - workers_used
            if workers > workers_available:
                raise forms.ValidationError(_(
                    u"Only {available} workers available, cannot set "
                    u"{workers} as limit ").format(
                    available=workers_available, workers=workers))

        return self.cleaned_data


class EditApplicationRunPlanForm(ApplicationRunPlanForm):

    submit_label = 'Save'

    class Meta:
        document = ApplicationRunPlan
        exclude = ('application', 'backends')
