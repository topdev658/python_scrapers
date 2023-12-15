const { CanvasRenderingContext2D } = require('canvas');

function defineCanvas(window, spoofedImages, fonts) {
    let spoofedCanvasWasReturned = false;

    const originalToDataURL = window.HTMLCanvasElement.prototype.toDataURL;
    window.HTMLCanvasElement.prototype.toDataURL = function (type, quality) {
        if (type === 'image/webp') {
            return 'data:image/webp;base64,UklGRmwCAABXRUJQVlA4WAoAAAAwAAAAKwEAYwAASUNDUMgBAAAAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADZBTFBIDwAAAAEHEBERAFCk//8pov+ptQBWUDggZgAAAFAKAJ0BKiwBZAA+bTaZSaQjIqEgSACADYlpbuF2sRtAE9r0VcIMghqqTXbaLhBkENVSa7bRcIMghqqTXbaLhBkENVSa7bRcIMghqqTXbaLhBkENVSa7bRcIL0AA/v/WAAAAAAAAAA==';
        }
        if (this.usedForWebGL) {
            return spoofedImages.spoofedWebgl ? spoofedImages.spoofedWebgl : 'data:image/png; please, provide spoofedWebGLImage';
        }
        if (this.dataWasPut) {
            return spoofedImages.spoofedEmptyImage ? spoofedImages.spoofedEmptyImage : 'data:image/png; please, provide spoofedEmptyImage';
        }

        if (spoofedCanvasWasReturned) {
            console.warn('Spoofed canvas returned twice, probably something does not work!');
        }

        spoofedCanvasWasReturned = true;
        return spoofedImages.spoofedCanvas ? spoofedImages.spoofedCanvas : 'data:image/png; please, provide spoofedCanvasImage';
    }

    const originalCreateImageData = CanvasRenderingContext2D.prototype.createImageData;
    CanvasRenderingContext2D.prototype.createImageData = function (...args) {
        this.canvas.createdImageData = true;
        return originalCreateImageData.call(this, ...args);
    }

    const originalPutImageData = CanvasRenderingContext2D.prototype.putImageData;
    CanvasRenderingContext2D.prototype.putImageData = function (...args) {
        this.canvas.dataWasPut = true;
        return originalPutImageData.call(this, ...args);
    }

    CanvasRenderingContext2D.prototype.measureText = function (text) {
        let font = this.font.split(' ')[1].split(',')[0];

        // Instead of returning anything meaningful,
        // we return { 0, 0, 0... } for 'non-existing fonts'
        // and non-zero object for spoofed ones
        if (fonts.includes(font)) {
            return {
                width: 100,
                actualBoundingBoxAscent: 100,
                actualBoundingBoxDescent: 100,
                actualBoundingBoxLeft: 100,
                actualBoundingBoxRight: 100,
            }
        } else {
            return {
                width: 0,
                actualBoundingBoxAscent: 0,
                actualBoundingBoxDescent: 0,
                actualBoundingBoxLeft: 0,
                actualBoundingBoxRight: 0,
            }
        }
    }
}

module.exports = defineCanvas;
