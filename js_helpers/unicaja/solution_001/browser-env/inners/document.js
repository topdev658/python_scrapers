
const defineDocument = (window, url) => {
  Object.defineProperties(window.Document.prototype, {
    URL: {
      get: () => {
        return 'https://www.kleinanzeigen.de/';
      }
    },
    hidden: {
      get: () => false,
    },
    cookie: {
      get: () => [
          'somecookie=somevalue'
      ].join('; '),
    }
  })
}

module.exports = defineDocument;
