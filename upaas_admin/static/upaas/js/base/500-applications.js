/*
:copyright: Copyright 2013-2014 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


window.UPAAS = window.UPAAS || {};
window.UPAAS.applications = window.UPAAS.applications || {};


//= Applications ===============================================================


window.UPAAS.applications.ApplicationModel = Backbone.Model.extend({
    urlRoot: '/api/v1/application/',
    url: function() {
        return Backbone.Model.prototype.url.call(this) + '?format=json';
    }
});

window.UPAAS.applications.ApplicationCollection = Backbone.Collection.extend({
   model: window.UPAAS.applications.ApplicationModel,
   url : "/api/v1/application/?format=json"
});
window.UPAAS.applications.Applications = new window.UPAAS.applications.ApplicationCollection();

window.UPAAS.applications.parse_updates = function(data) {
    window.UPAAS.utils.update_badge('.upaas-user-badge-apps', data.collection.length);

    // update apps badges and icons
    $.each(data.collection.models, function (i, app) {
        window.UPAAS.utils.update_badge('.upaas-app-' + app.attributes.id + '-badge-packages', app.attributes.packages.length);
        window.UPAAS.utils.update_badge('.upaas-app-' + app.attributes.id + '-badge-tasks', app.attributes.tasks.length);
        window.UPAAS.utils.update_badge('.upaas-app-' + app.attributes.id + '-badge-instances', app.attributes.instance_count);
        if (app.attributes.instance_count > 0) {
            $('#upaas-app-status-icon-' + app.attributes.id).removeClass('fa-stop').addClass('fa-play');
        } else {
            $('#upaas-app-status-icon-' + app.attributes.id).removeClass('fa-play').addClass('fa-stop');
        }
    });
}
window.UPAAS.utils.bind_backbone(window.UPAAS.applications.Applications, window.UPAAS.applications.parse_updates);


//= Packages ===================================================================


window.UPAAS.applications.PackageModel = Backbone.Model.extend({
    urlRoot: '/api/v1/application/',
    url: function() {
        return Backbone.Model.prototype.url.call(this) + '?format=json';
    }
});

window.UPAAS.applications.PackageCollection = Backbone.Collection.extend({
   model: window.UPAAS.applications.PackageModel,
   url : "/api/v1/package/?format=json"
});
window.UPAAS.applications.Packages = new window.UPAAS.applications.PackageCollection();


//= Instances ==================================================================

window.UPAAS.applications.parse_instances = function(data) {
    var instances_html = new Array();
    $.each(data.models, function (i, instance) {
        instances_html.push(
            haml.compileHaml('upaas-haml-template-instance')({
                instance: instance.attributes
            })
        );
    });
    if (instances_html.length == 0) {
        instances_html.push(
            haml.compileHaml('upaas-haml-template-stopped')()
        );
    }
    $('#stats-container').html(instances_html.join('\n'));
}

window.UPAAS.applications.InstanceModel = Backbone.Model.extend({});

window.UPAAS.applications.create_application_instances_collection = function(app_url) {
    var collection = Backbone.Collection.extend({
        model: window.UPAAS.applications.InstanceModel,
        url: app_url + 'instances/?format=json'
    });
    var col = new collection(app_url);
    col.bind('sync', window.UPAAS.applications.parse_instances);
    return col;
}


//= INIT =======================================================================

window.UPAAS.applications.init = function() {
    window.UPAAS.applications.app_poller = Backbone.Poller.get(window.UPAAS.applications.Applications);
    window.UPAAS.applications.app_poller.set({delay: 5000}).start();
}
