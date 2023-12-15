
function defineToString(window, topWindow) {
  const originalToString = window.Function.prototype.toString;
  window.Function.prototype.toString = function toString(...args) {
    switch (this) {
      case originalToString:
      case window.Function.prototype.toString:
      case window.JSON.stringify:
      case window.Object.getOwnPropertyDescriptor:
      case window.Function.prototype.call:
      case window.Function.prototype.apply:
      case window.Function.prototype.bind:
      case window.WebGLRenderingContext.prototype.getParameter:
      case window.navigator.getBattery:
      case window.console.debug:
      case (window.chrome || {}).loadTimes:
      case (topWindow.chrome || {}).loadTimes:
        return `function ${this.name}() { [native code] }`;
    }

    return originalToString.call(this, ...args);
  }
}

module.exports = defineToString;
