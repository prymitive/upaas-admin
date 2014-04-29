/*
:copyright: Copyright 2013-2014 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


window.UPAAS = window.UPAAS || {};
window.UPAAS.applications = window.UPAAS.applications || {};


//= Applications ===============================================================


window.UPAAS.applications.ApplicationModel = Backbone.Model.extend({});
window.UPAAS.applications.ApplicationCollection = Backbone.Collection.extend({
   model: window.UPAAS.applications.ApplicationModel,
   url : "/api/v1/application/?format=json"
});
window.UPAAS.applications.Applications = new window.UPAAS.applications.ApplicationCollection();

window.UPAAS.applications.parse_updates = function(data) {
    window.UPAAS.utils.update_badge('.upaas-user-badge-apps', data.collection.length);

    // update apps badges
    $.each(data.collection.models, function (i, app) {
        window.UPAAS.utils.update_badge('.upaas-app-' + app.attributes.id + '-badge-packages', app.attributes.packages.length);
        window.UPAAS.utils.update_badge('.upaas-app-' + app.attributes.id + '-badge-tasks', app.attributes.tasks.length);
        //window.UPAAS.utils.update_badge('.upaas-app-' + app.attributes.id + '-badge-instances', app.attributes.instances); // TODO
    });
}
window.UPAAS.utils.bind_backbone(window.UPAAS.applications.Applications, window.UPAAS.applications.parse_updates);


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
