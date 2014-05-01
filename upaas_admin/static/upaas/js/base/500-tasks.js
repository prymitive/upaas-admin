/*
:copyright: Copyright 2014 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


window.UPAAS = window.UPAAS || {};
window.UPAAS.tasks = window.UPAAS.tasks || {};


window.UPAAS.tasks.TaskModel = Backbone.Model.extend({
    urlRoot: '/api/v1/task/',
    url: function() {
        return Backbone.Model.prototype.url.call(this) + '?format=json';
    }
});


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
    url : "/api/v1/task/?format=json&status=RUNNING"
});
window.UPAAS.tasks.RunningTasks = new window.UPAAS.tasks.RunningTaskCollection();


window.UPAAS.tasks.running_task_dict = {};


window.UPAAS.tasks.render_task_menu_item = function(task) {
    var app = window.UPAAS.utils.where_or_get_first(window.UPAAS.applications.Applications, {
        resource_uri: task.attributes.application
    });
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
    }
}

window.UPAAS.tasks.parse_running_task = function(task) {
    window.UPAAS.tasks.update_task_menu_badge(task);
    window.UPAAS.tasks.render_task_menu_item(task);
}
window.UPAAS.utils.bind_backbone(window.UPAAS.tasks.RunningTasks, window.UPAAS.tasks.parse_running_task, ['remove']);


window.UPAAS.tasks.parse_removed_running_task = function(data) {
    window.UPAAS.tasks.update_task_menu_badge(data);
    var task = window.UPAAS.utils.where_or_get_first(window.UPAAS.tasks.Tasks, {id: data.attributes.id});
    window.UPAAS.tasks.render_task_menu_item(task);
    setTimeout(function(){
        $('#upaas-task-menu-header-' + task.attributes.id).remove();
        $('#upaas-task-menu-item-' + task.attributes.id).remove();
        $('#upaas-task-menu-divider-' + task.attributes.id).remove();
        delete window.UPAAS.tasks.running_task_dict[task.attributes.id];
        $('#upaas-tasks-menu').children('li').not('#upaas-tasks-menu-li-dummy').first().filter('.divider').remove();
        if ($('#upaas-tasks-menu').children('li').not('#upaas-tasks-menu-li-dummy').length == 0) {
            $('#upaas-tasks-menu-li-dummy').show();
        }
    }, 60*1000);
}

window.UPAAS.tasks.RunningTasks.bind('remove', window.UPAAS.tasks.parse_removed_running_task);


//= Messages ===================================================================

window.UPAAS.tasks.TaskMessageModel = Backbone.Model.extend({});


window.UPAAS.tasks.parse_task_messages = function(data) {
    var old_offset = data.offset;
    data.update_offset();
    if (data.offset > old_offset) {
        var messages = new Array();
        $.each(data.models, function(i, msg) {
            messages.push(
                haml.compileHaml('upaas-haml-template-task-messages')({
                    message: msg.attributes
                })
            );
        });
        if (messages.length > 0) {
            $('#upaas-task-messages-table tbody').append(messages.join('\n'));
            $('.upaas-messages-table-area').animate({
                scrollTop: $('.upaas-messages-table-area').get(0).scrollHeight
                }, 300);
        }
    }
}


window.UPAAS.tasks.create_task_messages_collection = function(task_url) {
    var collection = Backbone.Collection.extend({
        model: window.UPAAS.tasks.TaskMessageModel,
        task_url: task_url,
        offset: 0,
        url: function() {
            return this.task_url + 'messages/?format=json&offset=' + this.offset;
        },
        update_offset: function() {
            this.offset = this.offset + this.length;
        }
    });
    var col = new collection(task_url);
    col.bind('sync', window.UPAAS.tasks.parse_task_messages);
    return col;
}


//= Init =======================================================================

window.UPAAS.tasks.init = function() {
    // enable once used more widely
    // window.UPAAS.tasks.task_poller = Backbone.Poller.get(window.UPAAS.tasks.Tasks);
    // window.UPAAS.tasks.task_poller.set({delay: 5000}).start();

    window.UPAAS.tasks.running_task_poller = Backbone.Poller.get(window.UPAAS.tasks.RunningTasks);
    window.UPAAS.tasks.running_task_poller.set({delay: 4000}).start();
}
