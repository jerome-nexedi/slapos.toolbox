/*jslint undef: true */
/*global $, document, window, $SCRIPT_ROOT, ace */
/* vim: set et sts=4: */


$(document).ready(function () {
    "use strict";

    $('#fileNavigator').gsFileManager({script: $SCRIPT_ROOT + "/fileBrowser", root: 'workspace/'});
});
