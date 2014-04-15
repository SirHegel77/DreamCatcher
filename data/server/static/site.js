(function($){

    var Server = Backbone.Model.extend({
        urlRoot: '/server',
        defaults: {
            running: false
        }
    });


    var ServerView = Backbone.View.extend({
        events: {
            'click #toggleRecording': 'toggleRecording',
        },
        initialize: function(){
            _.bindAll(this, 'render');
            var that = this;
            this.model.fetch({success: function(model){
                that.render();
            }});

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
        initialize: function(){
            var that = this;
            _.bindAll(this, 'render');
            this.server = new Server();
            this.render();
            this.serverView = new ServerView({
                model: this.server,
                el: '#serverContainer',
            });
        },

        render: function(){
            this.$el.html('<div id="serverContainer"></div>');
        }
    });

var mv = new MainView();

})(jQuery);
