MyApp.dreamdetails = function (params) {

	var items = ko.observableArray();
	var header = ko.observable('');
	var start = ko.observable('');
	var end = ko.observable('');
	var total = ko.observable('');
	
	var chartOptions = {dataSource: items,
		margin: { top: 0, bottom: 50, left: 25, right: 25 
		},
		commonSeriesSettings: {argumentField: 'Name',
			type: 'pie'},
		series: [
			{ argumentField: 'Name',
			valueField: 'Total',
			tagField: 'Transitions',
			label: {
				visible: true,
				connector: {
					visible: true,
					width: 1
					},
				customizeText: function(item){
					return (item.value/3600).toFixed(1) + 'h\n'
						+ item.point.tag + 'x';
				},
			}	
		}],
		legend: {
			horizontalAlignment: 'center',
			verticalAlignment: 'bottom'
		}};

	var fetchData = function(){
		$.getJSON('/dreams/' + viewModel.id + '/summary')
			.done(function(data){
				items(data);
			});
	};
	
	var fetchDetails = function(){
		$.getJSON('/dreams/' + viewModel.id)
			.done(function(data){
				var s = moment.unix(data.start);
				var e = moment.unix(data.end);
				start(s.format('dd D.M HH:mm'));
				end(e.format('dd D.M HH:mm'));
				total(e.diff(s, 'hours', true).toFixed(2));
				fetchData();
			});
	};
	
	
	
    var viewModel = {
		data: items,
		id: params.id,
		header: header,
		start: start,
		end: end,
		total: total,
		chartOptions: chartOptions,
		fetchDetails: fetchDetails,
		fetchData: fetchData
    };

	fetchDetails();
	
    return viewModel;
};