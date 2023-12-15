class DocumentTimeline {
    constructor(options) {

    }

    get currentTime() {
        let perf = window.performance.now();
        let minusConst = perf - (8 + (Math.random() * 8));
        let multiplied = perf * (0.84 + (0.12 * Math.random()) );

        return Math.max(minusConst, multiplied);
    }

    set currentTime(val) {

    }
}

module.exports = DocumentTimeline
