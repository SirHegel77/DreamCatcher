(function() {
    "use strict";

    var MyApp = window.MyApp = { };
    
    // Uncomment the line below to disable platform-specific look and feel and to use the Generic theme for all devices
    // DevExpress.devices.current({ platform: "generic" });

    $(function() {
        MyApp.app = new DevExpress.framework.html.HtmlApplication({
            namespace: MyApp,
            commandMapping: {
				"ios-header-toolbar": {
					commands: [
						{id: 'search', location: 'right', showText: false}
					]
				},
				"android-footer-toolbar": {
					commands: [
						{id: 'search', location: 'center', showText: false}
					]
				},
				"tizen-footer-toolbar": {
					commands: [
						{id: 'search', location: 'center', showText: false}
					]
				},
				"generic-header-toolbar": {
					commands: [
						{id: 'search', location: 'right', showText: false}
					]
				},
				"win8-phone-appbar": {
					commands: [
						{id: 'search', location: 'center', showText: true}
					]
				},
			},
            navigationType: "slideout",
            navigation: [
              {
                title: "Home",
                action: "#home",
                icon: "home"
              },
			  {
				title: "Status",
				action: "#status",
				icon: "chart"
			  },
              {
                title: "Dreams",
                action: "#dreams",
                icon: "info"
              }
            ]
        });
        
        MyApp.app.router.register(":view/:id", { view: "home", id: undefined });
        MyApp.app.navigate();
    });
    
})();