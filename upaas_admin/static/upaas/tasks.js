/*
:copyright: Copyright 2013 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


function tasks_callback(data) {
    $('#upaas-tasks-badge').text(data.running);

    var menu = new Array();

    if (data.tasks.length > 0) {
        $.each(data.tasks, function (i, task) {
            if (i > 0) {
                menu.push('<li role="presentation" class="divider"></li>');
            }

            if (i > 5 && data.tasks.length > 6) {
                menu.push('<li role="presentation" class="dropdown-header"></li>');
                menu.push('<li>');
                menu.push('<a href="#"> ' + gettext('and') + ' ' +
                              (data.tasks.length - i) + ' ' +
                              gettext('more tasks') + '</a>');
                menu.push('</li>');
                return false;
            }

            menu.push('<li role="presentation" class="dropdown-header">');

            if (task.date_finished) {
                menu.push(gettext('Finished') + ': ' + moment(task.date_finished).fromNow());
            } else if (task.pending) {
                menu.push(gettext('Queued') + ': ' + moment(task.date_created).fromNow());
            } else {
                menu.push(gettext('Started') + ': ' + moment(task.locked_since).fromNow());
            }
            menu.push('</li>');

            menu.push('<li>');
            menu.push('<a href="' + Django.url('app_details', task.application.id) + '">');
            menu.push('<span class="glyphicon ' + task.icon + '"></span>');
            menu.push(task.title);
            if (!task.pending && task.progress >= 0) {
                menu.push('<div class="progress progress-tasks-menu">')
                menu.push('<div class="progress-bar" role="progressbar" aria-valuenow="'
                              + task.progress
                              + '" aria-valuemin="0" aria-valuemax="100" style="width: '
                              + task.progress + '%;">');
                menu.push('<span class="sr-only">' + task.progress + '% Complete</span>');
                menu.push('</div></div>');
            }
            menu.push('</a>');
            menu.push('</li>');
        });
    } else {
        menu.push('<li>');
        menu.push('<a href="#">' + gettext('No running tasks') + '</a>');
        menu.push('</li>');
    }
    $('#upaas-tasks-menu').html(menu.join('\n'));

    window.setTimeout(
        function() {
            Dajaxice.upaas_admin.apps.tasks.user_tasks(tasks_callback);
        },
        3000
    );
}


$(document).ready(function(){
    if (Django.user.is_authenticated) {
        Dajaxice.upaas_admin.apps.tasks.user_tasks(tasks_callback);
    }
});
