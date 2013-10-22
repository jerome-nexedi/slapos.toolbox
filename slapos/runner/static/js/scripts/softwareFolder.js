/*jslint undef: true */
/*global $, document, $SCRIPT_ROOT, ace, window */
/*global path: true */
/* vim: set et sts=4: */

$(document).ready(function () {
    "use strict";

    var editor = ace.edit("editor"),
        viewer,
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
        clipboardNode = null,
        pasteMode = null,
        selection = "",
        edit_status = "",
        base_path = function () {
            return softwareDisplay ? currentProject : 'workspace/';
        };


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
                    var name, start, path = file;
                    if (data.code === 1) {
                        $("#edit_info").empty();
                        name = file.split('/');
                        if (file.length > 80) {
                            //substring title.
                            start = file.length - 80;
                            path = "..." + file.substring(file.indexOf("/", (start + 1)));
                        }
                        $("#edit_info").append(" " + path);
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
        $("#info").append("Current work tree: " + file);
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
        if (!softwareDisplay) {
            $("span.swith_btn").empty();
            $("span.swith_btn").append("Workspace");
            $('#fileTreeFull').show();
            $('#fileTree').hide();
        } else {
            $("span.swith_btn").empty();
            $("span.swith_btn").append("This project");
            $('#fileTree').show();
            $('#fileTreeFull').hide();
        }
        $("#info").empty();
        $("#info").append("Current work tree: " + base_path());
        selection = "";
        clipboardNode = null;
        pasteMode = null;
    }

    function getmd5sum(path) {
        if (send) {
            return;
        }
        send = true;
        var filepath = (path) ? path : $("input#subfolder").val(),
            filename;

        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/getmd5sum',
            data: {file: filepath},
            success: function (data) {
                if (data.code === 1) {
                    filename = filepath.replace(/^.*(\\|\/|\:)/, '')
                    $("#info").empty();
                    $("#info").html("Md5sum for file [" + filename + "]: " + data.result);
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

    // --- Implement Cut/Copy/Paste --------------------------------------------

    function copyPaste(action, node) {
      switch( action ) {
        case "cut":
        case "copy":
          clipboardNode = node;
          pasteMode = action;
          break;
        case "paste":
          if( !clipboardNode ) {
            $("#error").Popup("Clipoard is empty. Make a copy first!", {type: 'alert', duration: 5000});
            break;
          }
          var dataForSend = {
            opt: 5,
            files: clipboardNode.data.path,
            dir: node.data.path
          };
          if( pasteMode == "cut" ) {
            // Cut mode: check for recursion and remove source
            dataForSend.opt = 7;
            fileBrowserOp(dataForSend);
            var cb = clipboardNode.toDict(true);
            if( node.isDescendantOf(cb) ) {
              $("#error").Popup("Cannot move a node to it's sub node.", {type: 'error', duration: 5000});
              return;
            }
            if (node.isExpanded()){
              node.addChildren(cb);
              node.render();
            }
            clipboardNode.remove();
          } else {
            if (node.key === clipboardNode.getParent().key){
              dataForSend = {opt: 14, filename: clipboardNode.title,
                              dir: node.data.path,
                              newfilename: clipboardNode.title
                            };
            }
            fileBrowserOp(dataForSend);
            // Copy mode: prevent duplicate keys:
            var cb = clipboardNode.toDict(true, function(dict){
              delete dict.key; // Remove key, so a new one will be created
            });
            if (dataForSend.opt === 14){
              node.lazyLoad(true);
              node.toggleExpanded();
            }
            else if (node.isExpanded()){
              node.addChildren(cb);
              node.render();
            }
          }
          clipboardNode = pasteMode = null;
          break;
      }
    };

    function manageMenu (srcElement, menu){
      if (srcElement.hasClass('fancytree-folder')){
        menu.disableContextMenuItems("#edit,#editfull,#view,#md5sum");
      }
      else{
        menu.disableContextMenuItems("#nfile,#nfolder,#refresh,#paste");
      }
      return true;
    }

    function fileBrowserOp(data){
      $.ajax({
        type: "POST",
        url: $SCRIPT_ROOT + '/fileBrowser',
        data: data,
        success: function (data) {
          if (data.indexOf('1') === -1) {
            $("#error").Popup("Error: " + data, {type: 'error', duration: 5000});
          } else {
            $("#error").Popup("Operation complete!", {type: 'confirm', duration: 5000});
          }
        },
        error: function(jqXHR, exception) {
          if (jqXHR.status == 404) {
              $("#error").Popup("Requested page not found. [404]", {type: 'error'});
          } else if (jqXHR.status == 500) {
              $("#error").Popup("Internal Error. Cannot respond to your request, please check your parameters", {type: 'error'});
          } else {
              $("#error").Popup("An Error occured: \n" + jqXHR.responseText, {type: 'error'});
          }
        }
      });
    }

    // --- Contextmenu helper --------------------------------------------------
    function bindContextMenu(span, editable) {
      // Add context menu to this node:
      var item = $(span).contextMenu({menu: "myMenu"}, function(action, el, pos) {
        // The event was bound to the <span> tag, but the node object
        // is stored in the parent <li> tag
        var node = $.ui.fancytree.getNode(el);
        var directory = encodeURIComponent(node.data.path.substring(0, node.data.path.lastIndexOf('/')) +"/");
        switch( action ) {
        case "cut":
        case "copy":
        case "paste":
          copyPaste(action, node);
          break;
        case "edit": openFile(node.data.path); break;
        case "view":
          $.colorbox.remove();
          $.ajax({
                type: "POST",
                url: $SCRIPT_ROOT + '/fileBrowser',
                data: {opt: 9, filename: node.title, dir: directory},
                success: function (data) {
                  $("#inline_content").empty();
                  $("#inline_content").append('<h2 style="color: #4c6172; font: 18px \'Helvetica Neue\', Helvetica, Arial, sans-serif;">Content of file: ' +
                		node.title +'</h2>');
            			$("#inline_content").append('<br/><div class="main_content"><pre id="editorViewer"></pre></div>');
                  viewer = ace.edit("editorViewer");
                  viewer.setTheme("ace/theme/crimson_editor");

                  var CurentMode = require("ace/mode/text").Mode;
                  viewer.getSession().setMode(new CurentMode());
                  viewer.getSession().setTabSize(2);
                  viewer.getSession().setUseSoftTabs(true);
                  viewer.renderer.setHScrollBarAlwaysVisible(false);
                  viewer.setReadOnly(true);
            			$("#inlineViewer").colorbox({inline:true, width: "847px", onComplete:function(){
            				viewer.getSession().setValue(data);
            			}});
      			      $("#inlineViewer").click();
                }
            });
          break;
        case "editfull":
          var url = $SCRIPT_ROOT+"/editFile?profile="+encodeURIComponent(node.data.path)+"&filename="+encodeURIComponent(node.title);
          window.open(url, '_blank');
          window.focus();
          break;
        case "md5sum":
          getmd5sum(node.data.path);
          break;
        case "refresh":
          node.lazyLoad(true);
          node.toggleExpanded();
          break;
        case "nfolder":
          var newName = window.prompt('Please Enter the folder name: ');
          if (newName == null || newName.length < 1) {
              return;
          }
          var dataForSend = {
              opt: 3,
              filename: newName,
              dir: node.data.path
          };
          fileBrowserOp(dataForSend);
          node.lazyLoad(true);
          node.toggleExpanded();
          break;
        case "nfile":
          var newName = window.prompt('Please Enter the file name: ');
          if (newName == null || newName.length < 1) {
              return;
          }
          var dataForSend = {
              opt: 2,
              filename: newName,
              dir: node.data.path
          };
          fileBrowserOp(dataForSend);
          node.lazyLoad(true);
          node.toggleExpanded();
          break;
        case "delete":
          if(!window.confirm("Are you sure that you want to delete this item?")){
            return;
          }
          var dataForSend = {
              opt: 4,
              files: encodeURIComponent(node.title),
              dir: directory
          };
          fileBrowserOp(dataForSend);
          node.remove();
          break;
        case "rename":
          var newName = window.prompt('Please enter the new name: ', node.title);
          if (newName == null) {
              return;
          }
          dataForSend = {
              opt: 6,
              filename: node.data.path,
              dir: directory,
              newfilename: newName
          };
          fileBrowserOp(dataForSend);
          var copy = node.toDict(true, function(dict){
            dict.title = newName;
          });
          node.applyPatch(copy);
          break;
        default:
          return;
        }
      }, manageMenu);
    };

    // --- Init fancytree during startup ----------------------------------------
    function initTree(tree, path, key){
      if (!key){
        key = '0';
      }
      $(tree).fancytree({
        activate: function(event, data) {
          var node = data.node;
        },
        click: function(event, data) {
          // Close menu on click
          if( $(".contextMenu:visible").length > 0 ){
            $(".contextMenu").hide();
  //          return false;
          }
        },
        source: {
          url: $SCRIPT_ROOT + "/fileBrowser",
          data:{opt: 20, dir: path, key: key, listfiles: 'yes'},
          cache: false
        },
        lazyload: function(event, data) {
          var node = data.node;
          data.result = {
            url: $SCRIPT_ROOT + "/fileBrowser",
            data: {opt: 20, dir: node.data.path , key: node.key, listfiles: 'yes'}
          }
        },
        keydown: function(event, data) {
          var node = data.node;
          // Eat keyboard events, when a menu is open
          if( $(".contextMenu:visible").length > 0 )
            return false;

          switch( event.which ) {

          // Open context menu on [Space] key (simulate right click)
          case 32: // [Space]
            $(node.span).trigger("mousedown", {
              preventDefault: true,
              button: 2
              })
            .trigger("mouseup", {
              preventDefault: true,
              pageX: node.span.offsetLeft,
              pageY: node.span.offsetTop,
              button: 2
              });
            return false;

          // Handle Ctrl-C, -X and -V
          case 67:
            if( event.ctrlKey ) { // Ctrl-C
              copyPaste("copy", node);
              return false;
            }
            break;
          case 86:
            if( event.ctrlKey ) { // Ctrl-V
              copyPaste("paste", node);
              return false;
            }
            break;
          case 88:
            if( event.ctrlKey ) { // Ctrl-X
              copyPaste("cut", node);
              return false;
            }
            break;
          }
        },
        createNode: function(event, data){
          bindContextMenu(data.node.span, !data.node.isFolder());
        }
      });
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

    initTree('#fileTree', currentProject, 'pfolder');
    initTree('#fileTreeFull', 'workspace');
    $("#info").append("Current work tree: " + base_path());
    /*setDetailBox();*/

    editor.on("change", function (e) {
        if (edit_status === "" && edit) {
            $("span#edit_status").html("*");
        }
    });
    editor.commands.addCommand({
      name: 'myCommand',
      bindKey: {win: 'Ctrl-S',  mac: 'Command-S'},
      exec: function(editor) {
        $("#save").click();
      },
      readOnly: false // false if this command should not apply in readOnly mode
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
        $("#info").append("Current work tree: " + base_path());
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
