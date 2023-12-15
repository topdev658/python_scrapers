const jsdom = require('jsdom');
const { JSDOM } = jsdom;

const definePlugins = require('./inners/plugins');
const defineNavigator = require('./inners/navigator');
const defineXMLHttpRequest = require('./inners/XMLHttpRequest');
const defineCurrentScript = require('./inners/document/currentScript');
const defineHTMLMediaElement = require('./inners/element/HTMLMediaElement');
const defineScreen = require('./inners/screen');
const defineIndexedDB = require('./inners/indexedDB');
const defineWebGL = require('./inners/webgl');
const definePerformance = require('./inners/performance');
const defineEvents = require('./inners/events');
const defineWebRTC = require("./inners/webrtc");
const defineSpeechSynthesis = require("./inners/speechSynthesis");
const defineDocument = require("./inners/document");
const defineFile = require("./inners/File");
const defineAddEventListener = require('./inners/eventListener');
const defineIFrame = require('./iframe');

// Unicaja
const DocumentTimeline = require('./inners/document/DocumentTimeline');
const defineCanvas = require('./inners/canvas');
const defineConsole = require('./inners/console');
const defineToString = require('./inners/toString');
const defineCallbackProperties = require('./inners/windowCallbackProperties');
const defineProperties = require('./inners/windowProperties');
const defineVisualViewport = require('./inners/visualViewport');
const defineObjectFunctions = require('./inners/objectFunctions');
const defineChrome = require('./inners/chrome');
const defineHistory = require('./inners/history');
const defineDatabase = require('./inners/database');

function createWindow(html, location, fingerprint, globalVariables) {
  const topWindow = new JSDOM(html, {
    url: location.url,
  }).window;

  // Everything that is both on Window and IFrames
  function setupWindow(window, iframe) {
    defineCurrentScript(window, location);
    definePlugins(window);
    defineNavigator(window, fingerprint.navigator);
    defineXMLHttpRequest(window);
    defineCurrentScript(window, location.scriptSrc);
    defineHTMLMediaElement(window);
    defineScreen(window, fingerprint.screen);
    defineIndexedDB(window);
    defineDatabase(window);
    defineWebGL(window, fingerprint.webGl);
    definePerformance(window);
    defineEvents(window);
    defineWebRTC(window);
    defineSpeechSynthesis(window);
    defineDocument(window, location.url);
    defineFile(window);
    defineAddEventListener(window);
    defineIFrame(window, setupWindow);

    delete window.SharedArrayBuffer;

    // Unicaja
    window.DocumentTimeline = DocumentTimeline;
    defineCanvas(window, fingerprint.spoofedImages, fingerprint.fonts);
    defineConsole(window);
    defineToString(window, topWindow);
    defineCallbackProperties(window);
    defineVisualViewport(window);
    defineObjectFunctions(window);
    defineHistory(window, location.historyLength);

    if (window !== topWindow) {
      // If it's top level iframe - define chrome object on it
      if (Array.from(topWindow.document.querySelectorAll('iframe')).includes(iframe)) {
        defineChrome(window)
      }
    }
  }

  setupWindow(topWindow);

  // Exclusive to top window
  defineChrome(topWindow);

  // Defined properties must be the last
  defineProperties(topWindow, globalVariables, fingerprint.windowKeysForLinux);

  global.window = topWindow;
  global.document = topWindow.document;
  global.screen = topWindow.screen;
  global.navigator = topWindow.navigator;
  global.chrome = topWindow.chrome;

  return topWindow;
}

module.exports = createWindow;
