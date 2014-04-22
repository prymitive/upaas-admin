/*
:copyright: Copyright 2013 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


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
        // FIXME replace with backbone loop
    }
});
