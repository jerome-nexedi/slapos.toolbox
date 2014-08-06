/*jslint undef: true */
/*global $, document, $SCRIPT_ROOT, window */
/*global path: true */
/* vim: set et sts=4: */

var shellHistory = "";
var currentCommand = 0;

$(document).ready(function () {
  "use strict";

  var updateHistory = function () {
    $.getJSON("/getMiniShellHistory", function (data) {
      shellHistory = data;
      currentCommand = shellHistory.length;
    });
  };

  updateHistory();

  $("#shell").click (function() {
    // We have to do that because once slide effect is activated, div is considered as visible
    $("#shell").css("background-color", "#E4E4E4");
    if ( ! $("#shell-window").is(':visible') ) {
      $("#shell").css("background-color", "#C7C7C7");
    }
    $("#shell-window").slideToggle("fast");
    if ( $("#shell-window").is(':visible') ) {
      $("#shell-input").focus();
    }
  });

  $("#shell-input").keypress(function (event) {
    //if Enter is pressed
    if(event.which === 13) {
      event.preventDefault();
      var command = $("#shell-input").val();
      var data = { command: command };
      var old_shell_btn_background = $(".shell_btn").css("background");
      $(".shell_btn").css("background", "url(/static/css/images/loading-min.gif) center right no-repeat")
      $.post("/runCommand", data, function (data) {
        var data = ">>> " + command + "\n\n" + data;
        $("#shell-result").val(data);
        $("#shell-input").val("");
        updateHistory();
      })
      .fail( function(xhr, status, error) {
        $("#error").Popup("Error while sending command. Server answered with :\n" + xhr.statusCode().status + " : " + error, {type: 'error', duration: 3000})
      })
      .always( function() {
        $(".shell_btn").css("background", old_shell_btn_background);
      });
    }
  });

  $("#shell-input").keydown(function (event) {
    //if Key Up is pressed
    if(event.which == 38) {
      event.preventDefault();
      currentCommand--;
      if (currentCommand <= 0)
        currentCommand = 0;
      $("#shell-input").val(shellHistory[currentCommand]);
    }

    //if Key Down is pressed
    if(event.which === 40) {
      event.preventDefault();
      currentCommand++;
      if (currentCommand > shellHistory.length) {
        currentCommand = shellHistory.length;
        $("#shell-input").val("");
      } else {
        $("#shell-input").val(shellHistory[currentCommand]);
      }
    }

    //if Tab is pressed
    if(event.which === 9) {
      event.preventDefault();
        $("#error").Popup("Sorry, Tab completion is not handled for the moment in MiniShell", {type: 'info', duration: 1000})
    }
  });
});
