const defineScreenOrientation = window => {
  class ScreenOrientation {
    constructor() {
      this.onchange = null;
    }

    get angle() {
      return 0;
    }

    get type() {
      return 'landscape-primary';
    }
  }

  window.ScreenOrientation = ScreenOrientation;
}

const defineScreen = (window, screen) => {
  defineScreenOrientation(window);

  let isLinux = screen.isLinux;

  let leftBarWidth = isLinux ? 72 : 0;
  let topBarHeight = isLinux ? 27 : 0;
  let taskBarHeight = isLinux ? 0 : 40;

  let addressBarAndBookmarksHeight = isLinux ? 136 : 143;

  Object.defineProperties(window.Screen.prototype, {
    'availHeight': {
      get: () => screen.height - topBarHeight - taskBarHeight,
    },
    'availLeft': {
      get: () => leftBarWidth,
    },
    'availTop': {
      get: () => topBarHeight
    },
    'availWidth': {
      get: () => screen.width - leftBarWidth,
    },
    'colorDepth': {
      get: () => 24
    },
    'height': {
      get: () => screen.height
    },
    'isExtended': {
      get: () => false
    },
    'pixelDepth': {
      get: () => 24
    },
    'width': {
      get: () => screen.width
    },
    'orientation': {
      get() {
        return new window.ScreenOrientation();
      }
    },
    'onchange': {
      get() {
        return null;
      }
    },
  });

  Object.defineProperties(window, {
    innerHeight: {
      get() {
        return screen.height - addressBarAndBookmarksHeight;
      }
    },
    innerWidth: {
      get() {
        return screen.width;
      }
    },
    outerHeight: {
      get() {
        return screen.height - topBarHeight - taskBarHeight;
      }
    },
    outerWidth: {
      get() {
        return screen.width;
      }
    },
    devicePixelRatio: {
      get() {
        return 1;
      }
    }
  });

}

module.exports = defineScreen;
