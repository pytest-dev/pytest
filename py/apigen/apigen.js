function loadloc() {
    /* load iframe content using # part of the url */
    var loc = document.location.toString();
    if (loc.indexOf('#') == -1) {
        return;
    };
    var chunks = loc.split('#');
    var anchor = chunks[chunks.length - 1];
    var iframe = document.getElementsByTagName('iframe')[0];
    iframe.src = anchor;
};
