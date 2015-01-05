/*jslint undef: true */
/*global $, document, $SCRIPT_ROOT, ace, window */
/*global path: true */
/* vim: set et sts=4: */

$(document).ready(function () {
  "use strict";

    var viewer,
        modelist,
        config,
        files,
        working_node = null,
        editorlist = [],
        editorIndex = 0,
        saveTimeOut = null,
        softwareDisplay = true,
        projectDir = $("input#project").val(),
        workdir = $("input#workdir").val(),
        currentProject = "workspace/" + projectDir.replace(workdir, "").split('/')[1],
        send = false,
        edit = false,
        ajaxResult = false,
        clipboardNode = null,
        pasteMode = null,
        favourite_list = [],
        editorWidth = $("#code").css("width"),
        beforeunload_warning_set = 0,
        base_path = function () {
            return softwareDisplay ? currentProject : 'workspace/';
        };
    
    var MAX_TABITITLE_WIDTH = 126;
    var TAB_EXTRA_WIDTH = 25;
    var MIN_TABITEM_WIDTH = 61; //The minimum size of tabItem
    var MAX_TAB_NUMBER = 10; //The maximum number of tab that could be opened


    function alertStatus (jqXHR) {
      if (jqXHR.status == 404) {
          $("#error").Popup("Requested page not found. [404]", {type: 'error'});
      } else if (jqXHR.status == 500) {
          $("#error").Popup("Internal Error. Cannot respond to your request, please check your parameters", {type: 'error'});
      } else {
          $("#error").Popup("An Error occured: \n" + jqXHR.responseText, {type: 'error'});
      }
    }

    // Open File in a new Tab and return status
    function openFile(file) {
      var status = false;
      if (file.substr(-1) === "/" || send) {
        return false;
      }
      var hash = addTab (file, true);
      if (hash === "") {
        return false;
      }
      var activeSpan = getActiveTabTitleSelector(hash);
      $(activeSpan).html('Loading file...');
      $.ajax({
          type: "POST",
          url: $SCRIPT_ROOT + '/getFileContent',
          data: {file: file}
        })
        .done(function(data) {
          var editor = editorlist[hash].editor;
          if (data.code === 1) {
            editor.session.setValue(data.result);
            $(activeSpan).html(file.replace(/^.*(\\|\/|\:)/, ''));
            var mode = modelist.getModeForPath(file);
            editor.session.modeName = mode.name;
            editor.session.setMode(mode.mode);
            ace.require("ace/ext/language_tools");
            editor.setOptions({ enableBasicAutocompletion: true });
            editor.session.getUndoManager().reset();
            editorlist[hash].busy = false;
            status = true;
          } else {
            $("#error").Popup("Unable to open file: " + file + "<br/>" + data.result,
                              {type: 'error', duration: 5000});
            //Close current tab
            $("#tabControl div[rel='" + hash + "']  span.bt_close").click();
          }
        })
        .fail(function(jqXHR, exception) {
          alertStatus (jqXHR);
          //Close current tab
          $("#tabControl div[rel='" + hash + "']  span.bt_close").click();
        })
        .always(function() {
          // always
        });
      return status;
    }

    function runSaveFile(hash){
      if ( !editorlist[hash].changed ) {
        return;
      }
      if (editorlist[hash].busy) {
          return;
      }
      editorlist[hash].busy = true;
      $.ajax({
          type: "POST",
          url: $SCRIPT_ROOT + '/saveFileContent',
          data: {
              file: editorlist[hash].path,
              content: editorlist[hash].editor.session.getValue()
          }})
        .done(function(data) {
          if (data.code === 1) {
            var currentSpan = getActiveTabTitleSelector(hash),
              title = $(currentSpan).html();
            editorlist[hash].changed = false;
            $(currentSpan).html(title.substr(1));
            if(--beforeunload_warning_set === 0) {
              window.onbeforeunload = function() { return; };
            }
          } else {
              $("#error").Popup(data.result, {type: 'error', duration: 5000});
          }
        })
        .fail(function(jqXHR, exception) {
          alertStatus (jqXHR);
        })
        .always(function() {
          editorlist[hash].busy = false;
        });
    }

    /******* MANAGE TAB CONTROL *****/

    function getTabList () {
      var list = [];
      for (var x in editorlist) {
        list.push(editorlist[x].path);
      }
      return list;
    }

    function saveTabList () {
      if (saveTimeOut) clearTimeout(saveTimeOut);
      saveTimeOut = setTimeout(function () {
          setCookie("OPENED_TAB_LIST", getTabList().join("#"));
        }, 2000);
    }

    function getMaxTab () {
      var tabBarWidth = $(".box_header").width() - $(".box_header ul").width();
      var max = (tabBarWidth - (tabBarWidth % MIN_TABITEM_WIDTH))/MIN_TABITEM_WIDTH;
      return ( max > MAX_TAB_NUMBER ) ? MAX_TAB_NUMBER : max;
    }

    //Reduce TabItem title to have the minimal or maximal width
    function resizeTabItems (addTab) {
      var numberTab = $("#tabControl div.item").length;
      var width = 0;
      if (addTab) {
        numberTab++;
      }
      if (numberTab === 0) {
        return width;
      }
      var tabBarWidth = $(".box_header").width() - $(".box_header ul").width();
      var rest = tabBarWidth % numberTab;
      var averageWidth = ( tabBarWidth - rest )/numberTab;
      if (averageWidth > MIN_TABITEM_WIDTH) {
        averageWidth -= TAB_EXTRA_WIDTH;
        width = averageWidth + rest;
        if (averageWidth > MAX_TABITITLE_WIDTH) {
          averageWidth = MAX_TABITITLE_WIDTH;
          width = averageWidth;
        }
        $("#tabControl div.item span:nth-child(1)").each(function () {
          $(this).css('width', averageWidth);
        });
        if ( !addTab && (rest !== 0) ) {
          $("#tabControl div.item:last-child span:nth-child(1)").each(function () {
            $(this).css('width', width);
          });
        }
      }
      return width;
    }

    //Add new tabItem
    function addTab (path, selected) {
      var hash =  path.hashCode() + '';
      if (editorlist.hasOwnProperty(hash)) {
        //this file already exist in editor. Select file and exit!
        $("#tabControl div.item").each( function () {
          var rel = $(this).attr('rel');
          if ( rel && (rel === hash) ) {
            $(this).click();
            return "";
          }
        });
        return "";
      }
      var title = path.replace(/^.*(\\|\/|\:)/, '');
      var numberTab = $("#tabControl div.item").length;
      if ( numberTab >= getMaxTab() ) {
        $("#error").Popup("Sorry! We cannot add more item, please close unused tab",
            {type: 'info', duration: 5000});
        return "";
      }
      var width = resizeTabItems(true);
      var tab  = '<div class="item" rel="' + hash
                + '"><span style="width: '+ width +'px" '
                + 'title="' + path + '">' + title + '</span>'
                + '<span class="bt_close" title="Close this tab">×</span></div>';
      var editorhtml = '<pre class="editor" id="editor' + (++editorIndex)
                + '" rel="' + hash + '"></pre>';

      //Add Elements
      $("#tabControl").append(tab);
      $("#tabContent").append(editorhtml);
      addEditor(path, hash, 'editor'+editorIndex);

      /* Change selected tab*/
      $("#tabControl div.item:last").click(function () {
        var rel = $(this).attr('rel'), current;
        if ( $(this).hasClass('active') ) {
          editorlist[rel].editor.focus();
          return false;
        }
        current = $("#tabContent pre.active").attr('rel');
        if (current && current !== undefined) {
          editorlist[current].isOpened = false;
        }
        $("#tabControl div.active").removeClass('active');
        $("#tabContent pre.active").removeClass('active');
        $(this).addClass('active');
        $("#tabContent pre[rel='" + rel + "']").addClass('active');
        editorlist[rel].isOpened = true;
        editorlist[rel].editor.resize();
        editorlist[rel].editor.focus();
        return false;
      });

      /*Close Selected Tab*/
      $("#tabControl div.item:last span.bt_close").click(function () {
        var $tab = $(this).parent(), position = 0,
            active = $tab.hasClass('active');
        var rel = $tab.attr('rel');
        if (editorlist[ rel ].changed) {
          if (!window.confirm("You have unsaved changes. Your changes will be lost if you don't save them")){
            return false;
          }
          if(--beforeunload_warning_set === 0) {
            window.onbeforeunload = function() { return; };
          }
        }
        //Remove tab
        position = ($tab.index() === 0) ? 1 : $tab.index();
        editorlist[ rel ].editor.destroy();
        delete editorlist[ rel ];
        $tab.remove();
        $("#tabContent pre[rel='" + rel + "']").remove();
        if ( active && $("#tabControl div.item").length > 0 ) {
          $("#tabControl div.item:nth-child("+position+")").click();
        }
        resizeTabItems ();
        saveTabList ();
        return false;
      });
      if (selected) {
        $("#tabControl div.item:last").click();
      }

      return hash;
    }

    function addEditor (path, hash, id) {
      var editor = ace.edit(id);
      //Init Ace editor!!

      editor.setTheme("ace/theme/crimson_editor");
      editor.session.setMode("ace/mode/text");
      editor.session.setTabSize(2);
      editor.session.setUseSoftTabs(true);
      editor.renderer.setHScrollBarAlwaysVisible(false);

      editorlist[hash] = {editor: editor, changed: false, path: path,
                          isOpened: false, busy: true};
      editor.on('input', function (e) {
        var activeToken = getActiveToken(),
            activeSpan = getActiveTabTitleSelector();
        if (!editorlist[activeToken].busy && !editorlist[activeToken].changed) {
          if (!editorlist[activeToken].editor.session.getUndoManager().hasUndo()){
            return;
          }
          editorlist[activeToken].changed = true;
          $(activeSpan).html("*" + $(activeSpan).html());
          if(beforeunload_warning_set === 0) {
            window.onbeforeunload = function() { return "You have unsaved changes. Your changes will be lost if you don't save them"; };
          }
          beforeunload_warning_set++;
        }
      });
      editor.commands.addCommand({
        name: 'SaveText',
        bindKey: {win: 'Ctrl-S',  mac: 'Command-S'},
        exec: function(editor) {
          $("#save").click();
        },
        readOnly: false // false if this command should not apply in readOnly mode
      });
      editor.commands.addCommand({
        name: 'Fullscreen',
        bindKey: {win: 'Ctrl-E',  mac: 'Command-E'},
        exec: function(editor) {
            $("#fullscreen").click();
        }
      });
    }

    function getCurrentEditor () {
      var hash = $("#tabContent pre.active").attr('rel');
      if ( editorlist.hasOwnProperty(hash) ) {
        return editorlist[hash].editor;
      }
      else { return null }
    }

    function getActiveToken () {
      return $("#tabContent pre.active").attr('rel');
    }

    function getActiveTabTitleSelector (hash) {
      var rel = (hash) ? hash : $("#tabContent pre.active").attr('rel');
      if ( editorlist.hasOwnProperty(rel) ) {
        return "#tabControl div[rel='" + rel + "']  span:nth-child(1)";
      }
      else { return ""; }
    }


    /****** END ******/

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
                    if ( $("body").hasClass("fullScreen") ) {
                      $("#error").Popup("Md5sum for file [" + filename + "]:<br/>" 
                              + "<b>" + data.result + "</b>", {type: 'confirm'});
                    }
                    else {
                      $("#info").empty();
                      $("#info").html("Md5sum for file [" + filename + "]: " + data.result);
                    }
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
        var editor = getCurrentEditor();
        editor.navigateFileStart();
        editor.find('buildout', {caseSensitive: true, wholeWord: true});
        if (!getCurrentEditor().getSelectionRange().isEmpty()) {
            //editor.find("",{caseSensitive: true,wholeWord: true,regExp: true});
            //if (!editor.getSelectionRange().isEmpty()) {
                    //alert("found");
            //}
            //else{alert("no found");
            //}
        } else {
            $("#error").Popup("Can not found part [buildout]! Please make sure that you have a cfg file",
                {type: 'alert', duration: 3000});
            return;
        }
        editor.navigateLineEnd();
        $.post($SCRIPT_ROOT + "/getPath", {file: developList.join("#")}, function (data) {
            var result, i;
            if (data.code === 1) {
                result = data.result.split('#');
                editor.insert("\ndevelop =\n\t" + result[0] + "\n");
                for (i = 1; i < result.length; i += 1) {
                    getCurrentEditor().insert("\t" + result[i] + "\n");
                }
            }
        })
            .error(function () {})
            .complete(function () {});
        editor.insert("\n");
        //Close popup
        $("#option").click();
    }

    /***** FILE TREE MANAGEMENT ******/
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
          // Copy mode: prevent duplicate keys:
          var request, cb = clipboardNode.toDict(true, function(dict){
            delete dict.key; // Remove key, so a new one will be created
          });
          cb.data.path = node.data.path + '/' + clipboardNode.title;
          if( pasteMode == "cut" ) {
            // Cut mode: check for recursion and remove source
            dataForSend.opt = 7;
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
                  node.load(true);
                }
                clipboardNode.remove();
              }
              clipboardNode = pasteMode = null;
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
                if (dataForSend.opt === 14){
                  node.load(true);
                  expandAfterLoad (node, true);
                }
                else if (node.isExpanded()){
                  node.addChildren(cb);
                  node.render();
                }
              }
              clipboardNode = pasteMode = null;
            });
          }
          break;
      }
    }

    function manageMenu (srcElement, menu){
      /*if (!srcElement.hasClass('fancytree-node')){
        menu.disableContextMenuItems("#edit,#editfull,#view,#md5sum,#refresh,#paste");
        return;
      }*/
      var node = $.ui.fancytree.getNode(srcElement);
      node.setFocus();
      node.setActive();
      if (srcElement.hasClass('fancytree-folder')){
        menu.disableContextMenuItems("#edit,#view,#md5sum");
      }
      else{
        menu.disableContextMenuItems("#nfile,#nfolder,#refresh,#paste,#ufile");
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
          alertStatus (jqXHR);
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
        case "edit": openFile(node.data.path);
          saveTabList (); break;
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
              viewer.session.modeName = mode.name;
              viewer.session.setMode(mode.mode);
              viewer.session.setTabSize(2);
              viewer.session.setUseSoftTabs(true);
              viewer.renderer.setHScrollBarAlwaysVisible(false);
              viewer.setReadOnly(true);
              $("#inlineViewer").colorbox({inline:true, width: "847px", onComplete:function(){
                viewer.session.setValue(data);
              }, title: "Content of file: " + node.title});
              $("#inlineViewer").click();
            }
          });
          break;
        case "md5sum":
          getmd5sum(node.data.path);
          break;
        case "refresh":
          node.load(true);
          expandAfterLoad (node, true);
          break;
        case "nfolder":
          var newName = window.prompt('Please Enter the folder name: ');
          if (newName === null || newName.length < 1) {
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
              node.load(true);
              expandAfterLoad (node, true);
            }
          });
          break;
        case "nfile":
          var newName = window.prompt('Please Enter the file name: ');
          if (newName === null || newName.length < 1) {
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
              node.load(true);
              expandAfterLoad (node, true);
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
          if (newName === null) {
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
              if (node.getParent().isRoot()) {
                if ($('#fileTreeFull').css('display') === 'none'){
                  $('#fileTree').fancytree("getTree").reload();
                }
                else {
                  $('#fileTreeFull').fancytree("getTree").reload();
                }
              }
              else {
                node.getParent().load(true);
                expandAfterLoad (node, true);
              }
            }
          });

          break;
        case "favorite":
          var nodePath = node.data.path;
          if (node.isFolder()) {
            nodePath = (nodePath.substr(-1) === '/') ? nodePath : nodePath + '/';
          }
          addToFavourite(nodePath);
          break;
        case "ufile":
          $.colorbox.remove();
          $("#uploadForm input[name=dir]").val(node.data.path);
          $("#inlineUpload").colorbox({inline:true,
                width: "480px", height: "200px", onComplete:function(){
                //nothing
          }});
          $("#inlineUpload").click();
          working_node = node;
          break;
        default:
          return;
        }
      }, manageMenu);
    }

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
            saveTabList ();
          }
        },
        source: {
          url: $SCRIPT_ROOT + "/fileBrowser",
          data:{opt: 20, dir: path, key: key, listfiles: 'yes'},
          cache: false
        },
        lazyLoad: function(event, data) {
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
    
    function expandAfterLoad (node, toState) {
      /*Expand node after the call of load.
        toState if true of false*/
      setTimeout(function () {
        if (node.isLoaded()) {
          node.setExpanded(toState);
        }
        else {
          expandAfterLoad (node, toState);
        }
      },300);
    }
    
    function loadNodeAndExpand(tree, subNode, node, position, loading) {
      var i = position, nextNode = null;
      if (i >= subNode.length ) {
        if (node) {
          node.setActive(true);
          node.scrollIntoView();
        }
        return;
      }
      if (!loading) {
        var childList = (i === 1 ) ? tree.toDict() : node.getChildren();
        for (var j=0; j<childList.length; j++){
          if (childList[j].title === subNode[i]) {
            nextNode = (i === 1 ) ? tree.getNodeByKey(childList[j].key) : childList[j];
            break;
          }
        }
      }
      else {
        nextNode = node;
      }
      if (nextNode) {
        if (!loading) {
          if (!nextNode.isLoaded()) {
            nextNode.load(false);
          }
          position++;
        }
        setTimeout(function () {
          if (nextNode.isLoaded()) {
            nextNode.setExpanded(true);
          }
          loadNodeAndExpand(tree, subNode, nextNode, position, !nextNode.isLoaded());
        },300);
      }
      else {
        $("#error").Popup("ERROR: File or Folder not found. Please make sure that it exist!!", 
                                                {type: 'error', duration: 5000});
      }
    }

    /******* END ******/

    function openOnFavourite($elt){
      var index = parseInt($elt.attr('rel')),
          file = favourite_list[index];
      if ( file.substr(-1) === '/') {
        file = file.slice(0, -1);
        var subNode = file.split('/'), tree = null;
        if (softwareDisplay) {
          softwareDisplay = !softwareDisplay;
          switchContent();
        }
        tree = $('#fileTreeFull').fancytree("getTree");
        //XXX - hard values, get relative path form runner_workdir directory
        if (subNode[0] === 'workspace') {
          subNode.splice(0, 0, 'runner_workdir');
          subNode[1] = 'project';
        }
        loadNodeAndExpand(tree, subNode, null, 1, false);
      }
      else {
        openFile(file);
        saveTabList ();
      }
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
      /*GET TAB List and Open files in tab*/
      var strList = getCookie("OPENED_TAB_LIST"), tabList;
      if (strList) {
        tabList = strList.split("#");
        for (var i=0; i< tabList.length; i++) {
          openFile(tabList[i]);
        }
      }
      /*Load Favourite Files and Folders*/
      tmp = getCookie("FAV_FILE_LIST");
      if(tmp){
        favourite_list = tmp.split('#');
        if (favourite_list.length !== 0){
          $("#tooltip-filelist ul").empty();
        }
        for (var i=0; i<favourite_list.length; i++){
          filename = favourite_list[i].replace(/^.*(\\|\/|\:)/, '');
          if (filename === '' && favourite_list[i].substr(-1) === '/') {
            filename = '[DIR] ' + favourite_list[i].slice(0,
                                                -1).replace(/^.*(\\|\/|\:)/, '');
          }
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
      saveTabList ();
    }

    function addToFavourite(filepath){
      if (! filepath ) {
        return;
      }
      var i = favourite_list.length,
          filename = filepath.replace(/^.*(\\|\/|\:)/, '');
      if (filename === '' && filepath.substr(-1) === '/') {
        filename = '[DIR] ' + filepath.slice(0,-1).replace(/^.*(\\|\/|\:)/, '');
      }
      if (i === 0){
        $("#tooltip-filelist ul").empty();
      }
      if (favourite_list.indexOf(filepath) !== -1){
        $("#error").Popup("<b>Duplicate item!</b><br/>This Item (" + filename +
                          ") already exist in your favourite list",
                          {type: 'alert', duration: 5000});
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
    


    /************ INITIALIZE FUNTIONS CALLS  ************************/

    modelist = require("ace/ext/modelist");
    config = require("ace/config");
    initTree('#fileTree', currentProject, 'pfolder');
    initTree('#fileTreeFull', 'runner_workdir');
    //bindContextMenu('#fileTree');
    $("#info").append("Current work tree: " + base_path());

    initEditor();

    $("#option").Tooltip();
    $("#filelist").Tooltip();

    $("#save").click(function () {
      if ($("#tabControl div.item").length === 0) {
        return false;
      }
      var hash = getActiveToken();
      runSaveFile(hash);
      return false;
    });

    $( "#tabControl" ).resize(function() {
      resizeTabItems ();
    });

    $("#expand").click( function () {
      var leftWith = $('#fileTree').width() + 6;
      if ( $("#details_box").css("display") !== 'none' ) {
        $("#details_box").hide();
        $("#code").css("width", "100%");
        if ( $("body").hasClass("fullScreen") ) {
          $(".main_content").css('left', '0');
        }
      }
      else {
        if ( $("body").hasClass("fullScreen") ) {
          $(".main_content").css('left', leftWith + 'px');
        }
        $("#details_box").show();
        $("#code").css("width", editorWidth);
      }
      if ($("#tabControl div.item").length !== 0) {
        getCurrentEditor().resize();
      }
      $("#option").click();
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
      if ($("#tabControl div.item").length === 0) {
        return false;
      }
      getmd5sum(editorlist[getActiveToken()].path);
      $("#option").click();
      return false;
    });

    $("#adddevelop").click(function () {
      if ($("#tabControl div.item").length === 0) {
        return false;
      }
      var developList = [],
          i = 0;
      $("#plist li").each(function (index) {
          var elt = $(this).find("input:checkbox");
          if (elt.is(":checked")) {
              developList[i] = "workspace" + "/" + elt.val();
              i += 1;
              elt.attr("checked", false);
          }
      });
      if (developList.length > 0) {
          setDevelop(developList);
      }
      return false;
    });
    $("a#addflist").click(function () {
      if ($("#tabControl div.item").length === 0) {
        return false;
      }
      addToFavourite(editorlist[getActiveToken()].path);
      $("#option").click();
      return false;
    });

    $("a#find").click(function () {
      if ($("#tabControl div.item").length === 0) {
        return false;
      }
      config.loadModule("ace/ext/searchbox", function(e) {
        e.Search(getCurrentEditor());
      });
      $("#option").click();
      return false;
    });

    $("a#replace").click(function () {
      if ($("#tabControl div.item").length === 0) {
        return false;
      }
      config.loadModule("ace/ext/searchbox", function(e) {
        e.Search(getCurrentEditor(), true);
      });
      $("#option").click();
      return false;
    });

    $("#fullscreen").click(function(){
      var hash = getActiveToken();
      $("#fullscreen span").toggleClass("e_expanded");
      $("body").toggleClass("fullScreen");
      $("#software_folder").toggleClass("fullScreen");
      $(".main_content").toggleClass("fullScreen-editor");
      $('#fileTree').toggleClass("fullScreen-tree");
      $('#fileTreeFull').toggleClass("fullScreen-tree");
      $(".main_content").css('left', '');
      if ( $("#details_box").css("display") === 'none' ) {
        $(".main_content").css('left', '0');
      }
      if ($("#tabControl div.item").length === 0) {
        return false;
      }
      resizeTabItems ();
      editorlist[hash].editor.resize();
      editorlist[hash].editor.focus();
      return false;
    });

    $('#choosefiles').on('change', function (event) {
      files = event.target.files;
    });

    $("#submitUpload").click( function (){
      jQuery('#uploadForm').submit();
      $("#cboxClose").click();
      return false;
    });

    jQuery('#uploadForm').ajaxForm({
      beforeSubmit: function () {
        $("#error").Popup("We are uploading your file...", {type: 'info', duration: 3000});
      },
      success: function (data, statusText, xhr, $form) {
        if (data.indexOf("{result: '1'}") === -1) {
          var msg = (data === "{result: '0'}") ? "ERROR: Please check your file or folder location!" : data;
          $("#error").Popup("Error: " + msg, {type: 'error', duration: 5000});
        } else {
          $("#error").Popup("Your file has been uploaded!", {type: 'confirm', duration: 5000});
          working_node.load(true);
        }
      },
      error: function (xhr, ajaxOptions, thrownError) {
        alertStatus (xhr);
      },
      dataType: 'script'
    });


});
