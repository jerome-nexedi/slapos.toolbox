$(document).ready( function() {
	var method = $("input#method").val();
	var workdir = $("input#workdir").val();
	if (method != "file"){
		script = "/openFolder";
		$('#fileTree').fileTree({ root: workdir, script: $SCRIPT_ROOT + script, folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false, selectFolder: true }, function(file) { 
			selectFile(file);
		});
	}
	$("input#subfolder").val("");
	$("#create").click(function(){
		repo_url = $("input#software").val();
		if($("input#software").val() == "" || !$("input#software").val().match(/^[\w\d._-]+$/)){
			$("#error").Popup("Invalid Software name", {type:'alert', duration:3000})
			return false;
		}
		if($("input#subfolder").val() == ""){
			$("#error").Popup("Select the parent folder of your software!", {type:'alert', duration:3000})
			return false;
		}
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/createSoftware',
			data: "folder=" + $("input#subfolder").val() + $("input#software").val(),
			success: function(data){
				if(data.code == 1){
					location.href = $SCRIPT_ROOT + '/editSoftwareProfile'
				}
				else{
					$("#error").Popup(data.result, {type:'error', duration:5000})
					
				}
			}
		});
		return false;
	});
	
	$("#open").click(function(){
		$("#flash").fadeOut('normal');
		$("#flash").empty();
		$("#flash").fadeIn('normal');
		if($("input#path").val() == ""){
			$("#error").Popup("Select a valid Software Release folder!", {type:'alert', duration:3000})
			return false;
		}
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/setCurrentProject',
			data: "path=" + $("input#path").val(),
			success: function(data){
				if(data.code == 1){
					location.href = $SCRIPT_ROOT + '/editSoftwareProfile'
				}
				else{
					$("#error").Popup(data.result, {type:'error', duration:5000})
				}
			}
		});
		return false;
	});
	
	function selectFile(file){
		$("#info").empty();		
		$("input#subfolder").val(file);
		path = "";
		if(method == "open"){
			$("#info").append("Selection: " + file);
			checkFolder(file);
		}
		else{
			if($("input#software").val() != "" && $("input#software").val().match(/^[\w\d._-]+$/)){
				$("#info").append("New Software in: " + file + $("input#software").val());
			}
			else{
				$("#info").append("Selection: " + file);
			}
		}
		return;
	}
	
	function checkFolder(path){
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/checkFolder',
			data: "path=" + path,
			success: function(data){
				var path = data.result;
				$("input#path").val(path);
				if (path != ""){
					$("#check").fadeIn('normal');					
				}
				else{
					$("#check").hide();
				}
			}
		});
		return "";
	}
});