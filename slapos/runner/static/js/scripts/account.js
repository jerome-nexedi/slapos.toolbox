/*jslint undef: true */
/*global $, document, window, $SCRIPT_ROOT */
/* vim: set et sts=4: */

$(document).ready(function () {
    "use strict";
    var send = false;
    $("#information").Tooltip();

    $("#update").click(function () {
        var haspwd = false,
            hasAccount = ($("input#hasAccount").val() !== "");
        if ($("input#username").val() === "" || !$("input#username").val().match(/^[\w\d\._\-]+$/)) {
            $("#error").Popup("Invalid user name. Please check it!", {type: 'alert', duration: 3000});
            return false;
        }
        if ($("input#name").val() === "") {
            $("#error").Popup("Please enter your name and surname!", {type: 'alert', duration: 3000});
            return false;
        }
        if (!$("input#email").val().match(/^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/)) {
            $("#error").Popup("Please enter a valid email address!", {type: 'alert', duration: 3000});
            return false;
        }
        if (!hasAccount && !$("input#password").val()) {
            $("#error").Popup("Please enter your new password!", {type: 'alert', duration: 3000});
            return false;
        }
        if ($("input#password").val() !== "") {
            if ($("input#password").val() === "" || !$("input#password").val()) {
                $("#error").Popup("Please enter your new password!", {type: 'alert', duration: 3000});
                return false;
            }
            if ($("input#password").val() !== $("input#cpassword").val()) {
                $("#error").Popup("your password does not match!", {type: 'alert', duration: 3000});
                return false;
            }
            haspwd = true;
        }
        if (!$("input#rcode").val().match(/^[\w\d]+$/)) {
            $("#error").Popup("Please enter your password recovery code.", {type: 'alert', duration: 3000});
            return false;
        }
        if (send) {
            return false;
        }
        send = true;
	var base_url = 'https://' + $("input#username").val()  + ':'
	    + $("input#password").val() + '@' + location.host
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + ((hasAccount) ? '/updateAccount' : '/configAccount'),
            data: {
                name: $("input#name").val(),
                username: $("input#username").val(),
                email: $("input#email").val(),
                password: ((haspwd) ? $("input#password").val() : ""),
                rcode: $("input#rcode").val()
            },
            success: function (data) {
                if (data.code === 1) {
                    window.location.href = $SCRIPT_ROOT + '/';
                } else {
                    $("#error").Popup(data.result, {type: 'error', duration: 5000});
                }
                send = false;
            },
            error: function () { send = false; }
        });
        return false;
    });
    $("#save").click(function () {
        if (send) {
            return false;
        }
        send = true;
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/updateBuildAndRun',
            data: {
                run_instance: $("input#run_instance").is(':checked'),
                run_software: $("input#run_software").is(':checked'),
                max_run_instance: $("input#max_run_instance").val(),
                max_run_software: $("input#max_run_software").val()
            },
            success: function (data) {
                if (data.code === 1) {
                    $("#error").Popup(data.result, {type: 'alert', duration: 5000});
                } else {
                    $("#error").Popup(data.result, {type: 'error', duration: 5000});
                }
                send = false;
            },
            error: function () { send = false; }
        });
        return false;
    });
    $("#add_user").click(function () {
        if ($("input#new_username").val() === "" || !$("input#new_username").val().match(/^[\w\d\._\-]+$/)) {
            $("#error").Popup("Invalid user name. Please check it!", {type: 'alert', duration: 3000});
            return false;
        }
        if (!$("input#new_rcode").val().match(/^[\w\d]+$/)) {
            $("#error").Popup("Please enter your password recovery code.", {type: 'alert', duration: 3000});
            return false;
        }
        if (send) {
            return false;
        }
        send = true;
        $.ajax({
            type: "POST",
            url: $SCRIPT_ROOT + '/addUser',
            data: {
                username: $("input#new_username").val(),
                password: $("input#new_password").val(),
  		rcode: $("input#new_rcode").val(),
            },
            success: function (data) {
                if (data.code === 1) {
                    $("#error").Popup(data.result, {type: 'info', duration: 5000});
                } else if (data.code === 0) {
                    $("#error").Popup(data.result, {type: 'error', duration: 5000});
		} else {
                    $("#error").Popup(data.result, {type: 'alert', duration: 5000});
                }
                send = false;
                $("input#new_username").val('');
                $("input#new_password").val('');
  		$("input#new_rcode").val('');
            },
            error: function () { send = false; }
        });
        return false;
    });
});
