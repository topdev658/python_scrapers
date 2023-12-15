function defineConsole(window) {
    window.console.debug = function () {

    }

    Object.defineProperty(window.console.debug, 'name', {
        value: 'debug',
    });
}

module.exports = defineConsole;
