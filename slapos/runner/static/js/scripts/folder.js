$(document).ready( function() {
	var send = false;
	var cloneRequest;
	$('#fileTree').fileTree({ root: $("input#workdir").val(), script: $SCRIPT_ROOT + '/readFolder', folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false }, function(file) { 
		selectFile(file);
	});
	$("#clone").click(function(){
		if(send){
			cloneRequest.abort();
			$("#imgwaitting").fadeOut('normal');
			$("#clone").empty();
			$("#clone").append("Clone");
			send = false;
			return;
		}		
		var repo_url = $("input#repo").val();
		var email = "";
		var name = ""
		/* /^(ht|f)tps?:\/\/[a-z0-9-\.]+\.[a-z]{2,4}\/?([^\s<>\#%"\,\{\}\\|\\\^\[\]`]+)?$/ */
		if($("input#repo").val() == "" || !repo_url.match(/^[\w\d\.\/:~@_-]+$/)){						
			$("#error").Popup("Invalid url for the repository", {type:'alert', duration:3000});
			return false;
		}
		if($("input#name").val() == "" || !$("input#name").val().match(/^[\w\d\._-]+$/)){
			$("#error").Popup("Invalid project name", {type:'alert', duration:3000});
			return false;
		}
		if($("input#user").val() != "" && $("input#user").val() != "Enter your name..."){
			name = $("input#user").val();
		}
		if($("input#email").val() != "" && $("input#email").val() != "Enter your email adress..."){
			if(!$("input#email").val().match(/^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/)){
				$("#error").Popup("Please enter a valid email adress!", {type:'alert', duration:3000});
				return false;
			}
			email = $("input#email").val();
		}
		$("#imgwaitting").fadeIn('normal');
		$("#clone").empty();
		$("#clone").append("Stop");
		send = true;		
		cloneRequest = $.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/cloneRepository',
			data: "repo=" + repo_url + "&name=" + $("input#name").val() + "&email=" + email +
				"&user=" + name,
			success: function(data){
				if(data.code == 1){
					$("#file_navigation").fadeIn('normal');
					$("#error").Popup("Your repository is cloned!", {type:'confirm', duration:3000});
					$("input#repo").val("Enter the url of your repository...");
					$("input#name").val("Enter the project name...");
					$('#fileTree').fileTree({ root: $("input#workdir").val(), script: $SCRIPT_ROOT + '/readFolder', folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false }, function(file) { 
						selectFile(file);
					});
				}
				else{
					$("#error").Popup(data.result, {type:'error'});
				}
				$("#imgwaitting").hide();
				$("#clone").empty();
				$("#clone").append("Clone");
				send = false;
			}
		});
		return false;
	});	
	
	function selectFile(file){
		//nothing
		return;
	}
});