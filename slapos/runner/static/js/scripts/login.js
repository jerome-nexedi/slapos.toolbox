$(document).ready( function() {
  var send = false;
  //change background
  $("body").css("background", "#9C9C9C");
	$("#login").click(function(){
    if (send) return false;
		if($("input#clogin").val() === "" || !$("input#clogin").val().match(/^[\w\d\.-]+$/)){
			$("#error").Popup("Please enter a valid user name", {type:'alert', duration:3000});
			return false;
		}
		if($("input#cpwd").val() === "" || $("input#cpwd").val() ==="******"){
			$("#error").Popup("Please enter your password", {type:'alert', duration:3000});
			return false;
		}
    send = true;
    var param = {clogin:$("input#clogin").val(), cpwd:$("input#cpwd").val()};
    var url = $SCRIPT_ROOT + "/doLogin";
    $.post(url, param, function(data) {
      if (data.code==1){
        location.href = $SCRIPT_ROOT + '/';
      }
      else{
        $("#error").Popup(data.result, {type:'alert', duration:3000});
      }
    })
    .error(function() {$("#error").Popup("Cannot send your account identifier please try again!!",
      {type:'alert', duration:3000});})
    .complete(function() {
      send = false;
    });
    return false;
	});
});