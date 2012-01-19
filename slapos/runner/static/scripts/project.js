$(document).ready( function() {
	var method = $("input#method").val();
	var workdir = $("input#workdir").val();
	if (method != "file"){
		script = (method == "new") ? "/openFolder" : "/readFolder";
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
			$("#flash").append("<ul class='flashes'><li>Error: Select the folder of your software</li></ul>");
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
		relativeFile = file.replace(workdir, "");
		$("#info").empty();
		$("#info").append("Selection: " + relativeFile);
		$("input#subfolder").val(file);
		path = "";
		if(method == "open"){
			checkFolder(file);
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