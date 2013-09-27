/*
Credits go to:
http://blog.jbstrickler.com/2011/02/bytes-to-a-human-readable-string/
 */

function bytes_to_human(size) {
    var suffix = ["bytes", "KB", "MB", "GB", "TB", "PB"],
        tier = 0;

    while(size >= 1024) {
        size = size / 1024;
        tier++;
    }

    return Math.round(size * 10) / 10 + " " + suffix[tier];
}
