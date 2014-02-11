/*jslint undef: true */
/*global $, document, $SCRIPT_ROOT, ace, window */
/*global path: true */
/* vim: set et sts=4: */

$(document).ready(function () {
  "use strict";

    var viewer,
        editor,
        modelist,
        config,
        softwareDisplay = true,
        projectDir = $("input#project").val(),
        workdir = $("input#workdir").val(),
        currentProject = "workspace/" + projectDir.replace(workdir, "").split('/')[1],
        send = false,
        edit = false,
        ajaxResult = false,
        clipboardNode = null,
        pasteMode = null,
        selection = "",
        edit_status = "",
        current_file = null,
        favourite_list = new Array(),
        beforeunload_warning_set = false,
        base_path = function () {
            return softwareDisplay ? currentProject : 'runner_workdir/';
        };

    function openFile(file) {
        if (send) {
            return;
        }
        send = true;
        edit = false;
        if (file.substr(-1) !== "/") {
          var info = $("#edit_info").html();
          $("#edit_info").empty();
          $("#edit_info").append("LOADING FILE... <img src='"+$SCRIPT_ROOT+"/static/images/loading.gif' />");
          $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/getFileContent',
            data: {file: file},
            success: function (data) {
                var name, start, path = file;
                if (data.code === 1) {
                    $("#edit_info").empty();
                    name = file.split('/');
                    if (file.length > 75) {
                        //substring title.
                        start = file.length - 75;
                        path = "..." + file.substring(file.indexOf("/", (start + 1)));
                    }
                    $("#edit_info").append(" " + path);
                    editor.getSession().setValue(data.result);
                    var mode = modelist.getModeForPath(file);
                    editor.getSession().modeName = mode.name;
                    editor.getSession().setMode(mode.mode);
                    edit = true;
                    current_file = file;
                    $("span#edit_status").html("");
                    edit_status = "";
                    setCookie("EDIT_CURRENT_FILE", file);
                } else {
                    $("#error").Popup(data.result, {type: 'error', duration: 5000});
                    $("#edit_info").html(info);
                }
                send = false;
            }
          });
        }
        return;
    }

    function switchContent() {
        if (!softwareDisplay) {
            $("span.swith_btn").empty();
            $("span.swith_btn").append("Working dir");
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
        var filename;

        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/getmd5sum',
            data: {file: path},
            success: function (data) {
                if (data.code === 1) {
                    filename = path.replace(/^.*(\\|\/|\:)/, '');
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
        //Close popup
        $("#option").click();
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
            var cb = clipboardNode.toDict(true);
            if( node.isDescendantOf(clipboardNode) ) {
              $("#error").Popup("ERROR: Cannot move a node to it's sub node.", {type: 'error', duration: 5000});
              return;
            }
            request = fileBrowserOp(dataForSend);
            request.always(function() {
              if (ajaxResult){
                if (node.isExpanded()){
                  node.addChildren(cb);
                  node.render();
                }
                else{
                  node.lazyLoad()
                }
                clipboardNode.remove();
              }
            });
          } else {
            if (node.key === clipboardNode.getParent().key){
              dataForSend = {opt: 14, filename: clipboardNode.title,
                              dir: node.data.path,
                              newfilename: clipboardNode.title
                            };
            }
            request = fileBrowserOp(dataForSend);
            request.always(function() {
              if (ajaxResult){
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
            });
          }
          clipboardNode = pasteMode = null;
          break;
      }
    };

    function manageMenu (srcElement, menu){
      /*if (!srcElement.hasClass('fancytree-node')){
        menu.disableContextMenuItems("#edit,#editfull,#view,#md5sum,#refresh,#paste");
        return;
      }*/
      var node = $.ui.fancytree.getNode(srcElement);
      node.setFocus();
      node.setActive();
      if (srcElement.hasClass('fancytree-folder')){
        menu.disableContextMenuItems("#edit,#editfull,#view,#md5sum,#favorite");
      }
      else{
        menu.disableContextMenuItems("#nfile,#nfolder,#refresh,#paste");
      }
      return true;
    }

    function fileBrowserOp(data){

      ajaxResult = false;
      var jqxhr = $.ajax({
          type: "POST",
          url: $SCRIPT_ROOT + '/fileBrowser',
          data: data})
        .done(function(data) {
          if (data.indexOf("{result: '1'}") === -1) {
            var msg = (data === "{result: '0'}") ? "ERROR: Please check your file or folder location!" : data;
            $("#error").Popup("Error: " + msg, {type: 'error', duration: 5000});
          } else {
            $("#error").Popup("Operation complete!", {type: 'confirm', duration: 5000});
            ajaxResult = true;
          }
        })
        .fail(function(jqXHR, exception) {
          if (jqXHR.status == 404) {
              $("#error").Popup("Requested page not found. [404]", {type: 'error'});
          } else if (jqXHR.status == 500) {
              $("#error").Popup("Internal Error. Cannot respond to your request, please check your parameters", {type: 'error'});
          } else {
              $("#error").Popup("An Error occured: \n" + jqXHR.responseText, {type: 'error'});
          }
        })
        .always(function() {
          //return result;
        });
        return jqxhr;
    }

    // --- Contextmenu helper --------------------------------------------------
    function bindContextMenu(span) {
      // Add context menu to this node:
      var item = $(span).contextMenu({menu: "fileTreeMenu"}, function(action, el, pos) {
        // The event was bound to the <span> tag, but the node object
        // is stored in the parent <li> tag
        var node = $.ui.fancytree.getNode(el);
        var directory = encodeURIComponent(node.data.path.substring(0, node.data.path.lastIndexOf('/')) +"/");
        var request;
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
        			$("#inline_content").append('<div class="main_content"><pre id="editorViewer"></pre></div>');
              viewer = ace.edit("editorViewer");
              viewer.setTheme("ace/theme/crimson_editor");

              var mode = modelist.getModeForPath(node.data.path);
              viewer.getSession().modeName = mode.name;
              viewer.getSession().setMode(mode.mode);
              viewer.getSession().setTabSize(2);
              viewer.getSession().setUseSoftTabs(true);
              viewer.renderer.setHScrollBarAlwaysVisible(false);
              viewer.setReadOnly(true);
        			$("#inlineViewer").colorbox({inline:true, width: "847px", onComplete:function(){
        				viewer.getSession().setValue(data);
        			}, title: "Content of file: " + node.title});
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
          request = fileBrowserOp(dataForSend)
          request.always(function() {
            if (ajaxResult){
              node.lazyLoad(true);
              node.toggleExpanded();
            }
          });
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
          request = fileBrowserOp(dataForSend)
          request.always(function() {
            if (ajaxResult){
              node.lazyLoad(true);
              node.toggleExpanded();
            }
          });
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
          request = fileBrowserOp(dataForSend)
          request.always(function() {
            if (ajaxResult){
              node.remove();
            }
          });
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
          request = fileBrowserOp(dataForSend);
          request.always(function() {
            if (ajaxResult){
              var copy = node.toDict(true, function(dict){
                dict.title = newName;
              });
              node.applyPatch(copy);
            }
          });

          break;
        case "favorite":
          addToFavourite(node.data.path);
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
        dblclick: function(event, data) {
          if (!data.node.isFolder()){
            openFile(data.node.data.path);
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
          bindContextMenu(data.node.span);
        }
      });
    }

    function openOnFavourite($elt){
      var index = parseInt($elt.attr('rel')),
          file = favourite_list[index];
      openFile(file);
      $("#filelist").click();
    }

    function removeFavourite($elt){
      var index = parseInt($elt.attr('rel'));
      favourite_list.splice(index, 1);
      $elt.parent().remove();
      $('#tooltip-filelist ul li[rel="'+index+'"]').remove();
      if (favourite_list.length === 0){
        $("#tooltip-filelist ul").append("<li>Your favourites files list is <br/>empty for the moment!</li>");
      }
      else{
        var i = 0;
        $("#tooltip-filelist ul li").each(function(){
          $(this).attr('rel', i);
          //Change attribute rel of all children!!
          $(this).children().each(function(){
            $(this).attr('rel', i);
          });
          i++;
        });
      }
      deleteCookie("FAV_FILE_LIST");
      setCookie("FAV_FILE_LIST", favourite_list.join('#'));
    }

    function initEditor(){
      var tmp, filename;
      current_file = getCookie("EDIT_CURRENT_FILE");
      if (current_file) {
          openFile(current_file);
      }
      tmp = getCookie("FAV_FILE_LIST");
      if(tmp){
        favourite_list = tmp.split('#');
        if (favourite_list.length !== 0){
          $("#tooltip-filelist ul").empty();
        }
        for (var i=0; i<favourite_list.length; i++){
          filename = favourite_list[i].replace(/^.*(\\|\/|\:)/, '');
          $("#tooltip-filelist ul").append('<li rel="'+i+
                    '"><span class="bt_close" title="Remove this element!" rel="'+i+
                    '">×</span><a href="#" rel="'+i+'" title="' + favourite_list[i]
                    + '">'+ filename +'</a></li>');
        }
      }
      //Click on favorite file in list to open it!
      $("#tooltip-filelist ul li a").click(function(){
        openOnFavourite($(this));
        return false;
      });
      //Remove favorite file in list
      $("#tooltip-filelist ul li span").click(function(){
        removeFavourite($(this));
        return false;
      });
    }

    function addToFavourite(filepath){
      if (! filepath ) {
        return;
      }
      var i = favourite_list.length,
          filename = filepath.replace(/^.*(\\|\/|\:)/, '');
      if (i === 0){
        $("#tooltip-filelist ul").empty();
      }
      if (favourite_list.indexOf(filepath) !== -1){
        $("#error").Popup("<b>Duplicate item!</b><br/>This files already exist in your favourite list", {type: 'alert', duration: 5000});
      }
      else{
        favourite_list.push(filepath);
        $("#tooltip-filelist ul").append('<li rel="'+i+
                    '"><span class="bt_close" title="Remove this element!" rel="'+i+
                    '">×</span><a href="#" rel="'+i+'" title="' + filepath
                    + '">'+ filename +'</a></li>');
        deleteCookie("FAV_FILE_LIST");
        setCookie("FAV_FILE_LIST", favourite_list.join('#'));
        $("#tooltip-filelist ul li a[rel='"+i+"']").bind('click', function() {
          openOnFavourite($(this));
          return false;
        });
        $("#tooltip-filelist ul li span[rel='"+i+"']").click(function(){
          removeFavourite($(this));
          return false;
        });
        $("#error").Popup("<b>Item added!</b><br/>"+filename+" has been added to your favourite list.", {type: 'confirm', duration: 3000});
      }
    }



    editor = ace.edit("editor");
    modelist = require("ace/ext/modelist");
    ace.require("ace/ext/language_tools");
    config = require("ace/config");

    editor.setOptions({ enableBasicAutocompletion: true, enableSnippets: true });

    editor.setTheme("ace/theme/crimson_editor");
    editor.getSession().setMode("ace/mode/text");
    editor.getSession().setTabSize(2);
    editor.getSession().setUseSoftTabs(true);
    editor.renderer.setHScrollBarAlwaysVisible(false);

    initTree('#fileTree', currentProject, 'pfolder');
    initTree('#fileTreeFull', 'runner_workdir');
    //bindContextMenu('#fileTree');
    $("#info").append("Current work tree: " + base_path());

    initEditor();

    $("#option").Tooltip();
    $("#filelist").Tooltip();

    editor.getSession().on('change', function(){
        $("#editor").val(editor.getSession().getValue());
        if (!beforeunload_warning_set) {
            window.onbeforeunload = function() { return "You have unsaved changes"; };
            beforeunload_warning_set = true;
        }
    });

    $('input[value="Save Changes"]').click(function() {
        window.onbeforeunload = function() { return; };
    });

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
                file: current_file,
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
        getmd5sum(current_file);
        $("#option").click();
        return false;
    });

    $("#clearselect").click(function () {
        edit = false;
        $("#info").empty();
        $("#info").append("Current work tree: " + base_path());
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
    $("a#addflist").click(function(){
      addToFavourite(current_file);
      $("#option").click();
      return false;
    });

    $("a#find").click(function(){
      config.loadModule("ace/ext/searchbox", function(e) {e.Search(editor)});
      $("#option").click();
      return false;
    });

    $("a#replace").click(function(){
      config.loadModule("ace/ext/searchbox", function(e) {e.Search(editor, true)});
      $("#option").click();
      return false;
    });


});
