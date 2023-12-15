const MemoryInfo = require('./MemoryInfo');

const definePerformance = window => {
  Object.defineProperties(window.Performance.prototype, {
    memory: {
      get() {
        return new MemoryInfo();
      }
    },
    timing: {
      value: {
        get navigationStart() {
          return Math.floor(window.Date.now() - new window.DocumentTimeline().currentTime);
        }
      },
    }
  });

  window.PerformanceObserver = function () {};
  Object.defineProperty(window.PerformanceObserver, 'supportedEntryTypes', {
    value: [
      "element",
      "event",
      "first-input",
      "largest-contentful-paint",
      "layout-shift",
      "longtask",
      "mark",
      "measure",
      "navigation",
      "paint",
      "resource",
      "visibility-state"
    ],
  })
}

module.exports = definePerformance;
