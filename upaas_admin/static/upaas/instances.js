/*
:copyright: Copyright 2013 by Łukasz Mierzwa
:contact: l.mierzwa@gmail.com
*/


var UPAAS = {

    instances_data_from_uwsgi_stats: function (data) {
        var elems = new Array();
        if (data.stats.length > 0) {
            $.each(data.stats, function (i, item) {
                elems.push('<div class="panel panel-default">');
                elems.push('<div class="panel-heading">' + item.backend.name);
                elems.push(' (' + item.stats.version + ')');
                elems.push('</div>');
                elems.push('<div class="panel-body">');

                elems.push('<table class="table-bordered table-condensed table-hover upaas-instance-table"><thead><tr>');
                elems.push('<th>' + gettext('#') + '</th>');
                elems.push('<th>' + gettext('State') + '</th>');
                elems.push('<th>' + gettext('Memory') + '</th>');
                elems.push('<th>' + gettext('Restarts') + '</th>');
                elems.push('<th>' + gettext('Harakiri') + '</th>');
                elems.push('<th>' + gettext('Requests') + '</th>');
                elems.push('<th>' + gettext('Avg response time') + '</th>');
                elems.push('<th>' + gettext('Bytes out') + '</th>');
                elems.push('</tr></thead><tbody>');

                var total_workers = 0;
                var total_rss = 0;
                var total_harakiri = 0;
                var total_requests = 0;
                var total_avg_rt = 0;
                var total_avg_rt_summary = '';
                var total_tx = 0;

                $.each(item.stats.workers, function (j, worker) {
                    total_harakiri += worker.harakiri_count;
                    total_requests += worker.requests;
                    total_tx += worker.tx;
                    if (worker.status == 'cheap') return true;
                    total_workers += 1;
                    total_rss += worker.rss;
                    total_avg_rt += worker.avg_rt;

                    elems.push('<tr class="' + worker.status + '">');
                    elems.push('<td>' + worker.id + '</td>');
                    elems.push('<td>' + worker.status + '</td>');
                    elems.push('<td>' + bytes_to_human(worker.rss) + '</td>');
                    elems.push('<td>' + worker.respawn_count + '</td>');
                    elems.push('<td>' + worker.harakiri_count + '</td>');
                    elems.push('<td>' + worker.requests + '</td>');
                    elems.push('<td>' + Math.round(worker.avg_rt / 1000) + ' ms</td>');
                    elems.push('<td>' + bytes_to_human(worker.tx) + '</td>');
                    elems.push('</tr>');
                });

                if (total_workers == 0) {
                    elems.push('<tr><td class="text-center" colspan=8>' + gettext('All workers are cheaped') + '</td></tr>');

                } else {
                    total_avg_rt_summary = Math.round(total_avg_rt / total_workers / 1000) + ' ms';
                }


                elems.push('<tr class="summary">');
                elems.push('<td>' + total_workers + '</td>');
                elems.push('<td></td>');
                elems.push('<td>' + bytes_to_human(total_rss) + '</td>');
                elems.push('<td>' + total_harakiri + '</td>');
                elems.push('<td></td>');
                elems.push('<td>' + total_requests + '</td>');
                elems.push('<td>' + total_avg_rt_summary + '</td>');
                elems.push('<td>' + bytes_to_human(total_tx) + '</td>');
                elems.push('</tr>');

                elems.push('</tbody></table>');
                elems.push('</div>');
                elems.push('</div>');
            });
        }
        return elems;
    }

}
