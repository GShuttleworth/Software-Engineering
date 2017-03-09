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
function dismiss(id){
	var r = confirm("Dismiss anomaly?");
	if (r == true) {
		$.ajax({
			   type : 'POST',
			   url : "/dismiss",
			   data : JSON.stringify(id),
			   contentType: 'application/json;charset=UTF-8',
			   success: function(d) {
			   window.location.replace("/index");
			   },
			   error: function(d) {
			   
			   }
			   });
	}
	
}

//https://datatables.net/forums/discussion/21211/mistake-in-page-jumptodata
$.fn.dataTable.Api.register( 'page.jumpToData()', function ( data, column ) {
							
							var dt, pos, i;
							
							if ($.isArray(data)) {
							// data and columns are arrays
							dt = this.columns( column).data();
							for (pos = dt[0].indexOf( data[0]); pos >= 0; pos = dt[0].indexOf( data[0], pos+1)) {
							// check match on remaining values
							for (i = 1; i < dt.length  &&  (dt[i][pos] == data[i]); i++) {
							}
							if (i === dt.length) break; // found a match
							}
							} else {
							dt = this.column(column).data(); // array of column data
							pos = dt.indexOf( data ); // find index in column array matching data
							}
							
							if ( pos >= 0 ) {
							var page = Math.floor( pos / this.page.info().length );
							this.page( page ).draw( false );
							}
							
							return this;
							} );

$(document).ready(function() {
		var buyer = $("#table-buyer").DataTable({"deferRender": true, "searching": false,columnDefs: [ {
											targets: [ 2 ],
											 orderData: [ 2, 3 ]
											 }]});

				  var seller = $("#table-seller").DataTable();
				  var buyerrow = buyer.row("#buyer-trade");
				  var sellerrow = seller.row("#seller-trade");

				  // get the page of a given item in order to paginate to it's page on load
				  buyer.page.jumpToData( [buyerrow.data()[0],buyerrow.data()[1],buyerrow.data()[2],buyerrow.data()[3],buyerrow.data()[4]], [0,1,2,3,4] );
				  seller.page.jumpToData( [sellerrow.data()[0],sellerrow.data()[1],sellerrow.data()[2],sellerrow.data()[3],sellerrow.data()[4]], [0,1,2,3,4] );
				  
	$(".panel-heading").click(function(){
		  var btnId = $(this).data('id');
		  jQuery('.panel-body[data-id=' + btnId + ']').slideToggle( "slow", function(){});
	});
});

