const NetworkInformation = require('./NetworkInformation');

const MimeTypeArray = require('./navigator/MimeTypeArray')

const definePermissions = window => {
  class PermissionStatus {
    constructor(name) {
      this.name_ = name;
      this.onchangeCallBack = null;
    }

    get name() {
      return this.name_
    }

    get onchange() {
      return this.onchangeCallBack;
    }

    set onchange(value) {
      this.onchangeCallBack = value;
      this.onchangeCallBack();
    }

    get state() {
      return 'denied'
    }
  }
  window.PermissionStatus = PermissionStatus;

  window.Permissions = function() {}
  window.Permissions.prototype.query = async function(permission) {
    const { name } = permission;
    return Promise.resolve(new window.PermissionStatus(name));
  }
}

class Brave {
  constructor() {}

  async isBrave() {
    return new Promise.resolve(true);
  }
}

const defineNavigator = (window, params) => {
  definePermissions(window);


  let plugins = window.Object.getOwnPropertyDescriptor(window.Navigator.prototype, 'plugins');
  for (let key in window.Navigator.prototype) {
    delete window.Navigator.prototype[key];
  }

  Object.defineProperties(window.Navigator.prototype, {
    vendorSub: {
      value: "",
      enumerable: true,
    },
    productSub: {
      value: "20030107",
      enumerable: true,
    },
    vendor: {
      get: () => "Google Inc.",
      enumerable: true,
    },
    maxTouchPoints: {
      get: () => 0,
      enumerable: true,
    },
    scheduling: {
      get: () => {
        return {};
      },
      enumerable: true,
    },
    userActivation: {
      get: () => {
        return {};
      },
      enumerable: true,
    },
    doNotTrack: {
      get: () => null,
      enumerable: true,
    },
    geolocation: {
      get: () => {
        return {};
      },
      enumerable: true,
    },
    connection: {
      get: () => {
        return new NetworkInformation();
      },
      enumerable: true,
    },
    plugins: plugins,
    mimeTypes: {
      get: () => new MimeTypeArray(),
      enumerable: true,
    },
    pdfViewerEnabled: {
      get: () => {
        return {};
      },
      enumerable: true,
    },
    webkitTemporaryStorage: {
      get: () => {
        return {};
      },
      enumerable: true,
    },
    webkitPersistentStorage: {
      get: () => {
      },
      enumerable: true,
    },
    hardwareConcurrency: {
      get: () => params.hardwareConcurrency,
      enumerable: true,
    },
    cookieEnabled: {
      get: () => {
        return true;
      },
      enumerable: true,
    },
    appCodeName: {
      get: () => {
      },
      enumerable: true,
    },
    appName: {
      get: () => {
      },
      enumerable: true,
    },
    appVersion: {
      get: () => params.userAgent.substring(8),
      enumerable: true,
    },
    platform: {
      get: () => params.isLinux ? 'Linux x86_64' : 'Win32',
      enumerable: true,
    },
    product: {
      get: () => "Gecko",
      enumerable: true,
    },
    userAgent: {
      get: () => params.userAgent,
      enumerable: true,
    },
    language: {
      get: () => params.languages[0],
      enumerable: true,
    },
    languages: {
      get: () => params.languages,
      enumerable: true,
    },
    onLine: {
      get: () => true,
      enumerable: true,
    },
    webdriver: {
      get: () => false,
      enumerable: true,
    },
    getGamepads: {
      get: () => {
      },
      enumerable: true,
    },
    javaEnabled: {
      get: () => false,
      enumerable: true,
    },
    sendBeacon: {
      get: () => {
      },
      enumerable: true,
    },
    vibrate: {
      value: function vibrate() {
      },
      enumerable: true,
    },
  });

  if (!params.isLinux) {
    Object.defineProperties(window.Navigator.prototype, {
      bluetooth: {
        get: () => {
          return {};
        },
        enumerable: true,
      },
    });
  }

  Object.defineProperties(window.Navigator.prototype, {
    clipboard: {
      get: () => {
        return {};
      },
      enumerable: true,
    },
    credentials: {
      get: () => {
      },
      enumerable: true,
    },
    keyboard: {
      get: () => {
      },
      enumerable: true,
    },
    managed: {
      get: () => {
      },
      enumerable: true,
    },
    mediaDevices: {
      get: () => {
      },
      enumerable: true,
    },
    storage: {
      get: () => {
      },
      enumerable: true,
    },
    serviceWorker: {
      get: () => {
      },
      enumerable: true,
    },
    virtualKeyboard: {
      get: () => {
      },
      enumerable: true,
    },
    wakeLock: {
      get: () => {
      },
      enumerable: true,
    },
    deviceMemory: {
      get: () => params.deviceMemory,
      enumerable: true,
    },
    ink: {
      get: () => {
      },
      enumerable: true,
    },
    hid: {
      get: () => {
      },
      enumerable: true,
    },
    locks: {
      get: () => {
      },
      enumerable: true,
    },
    gpu: {
      get: () => {
      },
      enumerable: true,
    },
    mediaCapabilities: {
      get: () => {
      },
      enumerable: true,
    },
    mediaSession: {
      get: () => {
      },
      enumerable: true,
    },
    permissions: {
      get: () => {
        return {
          query: (data) => {
            const granted = [
              'midi',
              'background_sync',
              'magnetometer',
              'accelerometer',
              'gyroscope',
              'clipboard_write',
              'payment_handler',
            ]
            const prompted = [
              'geolocation',
              'notifications',
              'video_capture',
              'audio_capture',
              'durable_storage',
              'clipboard_read',
            ]
            const name = data.name;
            if (name in granted) {
              return Promise.resolve({
                name: name,
                onchange: null,
                state: "granted"
              });
            }

            if (name in prompted) {
              return Promise.resolve({
                name: name,
                onchange: null,
                state: "prompt"
              });
            }

            switch (name) {
              case 'push':
                return Promise.reject(
                  new DOMException("Failed to execute 'query' on 'Permissions': Push Permission without userVisibleOnly:true isn't supported yet.")
                );
              case 'ambient-light-sensor':
                return Promise.reject(
                  new TypeError("Failed to execute 'query' on 'Permissions': GenericSensorExtraClasses flag is not enabled.")
                );
              case 'accessibility-events':
                return Promise.reject(
                  new TypeError("Failed to execute 'query' on 'Permissions': Accessibility Object Model is not enabled.")
                );
              default:
                return Promise.reject(
                  new TypeError(`Failed to execute 'query' on 'Permissions': Failed to read the 'name' property from 'PermissionDescriptor': The provided value '${name}' is not a valid enum value of type PermissionName.`)
                )
            }
          }
        }
      },
      enumerable: true,
    },
    presentation: {
      get: () => {
      },
      enumerable: true,
    },
    usb: {
      get: () => {
      },
      enumerable: true,
    },
    xr: {
      get: () => {
      },
      enumerable: true,
    },
    serial: {
      get: () => {
      },
      enumerable: true,
    },
    windowControlsOverlay: {
      get: () => {
      },
      enumerable: true,
    },
    userAgentData: {
      get: () => {
      },
      enumerable: true,
    },
    adAuctionComponents: {
      get: () => {
      },
      enumerable: true,
    },
    runAdAuction: {
      get: () => {
      },
      enumerable: true,
    },
    canLoadAdAuctionFencedFrame: {
      get: () => {
      },
      enumerable: true,
    },
  });

  if (!params.isLinux) {
    Object.defineProperties(window.Navigator.prototype, {
      canShare: {
        get: () => {},
        enumerable: true,
      },
      share: {
        get: () => {},
        enumerable: true,
      },
    });
  }

  Object.defineProperties(window.Navigator.prototype, {
    clearAppBadge: {
      get: () => {},
      enumerable: true,
    },
    getBattery: {
      value: async function getBattery() {
        return new Promise((rs, rj) => {
          setTimeout(() => {
            rs({
              charging: true,
              chargingTime: 0,
              dischargingTime: Infinity,
              level: 1,
              onchargingchange: null,
              onchargingtimechange: null,
              ondischargingtimechange: null,
              onlevelchange: null,
            })
          }, 100);
        })
      },
      enumerable: true,
    },
    getUserMedia: {
      get: () => {},
      enumerable: true,
    },
    requestMIDIAccess: {
      get: () => {},
      enumerable: true,
    },
    requestMediaKeySystemAccess: {
      value: async function requestMediaKeySystemAccess(params) {
        return new window.Promise((rs, rj) => {
          rs(true);
        });
      },
      enumerable: true,
    },
    setAppBadge: {
      get: () => {},
      enumerable: true,
    },
    webkitGetUserMedia: {
      get: () => {},
      enumerable: true,
    },
    deprecatedReplaceInURN: {
      get: () => {},
      enumerable: true,
    },
    deprecatedURNToURL: {
      get: () => {},
      enumerable: true,
    },
    getInstalledRelatedApps: {
      get: () => {},
      enumerable: true,
    },
    joinAdInterestGroup: {
      get: () => {},
      enumerable: true,
    },
    leaveAdInterestGroup: {
      get: () => {},
      enumerable: true,
    },
    updateAdInterestGroups: {
      get: () => {},
      enumerable: true,
    },
    registerProtocolHandler: {
      get: () => {},
      enumerable: true,
    },
    unregisterProtocolHandler: {
      get: () => {},
      enumerable: true,
    },
  });
  window.clientInformation = window.navigator;
};

module.exports = defineNavigator;
