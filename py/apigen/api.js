function showhideel(el) {
    /* show or hide the element
    
        sets the value of el.style.display to 'none' or 'block' depending
        on the current value
    */
    if (el.style.display == 'none') {
        el.style.display = 'block';
    } else {
        el.style.display = 'none';
    };
};

function getnextsibling(el) {
    /* return next non-text sibling (or null) */
    var node = el.nextSibling;
    while (node && node.nodeType != 1) {
        node = node.nextSibling;
    };
    return node;
};

