// noinspection DuplicatedCode

require('canvas');
const fs = require('fs');
const createWindow = require('./browser-env/window');
const hasher = require('./hasher');

const getCanvasForPreset = require('./hardware-fingerprints/canvases');
const getWebGlForPreset = require('./hardware-fingerprints/webgls');
const getWebGlParamsForPreset = require('./hardware-fingerprints/webgl_params');
const HardwareFingerprint = require("./hardware-fingerprints/hardware-fingerprint");

// Parameters that should be read from command line or stdin
let scriptSrc;
let aih;
let historyLength;
let json;
let globalVariables;
let scriptCode;
let html;
{
    // Script parameters
    scriptSrc = 'https://univia.unicajabanco.es/nq-vent-man-macd-and-and-macbeth-gayne-i-not-of-';
    aih = 'cWGPGNo0iG5PXchwZU63i1/tuXyk4UX4IdoHPCnDHa8=';
    historyLength = 1;

    // Example Linux
    // json = {
    //     isLinux: true,
    //     navigator: {
    //         userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    //         hardwareConcurrency: 24,
    //         deviceMemory: 8,
    //         languages: ['en-US', 'en'],
    //     },
    //     screen: {
    //         width: 3840,
    //         height: 2160,
    //     },
    //     canvas: 'linux_001',
    //     webGl: {
    //         vendor: 'Google Inc. (NVIDIA Corporation)',
    //         renderer: 'ANGLE (NVIDIA Corporation, NVIDIA GeForce RTX 3070/PCIe/SSE2, OpenGL 4.5.0)',
    //         preset: 'linux_nvidia_001',
    //     }
    // }

    // Example Windows
    json = {
        isLinux: false,
        navigator: {
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            hardwareConcurrency: 24,
            deviceMemory: 8,
            languages: ['en-US', 'en'],
        },
        screen: {
            width: 3840,
            height: 2160,
        },
        canvas: 'windows_001',
        webGl: {
            vendor: 'Google Inc. (NVIDIA Corporation)',
            renderer: 'ANGLE (NVIDIA Corporation, NVIDIA GeForce RTX 3070/PCIe/SSE2, OpenGL 4.5.0)',
            preset: 'windows_nvidia_001',
        }
    }

    globalVariables = [
        'a1_0x4d5',
        'reese84',
        'a1_0xcd60',
    ];

    // HTML of the page is needed because the script checks elements on the page,
    // but you can leave it untouched as long as the script URL does not change
    // and stays the same: nq-vent-man-macd-and-and-macbeth-gayne-i-not-of-
    html = fs.readFileSync('index.html', { encoding: 'utf-8' });

    // The code of the fingerprinting function
    scriptCode = fs.readFileSync(`input-002-deobf.js`, { encoding: 'utf-8' });
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
        userAgent: json.navigator.userAgent,
        hardwareConcurrency: json.navigator.hardwareConcurrency, // CPU vCores
        deviceMemory: json.navigator.deviceMemory, // Chrome doesn't show values higher than 8
        platform: json.isLinux ? 'Linux x86_64' : 'Win32', // Win32, Linux x86_64
        languages: json.navigator.languages,
    },
    screen: {
        width: json.screen.width,
        height: json.screen.height,
        isLinux: json.isLinux, // This flags sets OS-dependent params such as screen.availTop/availLeft
    },

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

    function checkPlugins() {
        function getTopFrame() {
            let iframe = window.document.createElement('IFRAME');
            iframe.style.display = 'none';
            window.document.body.appendChild(iframe);
            return iframe;
        }

        let frame = getTopFrame();
        let contentWindow = frame.contentWindow;
        let nav = contentWindow.navigator;

        let plugins = [];

        let i = 0;
        let length = nav.plugins.length;
        while (i < length) {
            let plugin = nav.plugins[i];
            if (plugin) {
                plugins.push(plugin);
            }
            i++;
        }

        plugins.sort(function (p1, p2) {
            let res = 0;
            if (p1.name > p2.name) {
                res = 1;
            } else if (p1.name < p2.name) {
                res = -1;
            }
            return res;
        });

        for (let index in plugins) {
            let plugin = plugins[index];
            if (plugins.hasOwnProperty(index)) {
                console.log('Plugin:', plugin.name);
                console.log('Description:', plugin.description);

                for (let key in plugin) {
                    let prop = plugin[key];
                    if (plugin.hasOwnProperty(key)) {
                        if (prop) {
                            console.log(key + ':', prop.type + ',', 'suffixes:', prop.suffixes);
                        }
                    }
                }
            }

            console.log('');
        }
    }

    checkPlugins();

    return;

    // Collect fingerprint
    interrogator.interrogate(
        result => {
            console.log(JSON.stringify(result));
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
