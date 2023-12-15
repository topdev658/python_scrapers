class Plugin {
    constructor(mimeTypes, desc, filename, name) {
        this.mimeTypes = mimeTypes;

        this.mimeTypes.map(function (p){
            Plugin.prototype.__defineGetter__(p.type, function () {
                return p;
            })
        });

        this.description = desc;
        this.filename = filename;

        Plugin.prototype.__defineGetter__('length', function () {
            return Object.keys(this.mimetypes).length;
        });

        this.name = name;
    }
}

class MimeType {
    constructor(desc, suffixes, type) {
        this.description = desc;
        this.suffixes = suffixes;
        this.type = type;
    }
}

class MimeTypeArray {
    constructor() {
        let applicationPdf = new MimeType("Portable Document Format", "pdf", "application/pdf");
        let textPdf = new MimeType("Portable Document Format", "pdf", "text/pdf");

        let mimetypes = [applicationPdf, textPdf];
        let plugin = new Plugin(mimetypes, "Portable Document Format", "internal-pdf-viewer", "PDF Viewer");

        applicationPdf.enabledPlugin = plugin;
        textPdf.enabledPlugin = plugin;

        mimetypes.map((p, i) =>{
            Object.defineProperty(this, i, {
                get() {
                    return p;
                }
            })
        });

        mimetypes.map(p =>{
            Object.defineProperty(this, p.type, {
                get() {
                    return p;
                }
            })
        });

        MimeTypeArray.prototype.__defineGetter__('length', function () {
            return mimetypes.length;
        });
    }

    get[Symbol.toStringTag](){
        return 'MimeTypeArray'
    }

    namedItem(name){
        for (var i=0; i<=this.mimetypes.length; i++) {
            if (this.mimetypes[i].type === name){
                return this.mimetypes[i]
            }
        }
    }

    item(index){
        if (index === 4294967296) {
            index = 0
        }
        this.p = this.mimetypes[index]
        return this.p
    }

    refresh() {

    }
}

module.exports = MimeTypeArray;
