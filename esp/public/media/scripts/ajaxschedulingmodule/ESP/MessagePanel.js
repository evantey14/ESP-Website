function MessagePanel(el, initialMessage) {
    this.el = el;

    this.init = function() {
        if(initialMessage) {
            this.addMessage(initialMessage);
        }
    };

    /**
     * Append a line to the message div.
     */
    this.addMessage = function(msg) {
        this.el.append( "<p>" + msg + "</p>");
        this.el.scrollTop(this.el[0].scrollHeight);
    };

    /**
     * Hide the message panel
     */
    this.hide = function() {
        this.el.addClass("ui-helper-hidden");
    };

    /**
     * Show the message panel
     */
    this.show = function() {
        this.el.removeClass("ui-helper-hidden");
    };

    this.init();

}
