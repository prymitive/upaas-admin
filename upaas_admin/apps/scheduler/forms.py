# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django import forms
from django.utils.translation import ugettext_lazy as _

from upaas_admin.contrib.forms import CrispyForm
from upaas_admin.apps.scheduler.models import ApplicationRunPlan


class ApplicationRunPlanForm(CrispyForm):

    submit_label = 'Start'
    layout = ['memory_limit']

    class Meta:
        document = ApplicationRunPlan
        exclude = ('application', 'backends')

    def clean_memory_limit(self):
        memory_limit = self.cleaned_data['memory_limit']
        budget_limit = self.user.budget['memory_limit']
        if memory_limit > budget_limit:
            raise forms.ValidationError(_(u"User memory budget is only %d MB, "
                                          u"can't set higher application "
                                          u"memory limit" % budget_limit))
        return memory_limit
