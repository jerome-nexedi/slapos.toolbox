/*jslint undef: true */
/*global $, window, $SCRIPT_ROOT */
/* vim: set et sts=4: */

/*Common javascript function*/
String.prototype.toHtmlChar = function () {
    "use strict";
    var c = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#039;',
        '#': '&#035;'
    };
    return this.replace(/[<&>'"#]/g, function (s) { return c[s]; });
};
String.prototype.trim = function () {
    "use strict";
    return this.replace(/^\s*/, "").replace(/\s*$/, "");
};

/****************************************/
function setInput($elt) {
    "use strict";
    if (!$elt) {
        $elt = $('input[type="text"], input[type="password"]');
    }
    $elt.addClass("idleField");
    $elt.focus(function () {
        $(this).removeClass("idleField").addClass("focusField");
        if (this.value === this.defaultValue) {
            this.value = '';
        }
        if (this.value !== this.defaultValue) {
            this.select();
        }
    });
    $elt.blur(function () {
        $(this).removeClass("focusField").addClass("idleField");
        if ($.trim(this.value) === '') {
            this.value = (this.defaultValue || '');
        }
    });
}

/*******************Bind remove all button*******************/
function bindRemove() {
    "use strict";
    $("a#removeSr").click(function () {
        if (!window.confirm("Do you really want to remove all software release?")) {
            return false;
        }
        window.location.href = $SCRIPT_ROOT + '/removeSoftware';
    });
    $("a#removeIst").click(function () {
        if (!window.confirm("Do you really want to remove all computer partition?")) {
            return false;
        }
        window.location.href = $SCRIPT_ROOT + '/removeInstance';
    });
}

/**************************/
(function ($, document, window) {
    "use strict";
    $.extend($.fn, {
        slideBox: function (state) {
            if (!state) {
                state = "hide";
            }
            var header = $("#" + $(this).attr('id') + ">h2"),
                box = $("#" + $(this).attr('id') + ">div");
            header.addClass(state);
            if (state === "hide") {
                box.css('display', 'none');
            }
            header.click(function () {
                var state = box.css("display");
                if (state === "none") {
                    box.slideDown("normal");
                    header.removeClass("hide");
                    header.addClass("show");
                } else {
                    box.slideUp("normal");
                    header.removeClass("show");
                    header.addClass("hide");
                }
            });
        }
    });
}(jQuery, document, this));

