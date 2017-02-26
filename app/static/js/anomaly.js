//global?
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

function init_session(){
	refresh()
}
