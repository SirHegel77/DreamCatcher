MyApp.dreams = function (params) {

    var viewModel = {
		dataSource: new DevExpress.data.DataSource({
			pageSize: 10,
			load: function(loadOptions){
				return $.getJSON('/dreams', {
					skip: loadOptions.skip,
					take: loadOptions.take
				});
			},
			map: function(item){
				var m = moment.unix(item.id);
			    return {id: item.id, 
					date: m.format('dddd DD.MM.YYYY'),
					time: m.format('HH:mm')}
			}
		}),
    };
	
    return viewModel;
};