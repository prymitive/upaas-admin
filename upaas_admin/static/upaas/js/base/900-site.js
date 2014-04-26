/*
:copyright: Copyright 2013-2014 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


Backbone.Tastypie.csrfToken = Django.csrf_token();


$(document).ready(function(){
    $('.nav-tabs').tabdrop({
        text: '<i class="fa fa-align-justify"></i>'
    });

    $('.upaas-help-tooltip').tooltip({container: '.upaas-content'});

    // http://jsfiddle.net/VEKYN/
    $('.upaas-dropdown-menu-form').on('click', function(e) {
        if($(this).hasClass('upaas-dropdown-menu-form')) {
            e.stopPropagation();
        }
    });

    if (Django.user.is_authenticated) {
        window.UPAAS.applications.init();
        window.UPAAS.tasks.init();
    }
});
