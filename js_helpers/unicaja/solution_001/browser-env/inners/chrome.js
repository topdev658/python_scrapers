class Chrome {}

Object.defineProperty(Chrome.prototype, 'runtime', {
  value: {
    OnInstalledReason: {
      CHROME_UPDATE: "chrome_update",
      INSTALL: "install",
      SHARED_MODULE_UPDATE: "shared_module_update",
      UPDATE: "update",
    },
    OnRestartRequiredReason: {
      APP_UPDATE: "app_update",
      OS_UPDATE: "os_update",
      PERIODIC: "periodic",
    },
    PlatformArch: {
      ARM: "arm",
      ARM64: "arm64",
      MIPS: "mips",
      MIPS64: "mips64",
      X86_32: "x86-32",
      X86_64: "x86-64",
    },
    PlatformNaclArch: {
      ARM: "arm",
      MIPS: "mips",
      MIPS64: "mips64",
      X86_32: "x86-32",
      X86_64: "x86-64",
    },
    PlatformOs: {
      ANDROID: "android",
      CROS: "cros",
      FUCHSIA: "fuchsia",
      LINUX: "linux",
      MAC: "mac",
      OPENBSD: "openbsd",
      WIN: "win",
    },
    RequestUpdateCheckStatus: {
      NO_UPDATE: "no_update",
      THROTTLED: "throttled",
      UPDATE_AVAILABLE: "update_available",
    },
    connect: function() {
      "[native code]";
    },
    sendMessage: function() {
      "[native code]";
    },
    id: undefined,
  }
});

function defineChrome(window) {
  // window.Chrome = Chrome;
  // let chrome = new Chrome();
  window.chrome = new Chrome();

  window.chrome.loadTimes = function () {
    "[native code]";
    return {
      get requestTime() {
        return startE / 1000;
      },
      get startLoadTime() {
        return startE / 1000;
      },
      get commitLoadTime() {
        return startE / 1000 + 0.324;
      },
      get finishDocumentLoadTime() {
        return startE / 1000 + 0.498;
      },
      get finishLoadTime() {
        return startE / 1000 + 0.534;
      },
      get firstPaintTime() {
        return startE / 1000 + 0.437;
      },
      get firstPaintAfterLoadTime() {
        return 0;
      },
      get navigationType() {
        return "Other";
      },
      get wasFetchedViaSpdy() {
        return true;
      },
      get wasNpnNegotiated() {
        return true;
      },
      get npnNegotiatedProtocol() {
        return "h3";
      },
      get wasAlternateProtocolAvailable() {
        return false;
      },
      get connectionInfo() {
        return "h3";
      },
    };
  };

  let startE = Date.now();
  window.chrome.csi = function () {
    "[native code]";
    return {
      startE: startE,
      onloadT: startE + 281,
      pageT: 3947.235,
      tran: 15,
    };
  };

  Object.defineProperty(window.chrome, 'app', {
    value: {
      isInstalled: false,
      getDetails: () => {
        "[native code]";
      },
      getIsInstalled: () => {
        "[native code]";
      },
      installState: () => {
        "[native code]";
      },
      runningState: () => {
        "[native code]";
      },
      InstallState: {
        DISABLED: "disabled",
        INSTALLED: "installed",
        NOT_INSTALLED: "not_installed",
      },
      RunningState: {
        CANNOT_RUN: "cannot_run",
        READY_TO_RUN: "ready_to_run",
        RUNNING: "running",
      },
    }
  });
}

module.exports = defineChrome;
