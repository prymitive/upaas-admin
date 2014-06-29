window.UPAAS = window.UPAAS || {};
window.UPAAS.utils = window.UPAAS.utils || {};


window.UPAAS.utils.bytes_to_human = function (size) {
    /*
    Credits go to:
    http://blog.jbstrickler.com/2011/02/bytes-to-a-human-readable-string/
    */
    var suffix = ["bytes", "KB", "MB", "GB", "TB", "PB"],
        tier = 0;

    while(size >= 1024) {
        size = size / 1024;
        tier++;
    }

    return Math.round(size * 10) / 10 + " " + suffix[tier];
}


window.UPAAS.utils.rgb_to_hex = function (rgb) {
    /*
    Credits go to:
    http://wowmotty.blogspot.com/2009/06/convert-jquery-rgb-output-to-hex-color.html
     */
    rgb = rgb.match(/^rgba?[\s+]?\([\s+]?(\d+)[\s+]?,[\s+]?(\d+)[\s+]?,[\s+]?(\d+)[\s+]?/i);
    return (rgb && rgb.length === 4) ? "#" +
        ("0" + parseInt(rgb[1],10).toString(16)).slice(-2) +
        ("0" + parseInt(rgb[2],10).toString(16)).slice(-2) +
        ("0" + parseInt(rgb[3],10).toString(16)).slice(-2) : '';
}


window.UPAAS.utils.update_badge = function(id, value) {
    if (value) {
        if ($(id).text() != value) {
            $(id).removeClass('upaas-badge-default');
        }
        $(id).text(value);

    } else {
        $(id).text('');
    }
}


window.UPAAS.utils.bind_backbone = function(what, callback_fn, exclude) {
    var events = ['add', 'remove', 'reset', 'change', 'destroy'];
    var excluded = exclude || [];
    jQuery.each(events, function(i, event) {
        if (jQuery.inArray(event, excluded) == -1) {
            what.bind(event, callback_fn);
        }
    });
}


window.UPAAS.utils.where_or_fetch = function(collection, options) {
    var ret;
    ret = collection.where(options);
    if (ret.length > 0) {
        return ret;
    } else {
        collection.fetch({async: false});
        return collection.where(options);
    }
}


window.UPAAS.utils.where_or_get_first = function(collection, options) {
    var ret;
    ret = collection.where(options);
    if (ret.length > 0) {
        return ret[0];
    } else {
        var model = new collection.model(options);
        model.fetch({async: false});
        return model;
    }
}


window.UPAAS.utils.update_progress = function(selector, progress) {
    $(selector).attr('aria-valuenow', progress).attr('style', 'width: ' + progress + '%;');
}


window.UPAAS.utils.set_progressbar_finished = function(outer_selector, bar_selector, is_successful) {
    $(outer_selector).removeClass('active progress-striped');
    if (is_successful) {
        $(bar_selector).addClass('progress-bar-success');
    } else {
        $(bar_selector).addClass('progress-bar-danger');
    }
}
