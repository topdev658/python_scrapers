const defineFile = (window) => {
  class File {
    constructor(options, path) {
      this.lastModified = window.Date.now();
      this.path = path;
    }
  }

  window.File = File;
}

module.exports = defineFile;
