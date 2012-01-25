$(document).ready( function() {
	var send = false;
	var runnerDir = $("input#runnerdir").val();
	var ajaxRun;
	fillContent();
	$("#softwarelist").change(function(){
		$("#info").empty();
		$("#info").append("Please select your file or folder into the box...");
		fillContent();
	});
	
	function selectFile(file){
		var relativeFile = file.replace(runnerDir + "/" + $("#softwarelist").val(), "");
		$("#info").empty();
		$("#info").append("Selection: " + relativeFile);
		return;
	}
	
	function fillContent(selectedElt){
		var folder = $("#softwarelist").val();
		var elt = $("option:selected", $("#softwarelist"));
		$('#fileTree').fileTree({ root: runnerDir + "/" + folder, script: $SCRIPT_ROOT + '/readFolder', 
			folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false, selectFolder: true }, function(file) { 
			selectFile(file);
		});
		$("#softcontent").empty();		
		$("#softcontent").append("File content: " + elt.attr('title'));
	}
	
	$("#open").click(function(){
		var elt = $("option:selected", $("#softwarelist"));
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/setCurentProject',
			data: "path=" + elt.attr('rel'),
			success: function(data){
				if(data.code == 1){
					location.href = $SCRIPT_ROOT + '/editSoftwareProfile'
				}
				else{
					error(data.result);
				}
			}
		});
		return false;
	});
	
	$("#delete").click(function(){
		if(send) return;
		send = false;
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/removeSoftwareDir',
			data: "name=" + $("#softwarelist").val(),
			success: function(data){
				if(data.code == 1){
					var folder = $("#softwarelist").val();
					$('#fileTree').fileTree({ root: runnerDir + "/" + folder, script: $SCRIPT_ROOT + '/readFolder', folderEvent: 'click', expandSpeed: 750,
						collapseSpeed: 750, multiFolder: false, selectFolder: true }, function(file) { 
					selectFile(file);
					});
					$("input#file").val("");
					$("#flash").fadeOut('normal');
					$("#flash").empty();
					$("#info").empty();
					$("#info").append("Please select your file or folder into the box...");
					$("#softwarelist").empty();
					for(i=0; i<data.result.length; i++){
						$("#softwarelist").append('<option value="' + data.result[i]["md5"] + 
							'" title="' + data.result[i]["title"] +'" rel="' + 
							data.result[i]["path"] +'">' + data.result[i]["title"] + '</option>');
					}
				}
				else{
					error(data.result);
				}
				send = false;
			}
		});
		return false;	
	});
	
	function error(msg){
		$("#flash").fadeOut('normal');
		$("#flash").empty();
		$("#flash").fadeIn('normal');
		$("#flash").append("<ul class='flashes'><li>" + msg + "</li></ul>");
	}
});