// noinspection DuplicatedCode

require('canvas');
const fs = require('fs');
const createWindow = require('./browser-env/window');
const hasher = require('./hasher');

const getCanvasForPreset = require('./hardware-fingerprints/canvases');
const getWebGlForPreset = require('./hardware-fingerprints/webgls');
const HardwareFingerprint = require("./hardware-fingerprints/hardware-fingerprint");
const getWebGlParamsForPreset = require("./hardware-fingerprints/webgl_params");

// Parameters that should be read from command line or stdin
let scriptSrc;
let aih;
let historyLength;
let json;
let globalVariables;
let scriptCode;
let html;
{
    // Parse the parameters
    scriptSrc = process.argv[2];
    aih = process.argv[3];
    historyLength = process.argv[4];

    json_str = process.argv[5];
    json = JSON.parse(json_str);

    globalVariables = process.argv[6].split(',')

    let stdin = fs.readFileSync(0, { encoding: 'utf-8' });
    let parts = stdin.split('</html>');
    html = parts[0] + '</html>';
    scriptCode = parts[1];
}

const location = {
    url: 'https://univia.unicajabanco.es/login',
    scriptSrc: scriptSrc,

    // 1 if direct hit to unicajabanco.es/login
    // 2+ if it's not the first website in the Chrome tab, e.g. there could easily be values of 4-6
    historyLength: historyLength,
};

let [spoofedCanvas, spoofedEmptyImage] = getCanvasForPreset(json.canvas);
let spoofedWebGl = getWebGlForPreset(json.webGl.preset);
let hardwareFingerprint = new HardwareFingerprint(spoofedCanvas, spoofedWebGl, spoofedEmptyImage);

let glParams = getWebGlParamsForPreset(json.webGl.preset);

const fingerprint = {
    navigator: {
        isLinux: json.isLinux,
        userAgent: json.navigator.userAgent,
        hardwareConcurrency: json.navigator.hardwareConcurrency, // CPU vCores
        deviceMemory: json.navigator.deviceMemory, // Chrome doesn't show values higher than 8
        languages: json.navigator.languages,
    },
    screen: {
        width: json.screen.width,
        height: json.screen.height,
        isLinux: json.isLinux, // This flags sets OS-dependent params such as screen.availTop/availLeft
    },

    windowKeysForLinux: json.isLinux,

    // Ideally, webGl.vendor + webGl.renderer + webGl.preset + spoofedImages should match each other
    webGl: {
        vendor: json.webGl.vendor,
        renderer: json.webGl.renderer,
        params: glParams,
    },

    spoofedImages: hardwareFingerprint,

    fonts: json.isLinux ? [
        'PMingLiU',
    ] : [
        'Calibri',
        'Marlett',
    ]
};

// Create Window object with spoofed environment
const window = createWindow(html, location, fingerprint, globalVariables);

// The script does not execute instantly, but has some delay
const delay = ms => new Promise(resolve => setTimeout(resolve, ms))

async function main() {
    // Emulate time spent on the first request + script loading + parsing
    // TODO: Better to implement it without delay() but add the value to window.performance
    //  and subtract from Date.now, DocumentTimeline & File.lastModified instead
    await delay(600 + (300 * Math.random()));

    // Execute the script. It will create a global 'reese84interrogator' object
    // that we will later call to collect fingerprint
    eval(scriptCode);

    // We execute only the first part of the script, but the second part
    // also sets its own global variables, so we emulate its presence here
    Object.defineProperties(window, {
        "initializeProtection": {},
        "protectionSubmitCaptcha": {},
        "protectionLoaded": {},
    });

    // Create the object that is responsible for collecting fingerprint
    // `aih` value must be parsed from the input script, search for `return new window`,
    // but it also looks constant, so you might not need to change it unless the
    // script URL changes
    const interrogator = new window.reese84interrogator({
        's': hasher.hash,
        't': new function() {
            this.marks = { total: Date.now() };
            this.measures = {};
            this.start = (name) => { this.marks[name] = Date.now() };
            this.stop = (name) => { this.measures[name] = Date.now() - this.marks[name] };
            this.startInternal = this.stopInternal = () => {};
            this.summary = () => this.measures;
        },
        'aih': aih,
        'at': 1
    })

    // Collect fingerprint
    interrogator.interrogate(
        result => {
            const json_str = JSON.stringify(result);

            // console.log does not output more than 2^17 bytes in one go,
            // so need to split into chunks
            const writeStream = process.stdout;
            const chunks = json_str.match(/.{1,8192}/g);
            chunks.forEach(it => {
                writeStream.write(it);
            })
            writeStream.write('\n');
            writeStream.end();

            process.exit(0);
        },
        err => {
            console.error(err);
            process.exit(1);
        }
    );
}

// noinspection JSIgnoredPromiseFromCall
main()
