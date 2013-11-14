/*jslint undef: true */
/*global $, document, ace, $SCRIPT_ROOT */
/* vim: set et sts=4: */


$(document).ready(function () {
    "use strict";

    var editor, CurrentMode, file, workdir, edit, send,
        modelist,
        config;

    function selectFile(file) {
        edit = false;
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/getFileContent',
            data: "file=" + file,
            success: function (data) {
                if (data.code === 1) {
                    editor.getSession().setValue(data.result);
                    edit = true;
                } else {
                    $("#error").Popup("Can not load your file, please make sure that you have selected a Software Release",
                                      {type: 'alert', duration: 5000});
                }
            }
        });
        return;
    }

    function getmd5sum() {
        if (send) {
            return;
        }
        send = true;
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/getmd5sum',
            data: {file: file},
            success: function (data) {
                if (data.code === 1) {
                    $("#md5sum").empty();
                    $("#md5sum").append('md5sum : <span>' + data.result + '</span>');
                } else {
                    $("#error").Popup(data.result, {type: 'error', duration: 5000});
                }
                send = false;
            }
        });
    }

    function setDevelop(developList) {
        if (developList === null || developList.length <= 0) {
            return;
        }
        editor.navigateFileStart();
        editor.find('buildout', {caseSensitive: true, wholeWord: true});
        if (editor.getSelectionRange().isEmpty()) {
            $("#error").Popup("Can not found part [buildout]! Please make sure that you have a cfg file",
                              {type: 'alert', duration: 3000});
            return;
        }
        //else {
        //    //editor.find("",{caseSensitive: true,wholeWord: true,regExp: true});
        //    //if (!editor.getSelectionRange().isEmpty()) {
        //            //alert("found");
        //    //}
        //    //else{alert("no found");
        //    //}
        //}
        editor.navigateLineEnd();
        $.post($SCRIPT_ROOT + "/getPath", {file: developList.join("#")}, function (data) {
            if (data.code === 1) {
                var i,
                    result = data.result.split('#');
                editor.insert("\ndevelop =\n\t" + result[0] + "\n");
                for (i = 1; i < result.length; i += 1) {
                    editor.insert("\t" + result[i] + "\n");
                }
            }
        })
            .error(function () {  })
            .complete(function () {});
        editor.insert("\n");
    }

    file = $("input#profile").val();
    workdir = $("input#workdir").val();
    edit = false;
    send = false;

    editor = ace.edit("editor");
    modelist = require("ace/ext/modelist");
    config = require("ace/config");

    editor.getSession().setMode("ace/mode/text");
    editor.getSession().setTabSize(2);
    editor.getSession().setUseSoftTabs(true);
    editor.renderer.setHScrollBarAlwaysVisible(false);
    var mode = modelist.getModeForPath(file);
    editor.getSession().modeName = mode.name;
    editor.getSession().setMode(mode.mode);

    selectFile(file);

    $("#save").click(function () {
        if (!edit) {
            $("#error").Popup("Can not load your file, please make sure that you have selected a Software Release",
                              {type: 'alert', duration: 5000});
            return false;
        }
        if (send) {
            return;
        }
        send = true;
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/saveFileContent',
            data: {file: file, content: editor.getSession().getValue()},
            success: function (data) {
                if (data.code === 1) {
                    $("#error").Popup("File Saved!", {type: 'confirm', duration: 2000});
                } else {
                    $("#error").Popup(data.result, {type: 'error', duration: 5000});
                }
                send = false;
            }
        });
        return false;
    });

    $("#editOption").Tooltip();

    $("#getmd5").click(function () {
        getmd5sum();
        return false;
    });

    $("#adddevelop").click(function () {
        var developList = [],
            i = 0;
        $("#plist li").each(function (index) {
            var elt = $(this).find("input:checkbox");
            if (elt.is(":checked")) {
                developList[i] = workdir + "/" + elt.val();
                i += 1;
                elt.attr("checked", false);
            }
        });
        if (developList.length > 0) {
            setDevelop(developList);
        }
        return false;
    });

});
