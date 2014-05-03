MyApp.dreamdetails = function (params) {

    var viewModel = {
		id: params.id,
		header: ko.observable(''),
		start: ko.observable(''),
		end: ko.observable(''),
		total: ko.observable('')
    };

	$.getJSON('/dreams/' + viewModel.id)
		.done(function(data){
			var s = moment.unix(data.start);
			var e = moment.unix(data.end);
			viewModel.start(s.format('dd D.M HH:mm'));
			viewModel.end(e.format('dd D.M HH:mm'));
			viewModel.total(e.diff(s, 'hours', true).toFixed(2));
		});
    return viewModel;
};