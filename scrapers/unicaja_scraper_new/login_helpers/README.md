# Unicaja bypass

### Project structure

Some explanation of the "big dirty zip with unnecessary files"
```sh
    .
    ├── resources/                                      # 
    │   └── gpu.json                                    # All WebGL Vendors and Renderers, you might want to use it
    │                                                   #
    │── solution_001/                                   # JS bypass
    │   ├── browser-env/ & hardware-fingerprints/       # Inner files for spoofing JS APIs
    │   ├── tests/                                      # All tests Incapsula performs, deobfuscated and isolated
    │   ├── hasher.js                                   # Their hasher for encryption
    │   ├── index.html                                  # HTML for testing
    │   ├── input-002-deobf.js                          # Fingerprinting script for testing
    │   ├── package.json & package-lock.json            # For npm to install deps with `npm install` command
    │   ├── unicaja.js                                  # Script to run from Python
    │   └── unicaja_test.js                             # Script to test with
    │                                                   #
    │── tests/                                          # Python tests for parsing & generation
    │── unicaja.py                                      # Main file for running
    └── ...                                             # Other Python files
```

### Setting up
1. `cd solution_001 && npm install` - should install JS dependencies. If fails then manually install
`npm install canvas && npm install jsdom`
2. Set `proxy_str` in `unicaja.py`
3. Run `unicaja.py`

> You probably want to add `solution_001/node_modules` to `.gitignore`

### Current fingerprints

##### Canvas:
* `linux_001` - Ubuntu
* `windows_001` - Windows
* `windows_002` - Windows VM

##### WebGL:
* `linux_nvidia_001` - Ubuntu with NVIDIA GPU
* `windows_nvidia_001` - Windows with NVIDIA GPU
* `windows_google_001` - Windows VM with Google Swiftshader

> Usually you should not use WebGL fingerprints with Google Swiftshader, as they always
> indicate that the PC is a virtual machine, thus it might have a lower trust

### Adding new fingerprints

> Paths are relative to `solution_001` dir

##### To add a new Canvas fingerprint:

1. Open `tests/input-tests-001.js` and locate the function `checkCanvasImage`.
2. Open the target machine where you want to collect a fingerprint and run the function
in Chrome's console. The output will have two images, the first one will be much bigger
than the second one
3. Open `hardware-fingerprints/canvases.js`
4. Add a new case clause, e.g. `windows_012`, and return `[first_img, second_img]` in it

##### To add a new WebGL fingerprint:

First you need to collect WebGL Image:
1. Open `tests/input-tests-001.js` and locate the function `checkGlImage`.
2. Open the target machine where you want to collect a fingerprint and run the function in
Chrome's console. The output will have two images, the first one will be much bigger than
the second one. The second one is actually useless, but the first one is the WebGL Image
3. Open `hardware-fingerprints/webgls.js`
4. Add a new case clause, e.g. `windows_intel_034`, and return `first_img` in it

Then you need to collect WebGL Extensions and Parameters:
1. Open `tests/input-tests-001.js` and locate the function `checkGlParams`.
2. Open the target machine and run it in a console. The output will have an array of
extensions and a big object with params
3. Copy-pasta these into `hardware-fingerprints/webgl_params.js` and add a new case clause,
and do not forget to change parameters that are arrays (e.g. `MAX_VIEWPORT_DIMS`) into
`Int32Array` or `FloatArray` as they are in the existing fingerprints.

> The name of the WebGL fingerprint (e.g. `windows_intel_034`) must be the same for both
> WebGL Image and WebGL Extensions & Parameters