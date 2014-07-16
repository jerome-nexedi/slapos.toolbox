/*jslint undef: true */
/*global $, window, $SCRIPT_ROOT, setRunningState, setCookie, getCookie, deleteCookie */
/*global currentState: true, running: true, $current: true, processType: true, currentProcess: true */
/*global sendStop: true, openedlogpage: true, logReadingPosition: true, speed: true */
/*global isRunning: true */
/* vim: set et sts=4: */

//Global Traitment!!!

var url = $SCRIPT_ROOT + "/slapgridResult";
var currentState = false;
var running = true;
var processType = "";
var currentProcess;
var sendStop = false;
var forcedStop = false;
var openedlogpage = ""; //content software or instance if the current page is software or instance log, otherwise nothing
var logReadingPosition = 0;
var speed = 5000;
var maxLogSize = 100000; //Define the max limit of log to display  ~ 2500 lines
var currentLogSize = 0; //Define the size of log actually displayed
var isRunning = function () {
    "use strict";
    if (running) {
        $("#error").Popup("Slapgrid is currently running!",
                          {type: 'alert', duration: 3000});
    }
    return running;
};

function setSpeed(value) {
    "use strict";
    if (openedlogpage === "") {
        speed = 5000;
    } else {
        speed = value;
    }
}

function clearAll(setStop) {
    "use strict";
    currentState = false;
    running = setStop;
}

function removeFirstLog() {
    "use strict";
    currentLogSize -= parseInt($("#salpgridLog p:first-child").attr('rel'), 10);
    $("#salpgridLog p:first-child").remove();
}

function getRunningState() {
    "use strict";
    var size = 0,
        log_info = "",
        param = {
            position: logReadingPosition,
            log: (openedlogpage !== "") ? processType.toLowerCase() : ""
        },
        jqxhr = $.post(url, param, function (data) {
            running = data.result;
            if (data.instance.state) {
                processType = "Instance";
            } else if (data.software.state) {
                processType = "Software";
            }
            setRunningState(data);
            size = data.content.position - logReadingPosition;
            if (size < 0) {
                clearAll();
            }
            if (logReadingPosition !== 0 && data.content.truncated) {
                log_info = "<p  class='info' rel='0'>SLAPRUNNER INFO: SLAPGRID-LOG HAS BEEN TRUNCATED HERE. To see full log reload your log page</p>";
            }
            logReadingPosition = data.content.position;
            if (data.content.content !== "") {
                if (data.content.content !== "") {
                    $("#salpgridLog").append(log_info + "<p rel='" + size + "'>" + data.content.content.toHtmlChar() + "</p>");
                    $("#salpgridLog")
                        .scrollTop($("#salpgridLog")[0].scrollHeight - $("#salpgridLog").height());
                }
            }
            if (running && openedlogpage !== "") {
                $("#salpgridLog").show();
                $("#manualLog").hide();
                $("#slapstate").show();
                $("#openloglist").hide();
            }
            currentLogSize += parseInt(size, 10);
            if (currentLogSize > maxLogSize) {
                //Remove the first element into log div
                removeFirstLog();
                if (currentLogSize > maxLogSize) {
                    removeFirstLog(); //in cas of previous <p/> size is 0
                }
            }
        }).error(function () {
            clearAll(false);
        });
}

function stopProcess() {
    "use strict";
    if (sendStop) {
        return;
    }
    if (running) {
        sendStop = true;

        var urlfor = $SCRIPT_ROOT + "stopSlapgrid",
            type = "slapgrid-sr";

        if (processType === "Instance") {
            type = "slapgrid-cp";
        }
        $.post(urlfor, {type: type}, function (data) {
        })
            .error(function () {
                $("#error").Popup("Failed to stop Slapgrid process", {type: 'error', duration: 3000});
            })
            .complete(function () {
                sendStop = false;
                forcedStop = true;
            });
    }
}

function bindRun() {
    "use strict";
    $("#softrun").click(function () {
        if ($(this).hasClass('slapos_stop')) {
            stopProcess();
        } else {
            if (!isRunning()) {
                runProcess($SCRIPT_ROOT + "/runSoftwareProfile");
                window.location.href = $SCRIPT_ROOT + "/viewLog?logfile=software.log";
            }
        }
        return false;
    });
    $("#instrun").click(function () {
        if ($("#softrun").hasClass('slapos_stop')) {
            stopProcess();
        } else {
            if (!isRunning()) {
                runProcess($SCRIPT_ROOT + "/runInstanceProfile");
                if (window.location.pathname === "/viewLog")
                     window.location.href = $SCRIPT_ROOT + "/viewLog?logfile=instance.log";
            }
        }
        return false;
    });
}

function updateStatus(elt, val) {
  "use strict";
  var src = '#' + elt + '_run_state', value = 'state_' + val;
  $(src).removeClass();
  $(src).addClass(value);
  switch (val) {
    case "waiting":
      $(src).children('p').text("Queue");
      break;
    case "stopped":
      $(src).children('p').text("Stopped by user");
      break;
    case "terminated":
      $(src).children('p').text("Complete");
      break;
    case "running":
      $(src).children('p').text("Processing");
      processType = elt;
      getRunningState()
      break;
  }
  // in case of failure
  if ($("#salpgridLog").text().indexOf("Failed to run buildout profile") !== -1) {
    var src = '#' + elt + '_run_state', value = 'state_' + "stopped";
    $(src).removeClass();
    $(src).addClass(value);
    $(src).children('p').text("Buildout Failed");
  }
}

function setRunningState(data) {
    "use strict";
    if (data.result) {
        if (!currentState) {
            $("#running").show();
            running = true;
            //change run menu title and style
            if (data.software.state) {
                if ( $("#running").children('span').length === 0 ) {
                  $("#softrun").removeClass('slapos_run');
                  $("#softrun").addClass('slapos_stop');
                  $("#running img").before('<p id="running_info" class="software">Building software...</p>');
                }
            }
            if (data.instance.state) {
              ///Draft!!
                if ( $("#running").children('span').length === 0 ) {
                  $("#softrun").removeClass('slapos_run');
                  $("#softrun").addClass('slapos_stop');
                  $("#running img").before('<p id="running_info" class="instance">Running instance...</p>');
                }
            	if (processType === "Software") {
                    running = false;
                    $("#running_info").remove();
                    $("#softrun").addClass('slapos_run');
                    $("#softrun").removeClass('slapos_stop');
                    $("#instrun").click();
                }
            }
        }
    } else {
        if ( $("#running").is(":visible") ) {
          $("#error").Popup("Slapgrid finished running your " + processType + " Profile", {type: 'info', duration: 3000});
          if ( forcedStop ) {
            updateStatus('instance', 'stopped');
            updateStatus('software', 'stopped');
          }
          else {
            updateStatus(processType.toLowerCase(), 'terminated');
          }
          //Update window!!!
          $("#slapswitch").attr('rel', 'opend');
          $("#slapswitch").text('Access application');
        }
        $("#running").hide();
        $("#running_info").remove();
        running = false; //nothing is currently running
        $("#softrun").removeClass('slapos_stop');
        $("#softrun").addClass('slapos_run');
        if ( $("#running").children('span').length > 0 ) {
          $("#running").children('p').remove();
        }
        currentState = false;
    }
    currentState = data.result;
}

function runProcess(urlfor) {
    "use strict";
    if (!isRunning()) {
        currentProcess = $.post(urlfor);
        if ( $("#running_info").children('span').length > 0 ) {
          $("#running_info").children('p').remove();
        }
    }
}

getRunningState();
setInterval('getRunningState()', 3000);
