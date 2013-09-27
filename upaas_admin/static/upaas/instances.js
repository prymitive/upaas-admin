/*
:copyright: Copyright 2013 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


function instances_data_from_uwsgi_stats(data) {
    var elems = new Array();
    if (data.stats.length > 0) {
        $.each(data.stats, function (i, item) {
            elems.push('<div class="panel panel-default">');
            elems.push('<div class="panel-heading">' + item.backend.name + '</div>');
            elems.push('<div class="panel-body">');

            elems.push('<table class="table-bordered table-condensed table-hover upaas-instance-table"><thead><tr>');
            elems.push('<th>' + gettext('#') + '</th>');
            elems.push('<th>' + gettext('State') + '</th>');
            elems.push('<th>' + gettext('Memory') + '</th>');
            elems.push('<th>' + gettext('Restarts') + '</th>');
            elems.push('<th>' + gettext('Requests') + '</th>');
            elems.push('<th>' + gettext('Avg response time') + '</th>');
            elems.push('<th>' + gettext('Bytes out') + '</th>');
            elems.push('</tr></thead><tbody>');

            $.each(item.stats.workers, function (j, worker) {
                elems.push('<tr>');
                elems.push('<td>' + worker.id + '</td>');
                elems.push('<td>' + worker.status + '</td>');
                elems.push('<td>' + worker.rss + '</td>');
                elems.push('<td>' + worker.respawn_count + '</td>');
                elems.push('<td>' + worker.requests + '</td>');
                elems.push('<td>' + Math.round(worker.avg_rt / 1000) + ' ms</td>');
                elems.push('<td>' + worker.tx + '</td>');
                elems.push('</tr>');
            });
            elems.push('</tbody></table>');
            elems.push('</div>');
            elems.push('</div>');
        });
    }
    return elems;
}
