
function defineVisualViewport(window) {
    window.VisualViewport = function () {};
    window.visualViewport = new window.VisualViewport();
    Object.defineProperties(window.VisualViewport.prototype, {
        'height': {
            get: () => window.innerHeight,
        },
        'offsetLeft': {
            get: () => 0,
        },
        'offsetTop': {
            get: () => 0,
        },
        'onresize': {
            get: () => null,
        },
        'onscroll': {
            get: () => null,
        },
        'pageLeft': {
            get: () => 0,
        },
        'pageTop': {
            get: () => 0,
        },
        'scale': {
            get: () => 1,
        },
        'width': {
            get: () => window.innerWidth,
        },
    });
}

module.exports = defineVisualViewport;
