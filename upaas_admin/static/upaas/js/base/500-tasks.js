/*
:copyright: Copyright 2014 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


window.UPAAS = window.UPAAS || {};
window.UPAAS.tasks = window.UPAAS.tasks || {};


window.UPAAS.tasks.TaskModel = Backbone.Model.extend({});


//= All tasks ==================================================================

window.UPAAS.tasks.TaskCollection = Backbone.Collection.extend({
   model: window.UPAAS.tasks.TaskModel,
   url : "/api/v1/task/?format=json"
});
window.UPAAS.tasks.Tasks = new window.UPAAS.tasks.TaskCollection();


window.UPAAS.tasks.parse_tasks = function(data) {
    window.UPAAS.utils.update_badge('.upaas-user-badge-tasks', data.collection.length);
}
window.UPAAS.utils.bind_backbone(window.UPAAS.tasks.Tasks, window.UPAAS.tasks.parse_tasks);


//= Only running tasks =========================================================

window.UPAAS.tasks.RunningTaskCollection = Backbone.Collection.extend({
   model: window.UPAAS.tasks.TaskModel,
   url : "/api/v1/task/?format=json&limit=5&status=RUNNING"
});
window.UPAAS.tasks.RunningTasks = new window.UPAAS.tasks.RunningTaskCollection();


window.UPAAS.tasks.running_task_dict = {};


window.UPAAS.tasks.render_task_menu_item = function(task) {
    var app = window.UPAAS.applications.Applications.where({
        resource_uri: task.attributes.application
    })[0];
    var task_html = haml.compileHaml('upaas-tasks-dropdown-details')({
        task: task.attributes,
        application: app.attributes
    });

    if (task.attributes.id in window.UPAAS.tasks.running_task_dict) {
        if (window.UPAAS.tasks.running_task_dict[task.attributes.id] != task_html) {
            window.UPAAS.tasks.running_task_dict[task.attributes.id] = task_html;

            var header = $(task_html).filter('.dropdown-header').first();
            $('#upaas-task-menu-header-' + task.attributes.id).html(header.html());
            $('#upaas-task-menu-header-' + task.attributes.id).replaceWith(header);

            var body = $(task_html).filter('.upaas-task-link').first();
            $('#upaas-task-menu-item-' + task.attributes.id).html(body.html());
            $('#upaas-task-menu-item-' + task.attributes.id).replaceWith(body);
        }
    } else {
        if (Object.keys(window.UPAAS.tasks.running_task_dict).length > 0) {
            var divider_html = haml.compileHaml('upaas-tasks-dropdown-divider')({
                task: task.attributes
            });
            $('#upaas-tasks-menu').append(divider_html);
        }
        window.UPAAS.tasks.running_task_dict[task.attributes.id] = task_html;
        $('#upaas-tasks-menu').append(task_html);
    }
}


window.UPAAS.tasks.update_task_menu_badge = function(task) {
    $('#upaas-tasks-badge').text(task.collection.length);
    if (task.collection.length > 0) {
        $('#upaas-tasks-badge').addClass('active');
        $('#upaas-tasks-menu-li-dummy').hide();
    } else {
        $('#upaas-tasks-badge').removeClass('active');
        $('#upaas-tasks-menu-li-dummy').show();
    }
}

window.UPAAS.tasks.parse_running_task = function(task) {
    window.UPAAS.tasks.update_task_menu_badge(task);
    window.UPAAS.tasks.render_task_menu_item(task);
}
window.UPAAS.utils.bind_backbone(window.UPAAS.tasks.RunningTasks, window.UPAAS.tasks.parse_running_task, ['remove']);


window.UPAAS.tasks.parse_removed_running_task = function(data) {
    window.UPAAS.tasks.update_task_menu_badge(data);
    var task = window.UPAAS.tasks.Tasks.where({id: data.attributes.id})[0];
    window.UPAAS.tasks.render_task_menu_item(task);
    setTimeout(function(){
        $('#upaas-task-menu-header-' + task.attributes.id).remove();
        $('#upaas-task-menu-item-' + task.attributes.id).remove();
        $('#upaas-task-menu-divider-' + task.attributes.id).remove();
        $('#upaas-tasks-menu').children('li').not('#upaas-tasks-menu-li-dummy').first().filter('.divider').remove();
    }, 60*1000);
}

window.UPAAS.tasks.RunningTasks.bind('remove', window.UPAAS.tasks.parse_removed_running_task);


//= Init =======================================================================

window.UPAAS.tasks.init = function() {
    window.UPAAS.tasks.task_poller = Backbone.Poller.get(window.UPAAS.tasks.Tasks);
    window.UPAAS.tasks.task_poller.set({delay: 5000}).start();

    window.UPAAS.tasks.running_task_poller = Backbone.Poller.get(window.UPAAS.tasks.RunningTasks);
    window.UPAAS.tasks.running_task_poller.set({delay: 5000}).start();
}
