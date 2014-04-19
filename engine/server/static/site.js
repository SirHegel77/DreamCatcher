(function($){

    var RecorderStatus = Backbone.Model.extend({
        urlRoot: '/server/status',
        defaults: {
            signal_power: 0.0,
            sleep_level: 0.0,
            breath: 0.0,
            hb: 0.0,
            state: 0.0
        }
    });

    var RecorderStatusView = Backbone.View.extend({
        initialize: function(){
            this.data = {
	labels : ["January","February","March","April","May","June","July"],
	datasets : [
		{
			fillColor : "rgba(220,220,220,0.5)",
			strokeColor : "rgba(220,220,220,1)",
			pointColor : "rgba(220,220,220,1)",
			pointStrokeColor : "#fff",
			data : [65,59,90,81,56,55,40]
		},
		{
			fillColor : "rgba(151,187,205,0.5)",
			strokeColor : "rgba(151,187,205,1)",
			pointColor : "rgba(151,187,205,1)",
			pointStrokeColor : "#fff",
			data : [28,48,40,19,96,27,100]
		}]};

        this.options =  {
				
	//Boolean - If we show the scale above the chart data			
	scaleOverlay : false,
	
	//Boolean - If we want to override with a hard coded scale
	scaleOverride : false,
	
	//** Required if scaleOverride is true **
	//Number - The number of steps in a hard coded scale
	scaleSteps : null,
	//Number - The value jump in the hard coded scale
	scaleStepWidth : null,
	//Number - The scale starting value
	scaleStartValue : null,

	//String - Colour of the scale line	
	scaleLineColor : "rgba(0,0,0,.1)",
	
	//Number - Pixel width of the scale line	
	scaleLineWidth : 1,

	//Boolean - Whether to show labels on the scale	
	scaleShowLabels : true,
	
	//Interpolated JS string - can access value
	scaleLabel : "<%=value%>",
	
	//String - Scale label font declaration for the scale label
	scaleFontFamily : "'Arial'",
	
	//Number - Scale label font size in pixels	
	scaleFontSize : 12,
	
	//String - Scale label font weight style	
	scaleFontStyle : "normal",
	
	//String - Scale label font colour	
	scaleFontColor : "#666",	
	
	///Boolean - Whether grid lines are shown across the chart
	scaleShowGridLines : true,
	
	//String - Colour of the grid lines
	scaleGridLineColor : "rgba(0,0,0,.05)",
	
	//Number - Width of the grid lines
	scaleGridLineWidth : 1,	

	//Boolean - If there is a stroke on each bar	
	barShowStroke : true,
	
	//Number - Pixel width of the bar stroke	
	barStrokeWidth : 2,
	
	//Number - Spacing between each of the X value sets
	barValueSpacing : 5,
	
	//Number - Spacing between data sets within X values
	barDatasetSpacing : 1,
	
	//Boolean - Whether to animate the chart
	animation : true,

	//Number - Number of animation steps
	animationSteps : 60,
	
	//String - Animation easing effect
	animationEasing : "easeOutQuart",

	//Function - Fires when the animation is complete
	onAnimationComplete : null
	
};
        },
        show: function(){
            this.render();
            this.$el.show();
            if(('chart' in this)==false){
                var ctx = this.$el.find('#statusCanvas')
                    .get(0).getContext('2d');
                this.chart = new Chart(ctx).Bar(this.data, this.options);
            }
            var that = this;
            var update = function(){
                that.model.fetch({success: function(){
                    that.render();
                    
                }});
            };
            update();
            this.timer = setInterval(update, 5000);
        },
        hide: function(){
            clearInterval(this.timer);
            this.$el.hide();
        },
        render: function(){
            this.$el.html('<h1>Recorder status</h1><canvas id="statusCanvas" width="400" height="400"/><p id="power"/><p id="sleep"/><p id="breath"/><p id="hb"/><p id="state"/>');
            this.$el.find('#power').text(this.model.get('signal_power'));
            this.$el.find('#sleep').text(this.model.get('sleep_level'));
            this.$el.find('#breath').text(this.model.get('breath'));
            this.$el.find('#hb').text(this.model.get('hb'));
            this.$el.find('#state').text(this.model.get('state'));
        }
    });

    var Recorder = Backbone.Model.extend({
        urlRoot: '/server',
        defaults: {
            running: false
        }
    });

    var RecorderView = Backbone.View.extend({
        events: {
            'click #toggleRecording': 'toggleRecording',
        },
        initialize: function(){
            _.bindAll(this, 'render');
        },
        show: function(){
            this.$el.show();
            var that = this;
            this.model.fetch({success: function(model){
                that.render();
            }});
        },
        hide: function(){
            this.$el.hide();
        },
        render: function(){
            this.$el.html('<h1>DreamCatcher</h1><button id="toggleRecording"></button>');
            if(this.model.get('running')){
                this.$el.find('#toggleRecording').text('Stop recording');
            } else {
                this.$el.find('#toggleRecording').text('Start recording');
            }
            return this;
        },
        toggleRecording: function(){
            var that = this;
            if(this.model.get('running')){
                this.model.set('running', false);
            } else {
                this.model.set('running', true);
            }
            this.model.save(null, {success: function(model){
                that.render();
            }});
        }
    });

    var MainView = Backbone.View.extend({
        el: $('body'),
        events: {
            'click #nextViewButton': 'showNextView',
            'click #previousViewButton': 'showPreviousView',
        },
        initialize: function(){
            var that = this;
            _.bindAll(this, 'render', 'showView', 
                'showPreviousView', 'showNextView');
            this.recorder = new Recorder();
            this.status = new RecorderStatus();
            this.render();
            this.views = new Array();

            this.views[0] = new RecorderView({
                model: this.recorder,
                el: '#recorderContainer',
            });
            this.views[1] = new RecorderStatusView({
                model: this.status,
                el: '#statusContainer',
            });
            this.showView(0);
        },
        showView: function(index){
            if(index <= 0){
                index = 0;
                this.$el.find('#previousViewButton').hide();
            } else {
                this.$el.find('#previousViewButton').show();
            }; 
            if(index >= this.views.length-1){
                index = this.views.length-1;
                this.$el.find('#nextViewButton').hide();
            } else {
                this.$el.find('#nextViewButton').show();
            };
            if('viewIndex' in this) 
                this.views[this.viewIndex].hide();
            this.viewIndex = index;
            this.views[this.viewIndex].show();
        },
        showNextView: function(){
            this.showView(this.viewIndex + 1);
        },
        showPreviousView: function(){
            this.showView(this.viewIndex - 1);
        },
        render: function(){
            this.$el.append('<button id="previousViewButton">&lt;--</button>');
            this.$el.append('<button id="nextViewButton">--&gt;</button>');
            this.$el.append('<div id="recorderContainer"/>');
            this.$el.append('<div id="statusContainer"/>');
        }
    });

var mv = new MainView();

})(jQuery);
