function defineHistory(window, length) {
    Object.defineProperty(window.History.prototype, 'length', {
        get() {
            return length;
        }
    });
}

module.exports = defineHistory;
