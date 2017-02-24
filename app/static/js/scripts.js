function refresh() {
	$.ajax({
		type : 'POST',
		url : "/refresh",
		success: function(d) {
		// do something with the return value here if you like
			var data = JSON.parse(d);
			live(data.live);
			updatedash(data.anomaly,data.trades,data.tradevalue);
		},
		error: function(d) {
			console.log("server down");
		}
	});
	setTimeout(refresh, 2000); // you could choose not to continue on failure...
}

function live(status) {
	if(status==true){
		$('#live').html('Live Data');
	}else{
		$('#live').html('Historical Data');
	}
}

function updatedash(anomalycount,tradecount,tradevalue) {
	$('#trades').html(tradecount);
	$('#anomalies').html(anomalycount);
	$('#tradevalue').html('&pound;'+tradevalue);

}

$(document).ready(function() {
	// run the first time; all subsequent calls will take care of themselves
	setTimeout(refresh, 2000);
});
