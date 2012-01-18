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
		$("#flash").fadeOut('normal');
		$("#flash").empty();
		$("#flash").fadeIn('normal');	
		repo_url = $("input#repo").val();
		/* /^(ht|f)tps?:\/\/[a-z0-9-\.]+\.[a-z]{2,4}\/?([^\s<>\#%"\,\{\}\\|\\\^\[\]`]+)?$/ */
		if($("input#repo").val() == "" || !repo_url.match(/^[\w\d\.\/:~@_-]+$/)){			
			$("#flash").append("<ul class='flashes'><li>Error: Invalid url for the repository</li></ul>");
			return false;
		}
		if($("input#name").val() == "" || !$("input#name").val().match(/^[\w\d\._-]+$/)){
			$("#flash").append("<ul class='flashes'><li>Error: Invalid project name</li></ul>");
			return false;
		}
		if($("input#user").val() == "" || $("input#user").val() == "Enter your name..."){
			$("#flash").append("<ul class='flashes'><li>Error: Please enter your name!</li></ul>");
			return false;
		}
		if($("input#email").val() == "" || !$("input#email").val().match(/^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/)){
			$("#flash").append("<ul class='flashes'><li>Error: Please enter your email adress!</li></ul>");
			return false;
		}
		$("#imgwaitting").fadeIn('normal');
		$("#clone").empty();
		$("#clone").append("Stop");
		send = true;
		cloneRequest = $.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/cloneRepository',
			data: "repo=" + repo_url + "&name=" + $("input#name").val() + "&email=" + $("input#email").val() +
				"&user=" + $("input#user").val(),
			success: function(data){
				if(data.code == 1){
					$("#file_navigation").fadeIn('normal');
					$("#flash").append("<ul class='flashes'><li>Repository is cloned!</li></ul>");
					$("input#repo").val("Enter the url of your repository...");
					$("input#name").val("Enter the project name...");
					$('#fileTree').fileTree({ root: $("input#workdir").val(), script: $SCRIPT_ROOT + '/readFolder', folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false }, function(file) { 
						selectFile(file);
					});
				}
				else{
					$("#flash").append("<ul class='flashes'><li>Error: " + data.result + "</li></ul>");
				}
				$("#imgwaitting").hide()
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