const defineCurrentScript = (window, scriptSrc) => {
  Object.defineProperty(window.Document.prototype, 'currentScript', {
    get: () => {
      return new Proxy({}, {
        get(target, prop, r) {
          if (prop === 'src') {
            return scriptSrc;
          }
        }
      })
    }
  });
}

module.exports = defineCurrentScript;
