/*jslint undef: true */
/*global $, window, $SCRIPT_ROOT, setRunningState, setCookie, getCookie, deleteCookie */
/*global currentState: true, running: true, $current: true, processType: true, currentProcess: true */
/*global sendStop: true, processState: true, openedlogpage: true, logReadingPosition: true, speed: true */
/*global isRunning: true */
/* vim: set et sts=4: */

//Global Traitment!!!

var url = $SCRIPT_ROOT + "/slapgridResult";
var currentState = false;
var running = true;
var $current;
var processType = "";
var currentProcess;
var sendStop = false;
var processState = "Checking"; //define slapgrid running state
var openedlogpage = ""; //content software or instance if the current page is software or instance log, otherwise nothing
var logReadingPosition = 0;
var speed = 5000;
var maxLogSize = 100000; //Define the max limit of log to display  ~ 2500 lines
var currentLogSize = 0; //Define the size of log actually displayed
var isRunning = function () {
    "use strict";
    if (running) {
        $("#error").Popup("Slapgrid is currently under execution!",
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

function removeFirstLog(){
  "use strict";
  currentLogSize -= parseInt($("#salpgridLog p:first-child").attr('rel'), 10);
  $("#salpgridLog p:first-child").remove();
}

function getRunningState() {
    "use strict";
    var size = 0;
    var log_info = "";
    var param = {
        position: logReadingPosition,
        log: (processState !== "Checking" && openedlogpage === processType.toLowerCase()) ? openedlogpage : ""
    },
        jqxhr = $.post(url, param, function (data) {
            setRunningState(data);
            size = data.content.position - logReadingPosition;
            if (logReadingPosition !== 0 && data.content.truncated){
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
            if (running && processState === "Checking" && openedlogpage !== "") {
                $("#salpgridLog").show();
                $("#manualLog").hide();
            }
            processState = running ? "Running" : "Stopped";
            currentLogSize += parseInt(size, 10);
            if (currentLogSize > maxLogSize){
                //Remove the first element into log div
                removeFirstLog();
                if (currentLogSize > maxLogSize){
                    removeFirstLog(); //in cas of previous <p/> size is 0
                }
            }
        })
        .error(function () {
            clearAll(false);
        })
        .complete(function () {
            if (running) {
                setTimeout(function () {
                    getRunningState();
                }, speed);
            }
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

        if ($("#instrun").text() === "Stop instance") {
            type = "slapgrid-cp";
        }
        $.post(urlfor, {type: type}, function (data) {
            //if (data.result) {
                //$("#error").Popup("Failled to run Slapgrid", {type:'error', duration:3000}); });
            //}
        })
            .error(function () {
                $("#error").Popup("Failed to stop Slapgrid process", {type: 'error', duration: 3000});
            })
            .complete(function () {
                sendStop = false;
                processState = "Stopped";
            });
    }
}

function bindRun() {
    "use strict";
    $("#softrun").click(function () {
        if ($("#softrun").text() === "Stop software") {
            stopProcess();
        } else {
            if (!isRunning()) {
                setCookie("slapgridCMD", "Software");
                window.location.href = $SCRIPT_ROOT + "/viewSoftwareLog";
            }
        }
        return false;
    });
    $("#instrun").click(function () {
        if ($("#instrun").text() === "Stop instance") {
            stopProcess();
        } else {
            if (!isRunning()) {
                setCookie("slapgridCMD", "Instance");
                window.location.href = $SCRIPT_ROOT + "/viewInstanceLog";
            }
        }
        return false;
    });
}

function setRunningState(data) {
    "use strict";
    if (data.result) {
        if (!currentState) {
            $("#running").show();
            running = true;
            //change run menu title and style
            if (data.software) {
                $("#softrun").empty();
                $("#softrun").append("Stop software");
                $("#softrun").css("color", "#0271BF");
                $current = $("#softrun");
                processType = "Software";
            }
            if (data.instance) {
                $("#instrun").empty();
                $("#instrun").append("Stop instance");
                $("#instrun").css("color", "#0271BF");
                $current = $("#instrun");
                processType = "Instance";
            }
        }
    } else {
        $("#running").hide();
        running = false; //nothing is currently running
        if ($current !== undefined) {
            $current.empty();
            $current.append("Run " + processType.toLowerCase());
            $current.css("color", "#000");
            $current = undefined;
            currentState = false;
            $("#error").Popup("Slapgrid finished running your " + processType + " Profile", {type: 'info', duration: 3000});
        }
    }
    currentState = data.result;
}

function runProcess(urlfor, data) {
    "use strict";
    if (!isRunning()) {
        running = true;
        processState = "Running";
        currentProcess = $.post(urlfor)
            .error(function () {
                $("#error").Popup("Failled to run Slapgrid", {type: 'error', duration: 3000});
            });
        setRunningState(data);
        setTimeout(getRunningState, 6000);
    }
}

function checkSavedCmd() {
    "use strict";
    var result = getCookie("slapgridCMD");
    if (!result) {
        return false;
    }
    if (result === "Software") {
        running = false;
        runProcess(($SCRIPT_ROOT + "/runSoftwareProfile"),
                   {result: true, instance: false, software: true});
    } else if (result === "Instance") {
        running = false;
        runProcess(($SCRIPT_ROOT + "/runInstanceProfile"),
                   {result: true, instance: true, software: false});
    }
    deleteCookie("slapgridCMD");
    return (result !== null);
}
