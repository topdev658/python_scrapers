
const defineCanPlayType = window => {

  const parseInput = arg => {
    const [mime, codecStr] = arg.trim().split(';')
    let codecs = []
    if (codecStr && codecStr.includes('codecs="')) {
      codecs = codecStr
        .trim()
        .replace(`codecs="`, '')
        .replace(`"`, '')
        .trim()
        .split(',')
        .filter(x => !!x)
        .map(x => x.trim())
    }
    return {
      mime,
      codecStr,
      codecs
    }
  }

  const canPlayType = {
    // Intercept certain requests
    apply: function(target, ctx, args) {
      if (!args || !args.length || !args[0].length)
        return target.apply(ctx, args)

      const { mime, codecs } = parseInput(args[0])

      if (!codecs.length) {
        switch (mime.toLowerCase()) {
          case 'audio/mpeg':
          case 'audio/aac':
            return 'probably';
          case 'audio/x-m4a':
            return 'maybe';
        }
      }

      if (mime === 'video/mp4') {
        if (codecs.includes('avc1.42E01E') || codecs.includes('avc1.4D401E'))
          return 'probably'
      }

      if (mime === 'video/ogg') {
        if (codecs.includes('theora'))
          return 'probably'
      }

      if (mime === 'audio/ogg') {
        if (codecs.includes('vorbis'))
          return 'probably'
      }

      if (mime === 'video/webm') {
        if (codecs.includes('vp8') && codecs.includes('vorbis'))
          return 'probably'
      }

      if (mime === 'audio/wav') {
        if (codecs.includes('1'))
          return 'probably'
      }

      return target.apply(ctx, args)
    }
  }

  window.HTMLMediaElement.prototype.canPlayType = new Proxy(
    window.HTMLMediaElement.prototype.canPlayType,
    canPlayType
  )
}

const defineHTMLMediaElement = window => {
  defineCanPlayType(window);
}

module.exports = defineHTMLMediaElement;
