/*jslint undef: true */
/*global $, document, window, $SCRIPT_ROOT */
/* vim: set et sts=4: */

$(document).ready(function () {
    "use strict";

    var method = $("input#method").val(),
        workdir = $("input#workdir").val();

    /*
     * Check if path is a .cfg (buildout profile) file.
     **/
    function isBuildoutFile(path) {
        var suffix = '.cfg',
            isBuildoutFile = path.indexOf(suffix, path.length - suffix.length) !== -1;
        $("#check").fadeIn('normal');
        if (isBuildoutFile) {
            $("input#path").val(path);
        } else {
            $("input#path").val('');
            $("#check").hide();
        }
        return "";
    }

    function selectFile(file) {
        $("#info").empty();
        $("input#subfolder").val(file);
        if (method === "open") {
            $("#info").append("Selection: " + file);
            isBuildoutFile(file);
        } else {
            if ($("input#software").val() !== "" && $("input#software").val().match(/^[\w\d._\-]+$/)) {
                $("#info").append("New Software in: " + file + $("input#software").val());
            } else {
                $("#info").append("Selection: " + file);
            }
        }
        return;
    }

    if (method !== "file") {
        $('#fileTree').fileTree({root: workdir, script: $SCRIPT_ROOT + '/readFolder', folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false, selectFolder: true }, function (file) {
            selectFile(file);
        });
    }
    $("input#subfolder").val("");
    $("#create").click(function () {
        if ($("input#software").val() === "" || !$("input#software").val().match(/^[\w\d._\-]+$/)) {
            $("#error").Popup("Invalid Software name", {type: 'alert', duration: 3000});
            return false;
        }
        if ($("input#subfolder").val() === "") {
            $("#error").Popup("Select the parent folder of your software!", {type: 'alert', duration: 3000});
            return false;
        }
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/createSoftware',
            data: "folder=" + $("input#subfolder").val() + $("input#software").val(),
            success: function (data) {
                if (data.code === 1) {
                    window.location.href = $SCRIPT_ROOT + '/editSoftwareProfile';
                } else {
                    $("#error").Popup(data.result, {type: 'error', duration: 5000});
                }
            }
        });
        return false;
    });

    $("#open").click(function () {
        $("#flash").fadeOut('normal');
        $("#flash").empty();
        $("#flash").fadeIn('normal');
        if ($("input#path").val() === "") {
            $("#error").Popup("Select a valid Software Release folder!", {type: 'alert', duration: 3000});
            return false;
        }
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/setCurrentProject',
            data: "path=" + $("input#path").val(),
            success: function (data) {
                if (data.code === 1) {
                    window.location.href = $SCRIPT_ROOT + '/editSoftwareProfile';
                } else {
                    $("#error").Popup(data.result, {type: 'error', duration: 5000});
                }
            }
        });
        return false;
    });
});
