$(document).ready( function() {
	var send = false;
	var cloneRequest;
	$('#fileTree').fileTree({ root: $("input#workdir").val(), script: $SCRIPT_ROOT + '/readFolder', folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false }, function(file) { 
		selectFile(file);
	});
	configRadio();
	$("input#nothing").change(function(){
		configRadio();
	});
	$("input#ssh").change(function(){
		configRadio();
	});
	$("input#https").change(function(){
		configRadio();
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
		if($("input#https").is(':checked')){
			if($("input#username").val() == "" || !$("input#username").val().match(/^[\w\d\._-]+$/)){
				$("#error").Popup("Please enter a correct username", {type:'alert', duration:3000});
				return false;
			}
			if($("input#password").val() != ""){
				if(repo_url.indexOf("https://") != -1){
					repo_url = "https://" + $("input#username").val() +
						":" + $("input#password").val() +
						"@" + repo_url.substring(8);
				}
				else{
					$("#error").Popup("The URL of your repository should start with 'https://'", {type:'alert', duration:3000});
					return false;
				}
			}
			else{
				$("#error").Popup("Please enter your password", {type:'alert', duration:3000});
				return false;
			}
		}
		else if(repo_url.indexOf("https://") != -1){
			$("#error").Popup("Please select HTTPS Security Mode for this repository", {type:'alert', duration:3000});
			return false;
		}
		$("#imgwaitting").fadeIn('normal');
		$("#clone").empty();
		$("#clone").append("Stop");
		send = true;
		cloneRequest = $.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/cloneRepository',
			data: {repo: repo_url, name: ($("input#workdir").val() + "/"
				+ $("input#name").val()), email:email,
				user:name},
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
	function configRadio(){
		$("#modelist li").each(function(index) {			
			var boxselector = "#box" + index;
			if($(this).hasClass('checked')){
				$(this).removeClass('checked');				
				$(boxselector).slideUp("normal");
			}
			if($(this).find("input:radio").is(':checked')){
				$(this).addClass('checked');
				//change content here
				$(boxselector).slideDown("normal");
			}
			if(index != 2){
				$("input#password").val("");
				$("input#cpassword").val("");
			}
		});
	}
	
	function selectFile(file){
		//nothing
		return;
	}
});