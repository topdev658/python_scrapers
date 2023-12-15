function defineIFrame(window, setupFunc) {
    Object.defineProperty(window.HTMLIFrameElement.prototype, 'loading', {
        get() {},
        set() {}
    })

    const originalGetter = Object.getOwnPropertyDescriptor(window.HTMLIFrameElement.prototype, 'contentWindow').get;
    Object.defineProperty(window.HTMLIFrameElement.prototype, 'contentWindow', {
        get() {
            let original = originalGetter.call(this);
            if (!this.wasSetup) {
                setupFunc(original, this);
                this.wasSetup = true;
            }
            return original;
        }
    });
}

module.exports = defineIFrame;
