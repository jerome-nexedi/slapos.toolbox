/*jslint undef: true */
/*global $, document, window, $SCRIPT_ROOT */
/* vim: set et sts=4: */

$(document).ready(function () {
    "use strict";

    var send = false;
    //change background
    $("body").css("background", "#9C9C9C");
    $("#login").click(function () {
        if (send) {
            return false;
        }
        if ($("input#clogin").val() === "" || !$("input#clogin").val().match(/^[\w\d\.\-]+$/)) {
            $("#error").Popup("Please enter a valid user name", {type: 'alert', duration: 3000});
            return false;
        }
        if ($("input#cpwd").val() === "" || $("input#cpwd").val() === "******") {
            $("#error").Popup("Please enter your password", {type: 'alert', duration: 3000});
            return false;
        }
        send = true;
        var param = { clogin: $("input#clogin").val(), cpwd: $("input#cpwd").val() },
            url = $SCRIPT_ROOT + "/doLogin";

        $("#login").removeClass("button").addClass("dsblebutton");
        $.post(url, param, function (data) {
            if (data.code === 1) {
	        url = 'https://' + param.clogin + ':' + param.cpwd + '@'
		+ location.host + $SCRIPT_ROOT + '/';
                window.location.href = url;
            } else {
                $("#error").Popup(data.result, {type: 'alert', duration: 3000});
            }
        })
            .error(function (response) {
                if (response && response.status === 401) {
                    $("#error").Popup('Login and/or password is incorrect.',
                                      {type: 'alert', duration: 3000}
                    );
                    return
                }
                $("#error").Popup("Cannot send your account identifier",
                                  {type: 'alert', duration: 3000});
            })
            .complete(function () {
                $("#login").removeClass('dsblebutton').addClass('button');
                send = false;
            });
        return false;
    });
});
