//global?
var refreshrate = 2000;
function live(status) {
	if(status==true){
		
	}else{
		
	}
}
function mode(status) {
	if(status==1){
		$('#live').html('Live Data');
	}else{
		$('#live').html('Historical Data');
	}
}

function changerefresh(rate){
	refreshrate=rate;
	alert("refresh rate changed to: "+rate);
}

function togglemode(mode){
	var data = {"mode":mode};
	$.ajax({
		type : 'POST',
		url : "/toggle",
		data : JSON.stringify(data),
		contentType: 'application/json;charset=UTF-8',
		success: function(d) {
			success = JSON.parse(d);
			if(success.change==false){
				alert("Already in live mode!");
			}
		},
		error: function(d) {
			console.log("unable to switch");
			//error bar here
		}
	});
}

$(document).ready(function() {
	// run the first time; all subsequent calls will take care of themselves
	init_session();
	//event listeners
	$("#btn-live").click(function(e){
		e.preventDefault();
		//alert("hi");
		togglemode(1);
	});
	$("#btn-historical").click(function(e){
	   e.preventDefault();
	   document.getElementById("data_file").click();
	   //alert("hi");
	   //togglemode(0);
	   //import file
   });
	$("input[type=file]").on("change", function(e){
		var data = new FormData();
		var file = $("#data_file")[0].files[0];
		if (confirm("Are you sure you want to upload: " + file.name)) {
			data.append("file",file);
			$.ajax({
				type: 'POST',
				url: "/upload",
				data: data,
				cache: false,
				processData: false, // Don't process the files
				async: false,
				contentType: false,
				success: function(data, textStatus, jqXHR){
					//console.log("success");
					alert("File uploaded");
					togglemode(0);
				},
				error: function(jqXHR, textStatus, errorThrown){
					console.log("fail");
				}
			});
		 }
	});
});
