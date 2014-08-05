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
      $.post("/runCommand", data, function (data) {
        data = ">>> " + command + "\n\n" + data;
        $("#shell-result").val(data);
        $("#shell-input").val("");
        updateHistory();
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
  });
});
