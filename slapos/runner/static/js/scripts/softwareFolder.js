/*jslint undef: true */
/*global $, document, $SCRIPT_ROOT, ace */
/*global path: true */
/* vim: set et sts=4: */


$(document).ready(function () {
    "use strict";

    var editor = ace.edit("editor"),
        CurrentMode,
        script = "/readFolder",
        softwareDisplay = true,
        Mode,
        modes,
        projectDir = $("input#project").val(),
        workdir = $("input#workdir").val(),
        currentProject = workdir + "/" + projectDir.replace(workdir, "").split('/')[1],
        send = false,
        edit = false,
        selection = "",
        edit_status = "";

    var base_path = function() {
      return softwareDisplay ? projectDir : currentProject;
    }

    function setEditMode(file) {
        var i,
            CurrentMode = require("ace/mode/text").Mode;
        editor.getSession().setMode(new CurrentMode());
        for (i = 0; i < modes.length; i += 1) {
            if (modes[i].extRe.test(file)) {
                editor.getSession().setMode(modes[i].mode);
                break;
            }
        }
    }

    function openFile(file) {
        if (send) {
            return;
        }
        send = true;
        edit = false;
        if (file.substr(-1) !== "/") {
            $.ajax({
                type: "POST",
                url: $SCRIPT_ROOT + '/getFileContent',
                data: {file: file},
                success: function (data) {
                    var name, start;
                    if (data.code === 1) {
                        $("#edit_info").empty();
                        name = file.split('/');
                        if (file.length > 60) {
                            //substring title.
                            start = file.length - 60;
                            file = "..." + file.substring(file.indexOf("/", (start + 1)));
                        }
                        $("#edit_info").append(" " + file);
                        $("a#option").show();
                        editor.getSession().setValue(data.result);
                        setEditMode(name[name.length - 1]);
                        edit = true;
                        $("input#subfolder").val(file);
                        $("span#edit_status").html("");
                        edit_status = "";
                    } else {
                        $("#error").Popup(data.result, {type: 'error', duration: 5000});
                    }
                    send = false;
                }
            });
        } else {
            $("#edit_info").empty();
            $("#edit_info").append("No file in editor");
            $("a#option").hide();
            editor.getSession().setValue("");
        }
        return;
    }

    function selectFile(file) {
        $("#info").empty();
        $("#info").append("Selection: " + file);
        selection = file;
        return;
    }
    /*
    function setDetailBox() {
        var state = $("#details_box").css("display");
        if (state === "none") {
            $("#details_box").fadeIn("normal");
            $("#details_head").removeClass("hide");
            $("#details_head").addClass("show");
        } else {
            $("#details_box").fadeOut("normal");
            $("#details_head").removeClass("show");
            $("#details_head").addClass("hide");
        }
    } */

    function switchContent() {
        var root = projectDir;
        if (!softwareDisplay) {
            $("#switch").empty();
            $("#switch").append("Switch to Profile&nbsp;");
            root = currentProject;
        } else {
            $("#switch").empty();
            $("#switch").append("Switch to Project");
        }
        $('#fileTree').fileTree({ root: root, script: $SCRIPT_ROOT + script, folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false, selectFolder: true }, function (file) {
            selectFile(file);
        }, function (file) { openFile(file); });
        $("#info").empty();
        $("#info").append("Selection: " + base_path());
        selection = "";
    }

    function getmd5sum() {
        if (send) {
            return;
        }
        send = true;
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/getmd5sum',
            data: {file: $("input#subfolder").val()},
            success: function (data) {
                if (data.code === 1) {
                    $("#info").empty();
                    $("#info").html("Md5sum Current file: " + data.result);
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
        if (!editor.getSelectionRange().isEmpty()) {
            //editor.find("",{caseSensitive: true,wholeWord: true,regExp: true});
            //if (!editor.getSelectionRange().isEmpty()) {
                    //alert("found");
            //}
            //else{alert("no found");
            //}
        } else {
            $("#error").Popup("Can not found part [buildout]! Please make sure that you have a cfg file", {type: 'alert', duration: 3000});
            return;
        }
        editor.navigateLineEnd();
        $.post($SCRIPT_ROOT + "/getPath", {file: developList.join("#")}, function (data) {
            var result, i;
            if (data.code === 1) {
                result = data.result.split('#');
                editor.insert("\ndevelop =\n\t" + result[0] + "\n");
                for (i = 1; i < result.length; i += 1) {
                    editor.insert("\t" + result[i] + "\n");
                }
            }
        })
            .error(function () {})
            .complete(function () {});
        editor.insert("\n");
    }


    editor.setTheme("ace/theme/crimson_editor");

    CurrentMode = require("ace/mode/text").Mode;
    editor.getSession().setMode(new CurrentMode());
    editor.getSession().setTabSize(2);
    editor.getSession().setUseSoftTabs(true);
    editor.renderer.setHScrollBarAlwaysVisible(false);

    Mode = function (name, desc, Clazz, extensions) {
        this.name = name;
        this.desc = desc;
        this.clazz = Clazz;
        this.mode = new Clazz();
        this.mode.name = name;

        this.extRe = new RegExp("^.*\\.(" + extensions.join("|") + ")$");
    };
    modes = [
        new Mode("php", "PHP", require("ace/mode/php").Mode, ["php", "in", "inc"]),
        new Mode("python", "Python", require("ace/mode/python").Mode, ["py"]),
        new Mode("buildout", "Python Buildout config", require("ace/mode/buildout").Mode, ["cfg"])
    ];
    $('#fileTree').fileTree({ root: projectDir, script: $SCRIPT_ROOT + script, folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false, selectFolder: true }, function (file) {
        selectFile(file);
    }, function (file) { openFile(file); });
    $("#info").append("Selection: " + base_path());
    /*setDetailBox();*/

    editor.on("change", function (e) {
        if (edit_status === "" && edit) {
            $("span#edit_status").html("*");
        }
    });

    $("#add").click(function () {
        var path = base_path();
        if (send) {
            return false;
        }
        if ($("input#file").val() === "" || $("input#file").val() === "Name here...") {
            $("#error").Popup("Please select a directory or nothing for root directory and enter your file name", {type: 'alert', duration: 5000});
            return false;
        }
        if (selection !== "") {
            path = selection;
        }
        path = path + "/" + $("input#file").val();
        send = true;
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/createFile',
            data: "file=" + path + "&type=" + $("#type").val(),
            success: function (data) {
                if (data.code === 1) {
                    switchContent();
                    $("input#file").val("");
                    $("#flash").fadeOut('normal');
                    $("#flash").empty();
                    $("#info").empty();
                    $("#info").append("Selection: " + base_path());
                    selection = "";
                } else {
                    $("#error").Popup(data.result, {type: 'error', duration: 5000});
                }
                send = false;
            }
        });
        return false;
    });

    $("#save").click(function () {
        if (!edit) {
            $("#error").Popup("Please select the file to edit", {type: 'alert', duration: 3000});
            return false;
        }
        if (send) {
            return false;
        }
        send = true;
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/saveFileContent',
            data: {
                file: $("input#subfolder").val(),
                content: editor.getSession().getValue()
            },
            success: function (data) {
                if (data.code === 1) {
                    $("#error").Popup("File saved succefuly!", {type: 'confirm', duration: 3000});
                    $("span#edit_status").html("");
                } else {
                    $("#error").Popup(data.result, {type: 'error', duration: 5000});
                }
                send = false;
            }
        });
        return false;
    });

    /*$("#details_head").click(function () {
        setDetailBox();
    });*/

    $("#switch").click(function () {
        softwareDisplay = !softwareDisplay;
        switchContent();
        return false;
    });
    $("#getmd5").click(function () {
        getmd5sum();
        return false;
    });

    $("#clearselect").click(function () {
        edit = false;
        $("#info").empty();
        $("#info").append("Selection: " + base_path());
        $("input#subfolder").val("");
        $("#edit_info").empty();
        $("#edit_info").append("No file in editor");
        editor.getSession().setValue("");
        $("a#option").hide();
        selection = "";
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
