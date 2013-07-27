/*jslint undef: true */
/*global document, escape, unescape */
/* vim: set et sts=4: */

/*Cookies Management*/
function getCookie(name) {
    "use strict";
    var i,
        x,
        y,
        result,
        ARRcookies = document.cookie.split(";");
    for (i = 0; i < ARRcookies.length; i += 1) {
        x = ARRcookies[i].substr(0, ARRcookies[i].indexOf("="));
        y = ARRcookies[i].substr(ARRcookies[i].indexOf("=") + 1);
        x = x.replace(/^\s+|\s+$/g, "");
        if (x === name) {
            result = unescape(y);
            if (result !== "" && result !== null) {
                return result;
            }
            return null;
        }
    }
    return null;
}

function deleteCookie(name, path, domain) {
    "use strict";
    if (getCookie(name)) {
        document.cookie = name + "=" +
            (path ? "; path=" + path : "/") +
            (domain ? "; domain=" + domain : "") +
            "; expires=Thu, 01-Jan-70 00:00:01 GMT";
    }
}

function setCookie(name, value, expires, path, domain, secure) {
    "use strict";
    if (getCookie(name) !== null) {
        deleteCookie(name);
    }
    if (!expires) {
        var today = new Date();
        expires = new Date(today.getTime() + 365 * 24 * 60 * 60 * 1000);
    }
    document.cookie = name + "=" + escape(value) +
        "; expires=" + expires.toGMTString() +
        ((path) ? "; path=" + path : "/") +
        ((domain) ? "; domain=" + domain : "") +
        ((secure) ? "; secure" : "");
}
/**************************/
