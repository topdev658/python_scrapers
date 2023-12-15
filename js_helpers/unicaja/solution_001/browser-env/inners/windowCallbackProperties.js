
function defineCallbackProperties(window) {
    let props = window.Object.getOwnPropertyNames(window)
        .filter(it => it.startsWith('onb') || it.startsWith("onu"));

    props.forEach(it => {
        delete window[it];
    });

    let obj = {
        get: () => null,
        set: () => {},
        enumerable: true,
        configurable: true,
    }

    Object.defineProperties(window, {
        'onbeforeinstallprompt': obj,
        'onbeforexrselect': obj,
        'onbeforeinput': obj,
        'onblur': obj,
        'onbeforeprint': obj,
        'onbeforeunload': obj,
        'onunhandledrejection': obj,
        'onunload': obj,
        'onbeforematch': obj,
        'onbeforetoggle': obj,
    })
}

module.exports = defineCallbackProperties;
