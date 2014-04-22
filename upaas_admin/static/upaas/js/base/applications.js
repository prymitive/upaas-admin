/*
:copyright: Copyright 2013-2014 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


window.UPAAS = window.UPAAS || {};
window.UPAAS.applications = window.UPAAS.applications || {};


window.UPAAS.apps_updates_callback = function (data) {
    $('#upaas-tasks-badge').text(data.tasks.running);

    // update apps badges
    $.each(data.apps.list, function (i, app) {
        window.UPAAS.update_badge('.upaas-app-' + app.id + '-badge-packages', app.packages);
        window.UPAAS.update_badge('.upaas-app-' + app.id + '-badge-instances', app.instances);
        window.UPAAS.update_badge('.upaas-app-' + app.id + '-badge-tasks', app.active_tasks.length);
        window.UPAAS.update_badge('.upaas-user-badge-apps', data.apps.list.length);
        window.UPAAS.update_badge('.upaas-user-badge-recent_tasks', data.tasks.recent);
    });

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

            if (i > 4 && data.tasks.list.length > 6) {
                //TODO move to template
                menu.push('<li role="presentation" class="dropdown-header"></li>');
                menu.push('<li>');
                menu.push('<a href="' + Django.url('users_tasks') + '"> ' + gettext('and') + ' ' +
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
        menu.push('<a href="' + Django.url('users_tasks') + '">' + gettext('No running tasks') + '</a>');
        menu.push('</li>');
    }
    if ($('#upaas-tasks-menu').html() != menu.join('')) {
        $('#upaas-tasks-menu').html(menu.join(''));
    }

    window.setTimeout(
        function() {
            Dajaxice.upaas_admin.apps.applications.apps_updates(window.UPAAS.apps_updates_callback);
        },
        3000
    );
}


//= Applications ===============================================================


window.UPAAS.applications.ApplicationModel = Backbone.Model.extend({});
window.UPAAS.applications.ApplicationCollection = Backbone.Collection.extend({
   model: window.UPAAS.applications.ApplicationModel,
   url : "/api/v1/application/?format=json"
});
window.UPAAS.applications.Applications = new window.UPAAS.applications.ApplicationCollection();

window.UPAAS.applications.parse_updates = function(data) {
    window.UPAAS.utils.update_badge('.upaas-user-badge-apps', data.collection.length);
}

window.UPAAS.applications.Applications.bind('add', window.UPAAS.applications.parse_updates);
window.UPAAS.applications.Applications.bind('remove', window.UPAAS.applications.parse_updates);
window.UPAAS.applications.Applications.bind('reset', window.UPAAS.applications.parse_updates);
window.UPAAS.applications.Applications.bind('change', window.UPAAS.applications.parse_updates);
window.UPAAS.applications.Applications.bind('destroy', window.UPAAS.applications.parse_updates);


//= Packages ===================================================================


window.UPAAS.applications.PackageModel = Backbone.Model.extend({});
window.UPAAS.applications.PackageCollection = Backbone.Collection.extend({
   model: window.UPAAS.applications.PackageModel,
   url : "/api/v1/package/?format=json"
});
window.UPAAS.applications.Packages = new window.UPAAS.applications.PackageCollection();


//= INIT =======================================================================

window.UPAAS.applications.init = function() {
    window.UPAAS.applications.app_poller = Backbone.Poller.get(window.UPAAS.applications.Applications);
    window.UPAAS.applications.app_poller.set({delay: 5000}).start();
}
