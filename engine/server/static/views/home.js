MyApp.home = function (params) {

    var viewModel = {
		viewShown: function(){
			this.fetch();
		},
		viewHidden: function(){
		},
		headerText: ko.observable(''),
		buttonText: ko.observable('Start recording'),
		buttonDisabled: ko.observable(true),
		isRecording: ko.observable(false),
		parse: function(data){
			viewModel.buttonDisabled(false);
			if(data.is_recording){
				viewModel.isRecording(true);
				viewModel.headerText('DreamCatcher is recording.');
				viewModel.buttonText('Stop recording');
			} else {
				viewModel.isRecording(false);
				viewModel.headerText('DreamCatcher is idle.');
				viewModel.buttonText('Start recording');
			}
		},
		post: function(){
			$.ajax({url: '/recorder',
				type: 'PUT',
				data: JSON.stringify({is_recording: !this.isRecording()}),
				contentType: 'application/json',
				success: this.parse});
		},
		fetch: function(){
			$.getJSON('/recorder').done(this.parse);
		}		
    };
	
    return viewModel;
};