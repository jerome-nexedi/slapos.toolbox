/*jslint undef: true */
/*global $, document, window, getCookie, setCookie, setSpeed, $SCRIPT_ROOT */
/*global openedlogpage: true, running: false */
/* vim: set et sts=4: */

$(document).ready(function () {
    "use strict";

    function getQueryVariable(variable) {
      var query = window.location.search.substring(1);
      var vars = query.split("&");
      for (var i=0;i<vars.length;i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) {
          return pair[1];
        }
      }
    }

    // Current_log is not used for auto displaying mode, only for manual reload of log file!!!
    var current_log = (getQueryVariable("logfile") !== undefined)? getQueryVariable("logfile") : "instance.log",
        sending,
        state,
        selectedFile = "",
        logfilelist = "instance_root/.log_list";

    var getCurrentLogFile = function () {
      if ( $("#manual").is(":checked") ) {
        return "";
      }
      if (current_log === "software.log") {
        return "software";
      }
      else if (current_log === "instance.log") {
        return "instance";
      }
      else {
        return "";
      }
    };

    function setupBox() {
        var state = $("#logconfigbox").css("display");
        if (state === "none") {
            $("#logconfigbox").slideDown("normal");
            $("#logheader").removeClass("hide");
            $("#logheader").addClass("show");
        } else {
            $("#logconfigbox").slideUp("normal");
            $("#logheader").removeClass("show");
            $("#logheader").addClass("hide");
        }
    }

    function updatelogBox() {
        if (! running || $("#manual").is(":checked")) {
            $("#salpgridLog").hide();
            $("#manualLog").show();
            $("#slapstate").hide();
            $("#openloglist").show();
            loadLog(current_log);
            $("#salpgridLog").empty();
        } else {
            $("#salpgridLog").show();
            $("#manualLog").hide();
            $("#slapstate").show();
            $("#openloglist").hide();
        }
    }

    function loadLog(filepath, $elt) {
      if (sending){
        return;
      }
      sending = true;
      var info = $("#logheader").html();
      $("#logheader").html("LOADING FILE... <img src='"+$SCRIPT_ROOT+"/static/images/loading.gif' />");
      var jqxhr = $.ajax({
          type: "POST",
          url: $SCRIPT_ROOT + '/getFileLog',
          data: {filename: filepath, truncate: 1500}
          })
        .done(function(data) {
          if (data.code === 0) {
            $("#error").Popup(data.result, {type: 'alert', duration: 5000});
          } else {
            $("#manualLog").empty();
            $("#manualLog").html(data.result);
            $("#logheader").empty();
            info = "Log from file " + filepath;
            $("#manualLog")
                .scrollTop($("#manualLog")[0].scrollHeight - $("#manualLog").height());
            current_log = filepath;
            if ($elt) {
              $("#openloglist ul li").each(function () {
                if ($(this).hasClass("checked")){
                  $(this).removeClass("checked");
                  return;
                }
              });
              $elt.addClass('checked');
            }
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
          sending = false;
          if (! running || $("#manual").is(":checked")) {
              $("#logheader").html(info);
          } else {
              $("#logheader").html("Inspecting slapgrid log - Click for more options");
          }
        });
    }

    function init() {
      openedlogpage = getCurrentLogFile();
      state = getCookie("autoUpdate");
      if (state) {
        $("#" + state).attr('checked', true);
        //updatelogBox();
        if (state === "manual") {
            openedlogpage = "";
            setSpeed(0);
        } else {
            setSpeed((state === "live") ? 100 : 2500);
        }
      } else {
          $("#slow").attr('checked', true);
      }
      $("#inlineViewer").colorbox({inline:true, width: "600px",
                      title: "Please select your log file",
                      onComplete:function () {
                        selectedFile = "";
                      }
      });
      //Load Custom file list if exist!
      $.ajax({
          type: "POST",
          url: $SCRIPT_ROOT + '/getFileContent',
          data: {file: logfilelist}
          })
        .done(function(data) {
          if (data.code === 0) {
            // nothing
          } else {
            var list = data.result.split('#'), i, filename;
            for (i = 0; i < list.length; i += 1) {
              if ( list[i] === "" ) {
                continue;
              }
              filename = list[i].replace(/^.*(\\|\/|\:)/, '');
              $("#openloglist ul").append("<li rel='" + list[i] + "'>" +
                    "<span class='bt_close' title='Remove this element!'" +
                    "style='display:none'>×</span>" + filename + "</li>");
            }
          }
        })
        .fail(function(jqXHR, exception) {
          // nothing
        })
        .always(function() {
          $("#openloglist ul li").click(function () {
            var logfile = $(this).attr('rel');
            if (current_log === logfile){
              return false;
            }
            loadLog(logfile, $(this));
            return false;
          });
        });
    }

    function initTree(tree, path, key) {
      if (!key){
        key = '0';
      }
      $.ajax({
        type: "POST",
        url: $SCRIPT_ROOT + '/getPath',
        data: {file: "instance_root"}
        })
      .done(function(data) {
        if (data.code === 1) {
          $(tree).fancytree({
            activate: function(event, data) {
              var node = data.node;
            },
            click: function(event, data) {
              if (!data.node.isFolder()){
                selectedFile = data.node.data.path;
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
          });
        }
        else {
          logfilelist = "";
        }
      });
    }

    init();
    updatelogBox();
    initTree('#fileTree', "instance_root");

    $("#logheader").click(function () {
        setupBox();
    });

    $("#manual").change(function () {
      if ( $(this).is(':checked') ) {
        setCookie("autoUpdate", "manual");
        updatelogBox();
        openedlogpage = "";
      }
        /*
        if ($("input#type").val() === "instance") {
            window.location.href = $SCRIPT_ROOT + "/viewInstanceLog";
        } else {
            window.location.href = $SCRIPT_ROOT + "/viewSoftwareLog";
        }*/
    });

    $("#live").change(function () {
      if ( $(this).is(':checked') ) {
        updatelogBox();
        setSpeed(100);
        setCookie("autoUpdate", "live");
      }
    });

    $("#slow").change(function () {
      if ( $(this).is(':checked') ) {
        updatelogBox();
        setSpeed(2500);
        setCookie("autoUpdate", "slow");
      }
    });

    $("#refreshlog").click(function () {
      loadLog(current_log);
      return false;
    });

    $("#addfile").click(function () {
      var filename;
      $.colorbox.close();
      if (selectedFile !== "") {
        $.ajax({
          type: "POST",
          url: $SCRIPT_ROOT + '/checkFileType',
          data: {path: selectedFile}
          })
        .done(function(data) {
          if (data.code === 0) {
            $("#error").Popup(data.result, {type: 'alert', duration: 5000});
          } else {
            filename = selectedFile.replace(/^.*(\\|\/|\:)/, '');
            $("#openloglist ul").append("<li rel='" + selectedFile + "'>" +
                    "<span class='bt_close' title='Remove this element!'" +
                    ">×</span>" + filename + "</li>");
          }
        })
        .fail(function(jqXHR, exception) {
          $("#error").Popup("An Error occured: \n" + jqXHR.responseText, {type: 'error'});
        });
      }
      else{
        $("#error").Popup("No log file selected!", {type: 'alert', duration: 3000});
      }
      return false;
    });

    $("#logEdit").click(function () {
      if ( logfilelist === "" ) {
        $("#error").Popup("You don't have any services yet! Please run your services to choose custom log files",
                    {type: 'alert', duration: 5000});
        return false;
      }
      if ( $(this).text() === "Save list") {
        $(this).text("Edit list");
        $("#addbox").hide();
        $("#openloglist ul li").click(function () {
          var logfile = $(this).attr('rel');
          if (current_log === logfile){
            return false;
          }
          loadLog(logfile, $(this));
          return false;
        });
        var savelist = "";
        $("#openloglist ul li").each(function () {
          $(this).children( "span" ).hide();
          $(this).children( "span" ).unbind('click');
          if ( $(this).children('span').length > 0 ) {
            savelist += $(this).attr('rel') + "#"
          }
        });
        //Send result to be saved!!
        $.ajax({
          type: "POST",
          url: $SCRIPT_ROOT + '/saveFileContent',
          data: {file: logfilelist, content: savelist}
          })
        .done(function(data) {
          if (data.code === 0) {
            $("#error").Popup(data.result, {type: 'error', duration: 5000});
          } else {
            $("#error").Popup("Done! Your log file list has been saved.", {type: 'confirm', duration: 5000});
          }
        })
        .fail(function(jqXHR, exception) {
          $("#error").Popup("An Error occured: \n" + jqXHR.responseText, {type: 'error'});
        });
      }
      else {
        $(this).text("Save list");
        $("#openloglist ul li").unbind('click');
        $("#addbox").show();
        $("#openloglist ul li").each(function () {
          $(this).children( "span" ).show();
          $(this).children( "span" ).click(function () {
            $(this).parent().remove();
          });
        });
      }
      return false;
    });

    $("#slapswitch").click( function () {
      if ( $(this).attr('rel') === 'opend' ) {
        window.location.href = $SCRIPT_ROOT + "/inspectInstance";
      }
      else {
        $("#softrun").click();
      }
      return false;
    });

});
