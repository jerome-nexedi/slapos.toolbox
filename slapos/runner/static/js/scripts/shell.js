/*jslint undef: true */
/*global $, document, $SCRIPT_ROOT, window */
/*global path: true */
/* vim: set et sts=4: */

$(document).ready(function () {
  "use strict";

  $("#shell").click (function() {
    $("#shell-window").slideToggle("fast");
    if ( $("#shell-window").is(':visible') ) {
      $("#shell-input").focus();
    }
  });

  $("#shell-input").keypress(function (event) {
    if(event.which === 13) {
      var command = $("#shell-input").val();
      event.preventDefault();
      var data = { command: command };
      $.post("/runCommand", data, function (data) {
        data = ">>> " + command + "\n\n" + data;
        $("#shell-result").val(data);
        $("#shell-input").val("");
    });
    }
  });
});
