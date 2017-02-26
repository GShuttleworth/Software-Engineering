//global?
var refreshrate = 2000;
function refresh() {
	$.ajax({
		type : 'POST',
		url : "/refresh_anomaly",
		success: function(d) {
			var data = JSON.parse(d);
			mode(data.mode);
			live(data.live);
		},
		error: function(d) {
			console.log("server down");
			//error bar here
		}
	});
	//for testing, stop this fucking refreshing
	setTimeout(refresh, refreshrate); // you could choose not to continue on failure...
}

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
			
		},
		error: function(d) {
			console.log("unable to switch");
			//error bar here
		}
	});
}

$(document).ready(function() {
	// run the first time; all subsequent calls will take care of themselves
	refresh();
	
	//event listeners
	$("#btn-live").click(function(e){
		e.preventDefault();
		//alert("hi");
		togglemode(1);
	});
	$("#btn-historical").click(function(e){
	   e.preventDefault();
	   //alert("hi");
	   togglemode(0);
	   //import file
   });
});
