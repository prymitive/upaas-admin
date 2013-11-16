/*
:copyright: Copyright 2013 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


window.UPAAS = window.UPAAS || {};


window.UPAAS.apps_updates_callback = function (data) {
    $('#upaas-tasks-badge').text(data.tasks.running);

    if (data.tasks.running > 0) {
        if ($('#upaas-tasks-badge').hasClass('active') == false) {
            $('#upaas-tasks-badge').addClass('active');
        }
    } else {
        $('#upaas-tasks-badge').removeClass('active');
    }

    var menu = new Array();

    if (data.tasks.list.length > 0) {
        $.each(data.tasks.list, function (i, task) {
            if (i > 0) {
                menu.push('<li role="presentation" class="divider"></li>');
            }

            if (i > 4 && data.tasks.length > 6) {
                //TODO move to template
                menu.push('<li role="presentation" class="dropdown-header"></li>');
                menu.push('<li>');
                menu.push('<a href="#"> ' + gettext('and') + ' ' +
                              (data.tasks.list.length - i) + ' ' +
                              gettext('more tasks') + '</a>');
                menu.push('</li>');
                return false;
            }

            menu.push(
                haml.compileHaml('upaas-tasks-dropdown-details')({
                    'task': task
                })
            )

        });
    } else {
        menu.push('<li>');
        menu.push('<a href="#">' + gettext('No running tasks') + '</a>');
        menu.push('</li>');
    }
    if ($('#upaas-tasks-menu').html() != menu.join('\n')) {
        $('#upaas-tasks-menu').html(menu.join('\n'));
    }

    window.setTimeout(
        function() {
            Dajaxice.upaas_admin.apps.applications.apps_updates(window.UPAAS.apps_updates_callback);
        },
        3000
    );
}
