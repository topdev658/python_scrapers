function defineDatabase(window) {
    window.openDatabase = function() {};
}

module.exports = defineDatabase;
