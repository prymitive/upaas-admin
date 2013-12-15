/*
:copyright: Copyright 2013 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


$(document).ready(function(){
    $('.nav-tabs').tabdrop({
        text: '<i class="fa fa-align-justify"></i>'
    });

    $('.upaas-help-tooltip').tooltip({container: '.upaas-content'});

    if (Django.user.is_authenticated) {
        Dajaxice.upaas_admin.apps.applications.apps_updates(
            window.UPAAS.apps_updates_callback
        );
    }
});
