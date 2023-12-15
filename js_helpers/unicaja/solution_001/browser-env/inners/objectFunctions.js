function defineObjectFunctions(window) {
    const originalGetOwnPropertyNames = window.Object.getOwnPropertyNames;
    window.Object.getOwnPropertyNames = function (obj) {
        const result = originalGetOwnPropertyNames.call(this, obj);
        if (obj === window) {
            return result.filter(it => !it.startsWith('_'));
        }

        return result;
    }
}

module.exports = defineObjectFunctions;
