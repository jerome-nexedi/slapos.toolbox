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
		$("#flash").fadeOut('normal');
		$("#flash").empty();
		$("#flash").fadeIn('normal');
		repo_url = $("input#software").val();
		if($("input#software").val() == "" || !$("input#software").val().match(/^[\w\d._-]+$/)){
			$("#flash").append("<ul class='flashes'><li>Error: Invalid Software name</li></ul>");
			return false;
		}
		if($("input#subfolder").val() == ""){
			$("#flash").append("<ul class='flashes'><li>Error: Select the parent folder of your software!</li></ul>");
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
					$("#flash").append("<ul class='flashes'><li>Error: " + data.result + "</li></ul>");
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
			$("#flash").append("<ul class='flashes'><li>Error: Select a valid Software Release folder</li></ul>");
			return false;
		}
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/setCurentProject',
			data: "path=" + $("input#path").val(),
			success: function(data){
				if(data.code == 1){
					location.href = $SCRIPT_ROOT + '/editSoftwareProfile'
				}
				else{
					$("#flash").append("<ul class='flashes'><li>Error: " + data.result + "</li></ul>");
				}
			}
		});
		return false;
	});
	
	function selectFile(file){
		var relativeFile = file.replace(workdir, "");
		$("#info").empty();		
		$("input#subfolder").val(file);
		path = "";
		if(method == "open"){
			$("#info").append("Selection: " + relativeFile);
			checkFolder(file);
		}
		else{
			if($("input#software").val() != "" && $("input#software").val().match(/^[\w\d._-]+$/)){
				$("#info").append("New Software in: " + relativeFile + $("input#software").val());
			}
			else{
				$("#info").append("Selection: " + relativeFile);
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