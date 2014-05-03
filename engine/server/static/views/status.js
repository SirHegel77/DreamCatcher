MyApp.status = function (params) {
	var breath = ko.observable(0);
	var hb = ko.observable(0);
	var signal_power = ko.observable(0);
	var sleep_level = ko.observable(0);
	var state = ko.observable(0);

	var pivot_items = [
			{ title: 'State', options: 
				{value: state,
				scale: {
					startValue: 0,
					endValue: 3,
					minorTick: {visible: false}
				},
				rangeContainer: {
					ranges: [
						{startValue: 0, endValue: 1, color: 'red'},
						{startValue: 1, endValue: 2, color: 'yellow'},
						{startValue: 2, endValue: 3, color: 'green'}
						]
					}}},
			{ title: 'Sleep level', options: 
				{value: sleep_level,
					scale: {
						startValue: -1.0,
						endValue: 1.0
					},
					rangeContainer: {
						ranges: [
							{startValue: -1, endValue: -0.5, color: 'green'},
							{startValue: -0.5, endValue: 0, color: 'yellow'},
							{startValue: 0, endValue: 0.5, color: 'orange'},
							{startValue: 0.5, endValue: 1, color: 'red'}
						]
					}}},
			{ title: 'Heartbeat', options: 
				{value: hb,
					scale: {
						startValue: 0.0,
						endValue: 120.0,
					},
					rangeContainer: {
						ranges: [
							{startValue: 0, endValue: 50, color: 'blue'},
							{startValue: 50, endValue: 70, color: 'green'},
							{startValue: 70, endValue: 90, color: 'orange'},
							{startValue: 90, endValue: 120, color: 'red'}
						]
					}}},
			{ title: 'Breath', options: 
				{value: breath,
					scale: {
						startValue: 0.0,
						endValue: 15.0},
						rangeContainer: {
							ranges: [
								{startValue: 0, endValue: 10, color: 'blue'},
								{startValue: 10, endValue: 13, color: 'green'},
								{startValue: 13, endValue: 15, color: 'red'}
							]
					}}},
			{ title: 'Signal', options: 
				{ value: signal_power, 
					scale: {
						startValue: 3.0,
						endValue: 3.5 }, 
					rangeContainer: {
						ranges: [
							{startValue: 3.0, endValue: 3.18, color: 'blue'},
							{startValue: 3.18, endValue: 3.35, color: 'green'},
							{startValue: 3.35, endValue: 3.5, color: 'red'}
						]
					}}}			
		];
		
	var viewModel = {
		viewShown: function(){
			this.startTimer();
		},
		viewHidden: function(){
			this.stopTimer();
		},
		breath: breath,
		hb: hb,
		signal_power: signal_power,
		sleep_level: sleep_level,
		state: state,
		fetch: function(){
			$.getJSON('/recorder/status')
				.done(function(data){
					breath(data.breath);
					hb(data.hb);
					signal_power(data.signal_power);
					sleep_level(data.sleep_level);
					state(data.state);
				});
		},
		startTimer: function(){
			this.timer = setInterval(this.fetch, 5000);
		},
		stopTimer: function(){
			clearInterval(this.timer);
			this.timer = undefined;
		},		
		pivot_items: pivot_items
    };

	
    return viewModel;
};