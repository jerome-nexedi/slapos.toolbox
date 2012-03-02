//Global Traitment!!!
var url = $SCRIPT_ROOT + "/slapgridResult"
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
var isRunning = function(){
  if (running){
    $("#error").Popup("Slapgrid is currently under execution!", {type:'alert', duration:3000});
  }
  return running;
}
function setSpeed(value){
  if (openedlogpage == ""){
    speed = 5000;
  }
  else{ speed=value;}
}
function getRunningState(){
  var param = {position:logReadingPosition, log:(processState!="Checking" && openedlogpage==processType.toLowerCase())? openedlogpage:""}
  var jqxhr = $.post(url, param, function(data) {
      setRunningState(data)
      logReadingPosition = data.content.position;
      if(data.content.content != ""){
        $("#salpgridLog").append(data.content.content.toHtmlChar());
        $("#salpgridLog")
        .scrollTop($("#salpgridLog")[0].scrollHeight - $("#salpgridLog")
          .height());
      }
      if (running && processState=="Checking" && openedlogpage != ""){$("#salpgridLog").show();$("#manualLog").hide();}
      processState = (running)?"Running":"Stopped";
  })
  .error(function() { clearAll(false); })
  .complete(function() {
    if (running){
      setTimeout(function(){
        getRunningState();
      }, speed);
    }
  });
}
function clearAll(setStop){
  currentState = false;
  running = setStop;
}
function bindRun(){
  $("#softrun").click(function(){
    if($("#softrun").text() == "Stop"){
      stopProcess();
    }
    else{
      if(!isRunning()){
        setCookie("slapgridCMD", "Software");
        location.href = $SCRIPT_ROOT + "/viewSoftwareLog";
      }
    }
    return false;
  });
  $("#instrun").click(function(){
    if($("#instrun").text() == "Stop"){
      stopProcess();
    }
    else{
      if(!isRunning()){
        setCookie("slapgridCMD", "Instance");
        location.href = $SCRIPT_ROOT + "/viewInstanceLog";
      }
    }
    return false;
  });
}
function setRunningState(data){
  if (data.result){
    if(!currentState){
      $("#running").show();
      running = true;
      //change run menu title and style
      if(data.software){
        $("#softrun").empty();
        $("#softrun").append("Stop");
        $("#softrun").css("color", "#0271BF");
        $current = $("#softrun");
        processType = "Software";
      }
      if(data.instance){
        $("#instrun").empty();
        $("#instrun").append("Stop");
        $("#instrun").css("color", "#0271BF");
        $current = $("#instrun");
        processType = "Instance";
      }
    }
  }
  else{
    $("#running").hide();
    running = false; //nothing is currently running
    if ($current != undefined){
      $current.empty();
      $current.append("Run");
      $current.css("color", "#000");
      $current = undefined;
      currentState = false;
      $("#error").Popup("Successfully run " + processType + " Profile", {type:'info', duration:3000});
    }
  }
  currentState = data.result;
}
function runProcess(urlfor, data){
  if(!isRunning()){
    running = true;
    processState = "Running";
    currentProcess = $.post(urlfor)
    .error(function() {
      $("#error").Popup("Failled to run Slapgrid", {type:'error', duration:3000}); });
    setRunningState(data);
    setTimeout("getRunningState()", 5000);
  }
}
function stopProcess(){
  if (sendStop) return;
  if (running){
    sendStop = true;
    var urlfor = $SCRIPT_ROOT + "stopSlapgrid"
    var type = "slapgrid-sr.pid";
    if($("#instrun").text() == "Stop"){
      type = "slapgrid-cp.pid";
    }
    $.post(urlfor, {type:type}, function(data){
      //if (data.result){
        //$("#error").Popup("Failled to run Slapgrid", {type:'error', duration:3000}); });
      //}
    })
    .error(function() {
      $("#error").Popup("Failled to stop Slapgrid process", {type:'error', duration:3000}); })
    .complete(function() {sendStop = false;processState="Stopped";});
  }
}

function checkSavedCmd(){
  var result = getCookie("slapgridCMD");
  if (!result) return false;
  if (result == "Software"){
    running = false;
    runProcess(($SCRIPT_ROOT + "/runSoftwareProfile"),
      {result: true, instance:false, software:true});
  }
  else if(result == "Instance"){
    running = false;
    runProcess(($SCRIPT_ROOT + "/runInstanceProfile"),
      {result: true, instance:true, software:false});
  }
  deleteCookie("slapgridCMD");
  return (result != null);
}