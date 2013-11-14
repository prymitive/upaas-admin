/*
:copyright: Copyright 2013 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


window.UPAAS = window.UPAAS || {};


window.UPAAS.tasks_callback = function (data) {
    $('#upaas-tasks-badge').text(data.running);

    if (data.running > 0) {
        if ($('#upaas-tasks-badge').hasClass('active') == false) {
            $('#upaas-tasks-badge').addClass('active');
        }
    } else {
        $('#upaas-tasks-badge').removeClass('active');
    }

    var menu = new Array();

    if (data.tasks.length > 0) {
        $.each(data.tasks, function (i, task) {
            if (i > 0) {
                menu.push('<li role="presentation" class="divider"></li>');
            }

            if (i > 4 && data.tasks.length > 6) {
                menu.push('<li role="presentation" class="dropdown-header"></li>');
                menu.push('<li>');
                menu.push('<a href="#"> ' + gettext('and') + ' ' +
                              (data.tasks.length - i) + ' ' +
                              gettext('more tasks') + '</a>');
                menu.push('</li>');
                return false;
            }

            if (task.failed) {
                menu.push('<li role="presentation" class="dropdown-header upaas-task-failed">');
            } else {
                menu.push('<li role="presentation" class="dropdown-header">');
            }

            if (task.date_finished) {
                menu.push(gettext('Finished') + ': ' + moment(task.date_finished).fromNow());
            } else if (task.pending) {
                menu.push(gettext('Queued') + ': ' + moment(task.date_created).fromNow());
            } else {
                menu.push(gettext('Started') + ': ' + moment(task.locked_since).fromNow());
            }
            menu.push('</li>');

            if (task.failed) {
                menu.push('<li class="upaas-task-failed">');
            } else {
                menu.push('<li>');
            }
            if (task.subtasks.length > 0) {
                menu.push('<a href="' + Django.url('app_tasks', task.application.id) + '">');
            } else {
                menu.push('<a href="' + Django.url('app_task_details', task.task_id) + '">');
            }
            menu.push('<i class="' + task.icon + '"></i>');
            menu.push(task.title);
            if (task.subtasks.length > 0) {
                menu.push('<span class="badge pull-right upaas-task-tooltip">');
                menu.push(task.subtasks.length);
                menu.push('</span> ');
            }
            if (!task.pending) {
                menu.push('<div class="progress');
                if (!task.finished) menu.push(' active progress-striped');
                menu.push(' upaas-task-progressbar">');

                if (task.subtasks.length > 0) {
                    $.each(task.subtasks, function(j, subtask) {
                        var bar_class = 'progress-bar-default';
                        switch (j % 3) {
                            case 1:
                                bar_class = 'progress-bar-success';
                                break;
                            case 2:
                                bar_class = 'progress-bar-warning';
                                break;
                        }
                        menu.push('<div class="progress-bar ' + bar_class
                                  + '" role="progressbar" aria-valuenow="'
                                  + subtask.progress
                                  + '" aria-valuemin="0" aria-valuemax="100" style="width: '
                                  + subtask.progress + '%;">');
                        menu.push('<span class="sr-only">' + task.progress + '% Complete</span>');
                        menu.push('</div>');
                    });
                    menu.push('</div>');

                } else {
                    menu.push('<div class="progress-bar progress-bar-default" role="progressbar" aria-valuenow="'
                              + task.progress
                              + '" aria-valuemin="0" aria-valuemax="100" style="width: '
                              + task.progress + '%;">');
                    menu.push('<span class="sr-only">' + task.progress + '% Complete</span>');
                    menu.push('</div></div>');
                }
            }
            menu.push('</a>');
            menu.push('</li>');
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
            Dajaxice.upaas_admin.apps.applications.user_tasks(window.UPAAS.tasks_callback);
        },
        3000
    );
}


$(document).ready(function(){
    if (Django.user.is_authenticated) {
        Dajaxice.upaas_admin.apps.applications.user_tasks(window.UPAAS.tasks_callback);
    }
});
