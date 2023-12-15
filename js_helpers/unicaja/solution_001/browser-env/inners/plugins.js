const definePlugins = (window) => {
  const chromePDFViewer = Object.create(window.Plugin.prototype);

  const mimeType0 = Object.create(window.MimeType.prototype);
  const mimeType1 = Object.create(window.MimeType.prototype);
  Object.defineProperties(mimeType0, {
    type: {
      get: () => 'application/pdf',
    },
    suffixes: {
      get: () => 'pdf',
    },
    enabledPlugin: {
      get: () => chromePDFViewer,
    }
  });

  Object.defineProperties(mimeType1, {
    type: {
      get: () => 'text/pdf',
    },
    suffixes: {
      get: () => 'pdf',
    },
    enabledPlugin: {
      get: () => chromePDFViewer,
    }
  });

  Object.defineProperties(chromePDFViewer, {
    name: {
      get: () => 'Chrome PDF Viewer',
    },
    description: {
      get: () => 'Portable Document Format',
    },
    0: {
      get: () => mimeType0,
      enumerable: true,
    },
    1: {
      get: () => mimeType1,
      enumerable: true,
    },
    length: {
      get: () => 2,
    },
    filename: {
      get: () => 'internal-pdf-viewer',
    },
  });

  const chromiumPDFViewer = Object.create(window.Plugin.prototype);
  Object.defineProperties(chromiumPDFViewer, {
    name: {
      get: () => 'Chromium PDF Viewer',
    },
    description: {
      get: () => 'Portable Document Format',
    },
    0: {
      get: () => mimeType0,
      enumerable: true,
    },
    1: {
      get: () => mimeType1,
      enumerable: true,
    },
    length: {
      get: () => 2,
    },
    filename: {
      get: () => 'internal-pdf-viewer',
    },
  });

  const edgePDFViewer = Object.create(window.Plugin.prototype);
  Object.defineProperties(edgePDFViewer, {
    name: {
      get: () => 'Microsoft Edge PDF Viewer',
    },
    description: {
      get: () => 'Portable Document Format',
    },
    0: {
      get: () => mimeType0,
      enumerable: true,
    },
    1: {
      get: () => mimeType1,
      enumerable: true,
    },
    length: {
      get: () => 2,
    },
    filename: {
      get: () => 'internal-pdf-viewer',
    },
  });

  const pdfViewer = Object.create(window.Plugin.prototype);
  Object.defineProperties(pdfViewer, {
    name: {
      get: () => 'PDF Viewer',
    },
    description: {
      get: () => 'Portable Document Format',
    },
    0: {
      get: () => mimeType0,
      enumerable: true,
    },
    1: {
      get: () => mimeType1,
      enumerable: true,
    },
    length: {
      get: () => 2,
    },
    filename: {
      get: () => 'internal-pdf-viewer',
    },
  });

  const webKitPDF = Object.create(window.Plugin.prototype);
  Object.defineProperties(webKitPDF, {
    name: {
      get: () => 'WebKit built-in PDF',
    },
    description: {
      get: () => 'Portable Document Format',
    },
    0: {
      get: () => mimeType0,
      enumerable: true,
    },
    1: {
      get: () => mimeType1,
      enumerable: true,
    },
    length: {
      get: () => 2,
    },
    filename: {
      get: () => 'internal-pdf-viewer',
    },
  });

  const pluginArray = Object.create(window.PluginArray.prototype);

  pluginArray['0'] = pdfViewer;
  pluginArray['1'] = chromePDFViewer;
  pluginArray['2'] = chromiumPDFViewer;
  pluginArray['3'] = edgePDFViewer;
  pluginArray['4'] = webKitPDF;

  pluginArray['Chrome PDF Viewer'] = chromePDFViewer;
  pluginArray['Chromium PDF Viewer'] = chromiumPDFViewer;
  pluginArray['Microsoft Edge PDF Viewer'] = edgePDFViewer;
  pluginArray['PDF Viewer'] = pdfViewer;
  pluginArray['WebKit built-in PDF'] = webKitPDF;

  let refreshValue;

  Object.defineProperties(pluginArray, {
    length: {
      get: () => 5,
    },
    item: {
      value: function item(index) {
        if (index > 4294967295) {
          index = index % 4294967296;
        }
        switch (index) {
          case 0:
            return pdfViewer;
          case 1:
            return chromePDFViewer;
          case 2:
            return chromiumPDFViewer;
          case 3:
            return edgePDFViewer;
          case 4:
            return webKitPDF;
          default:
            break;
        }
      },
    },
    refresh: {
      value: function refresh() {
        return refreshValue;
      },
      // set: (value) => {
      //   refreshValue = value;
      // },
    },
    namedItem: {
      value: function namedItem(name) {
        '[native code]';
        switch (name) {
          case 'PDF Viewer':
            return pdfViewer;
          case 'Chrome PDF Viewer':
            return chromePDFViewer;
          case 'Chromium PDF Viewer':
            return chromiumPDFViewer;
          case 'Microsoft Edge PDF Viewer':
            return edgePDFViewer;
          case 'WebKit built-in PDF':
            return webKitPDF;
          default:
            return undefined;
        }
      },
    },
  });

  Object.defineProperty(window.Navigator.prototype, 'plugins', {
    value: pluginArray,
  });
}


module.exports = definePlugins;
