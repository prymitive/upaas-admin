# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from upaas_admin.common.forms import CrispyMongoForm
from upaas_admin.apps.scheduler.models import ApplicationRunPlan


class ApplicationRunPlanForm(CrispyMongoForm):

    submit_label = 'Start'
    submit_icon_class = 'fa fa-play'
    # FIXME patch crispy form-horizontal to support checkboxes
    form_class = ''
    label_class = ''
    field_class = ''
    layout = ['workers_min', 'workers_max']

    class Meta:
        document = ApplicationRunPlan
        exclude = ('application', 'backends', 'memory_per_worker')

    def clean(self):
        workers_min = self.cleaned_data.get('workers_min')
        workers_max = self.cleaned_data.get('workers_max')

        if not self.instance.id:
            apps_running = self.user.limits_usage['running_apps']
            apps_limit = self.user.limits['running_apps']
            if apps_limit and apps_running >= apps_limit:
                raise forms.ValidationError(
                    _("Already running maximum allowed applications "
                      "({count}), can't start another one").format(
                        count=apps_running))

        if workers_min is None or workers_max is None:
            return self.cleaned_data

        if workers_min > workers_max:
            raise forms.ValidationError(_("Minimum workers number cannot be"
                                          "lower than maximum"))

        workers_used = self.user.limits_usage['workers']
        if self.instance.id:
            run_plan = ApplicationRunPlan.objects(id=self.instance.id).first()
            workers_used -= run_plan.workers_max
        workers_limit = self.user.limits['workers']
        if workers_limit:
            workers_available = max(workers_limit - workers_used, 0)
            if workers_min > workers_available:
                raise forms.ValidationError(_(
                    "Only {available} workers available, cannot set "
                    "{workers} as minimum ").format(
                    available=workers_available, workers=workers_min))
            if workers_max > workers_available:
                raise forms.ValidationError(_(
                    "Only {available} workers available, cannot set "
                    "{workers} as maximum ").format(
                    available=workers_available, workers=workers_max))

        return self.cleaned_data


class EditApplicationRunPlanForm(ApplicationRunPlanForm):

    submit_label = 'Save'

    class Meta:
        document = ApplicationRunPlan
        exclude = ('application', 'backends', 'memory_per_worker')
