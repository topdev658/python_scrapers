
const defineWebGL = (window, params) => {
  const vendor = params.vendor;
  const renderer = params.renderer;

  const extensions = params.params[0];
  const glParams = params.params[1];

  class WebGLDebugRendererInfo {
    constructor() {}

    get UNMASKED_RENDERER_WEBGL() {
      return 37446;
    }
    get UNMASKED_VENDOR_WEBGL() {
      return 37445;
    }
  }

  const glDebugInfo = new WebGLDebugRendererInfo();

  class WebGLShader {
    constructor() {}
  }

  class WebGLProgram {
    constructor() {}
  }

  class WebGLRenderingContext {
    constructor(canvas) {
      this.canvas = canvas;

      this.COMPILE_STATUS = 35713;
      this.COLOR_BUFFER_BIT = 16384;
      this.ARRAY_BUFFER = 34962;
      this.STATIC_DRAW = 35044;

      this.ALIASED_LINE_WIDTH_RANGE = 33902;
      this.ALIASED_POINT_SIZE_RANGE = 33901;
      this.ALPHA_BITS = 3413;
      this.BLUE_BITS = 3412;
      this.DEPTH_BITS = 3414;
      this.GREEN_BITS = 3411;
      this.MAX_COMBINED_TEXTURE_IMAGE_UNITS = 35661;
      this.MAX_CUBE_MAP_TEXTURE_SIZE = 34076;
      this.MAX_FRAGMENT_UNIFORM_VECTORS = 36349;
      this.MAX_RENDERBUFFER_SIZE = 34024;
      this.MAX_TEXTURE_IMAGE_UNITS = 34930;
      this.MAX_TEXTURE_SIZE = 3379;
      this.MAX_VARYING_VECTORS = 36348;
      this.MAX_VERTEX_ATTRIBS = 34921;
      this.MAX_VERTEX_TEXTURE_IMAGE_UNITS = 35660;
      this.MAX_VERTEX_UNIFORM_VECTORS = 36347;
      this.MAX_VIEWPORT_DIMS = 3386;
      this.RED_BITS = 3410;
      this.RENDERER = 7937;
      this.SHADING_LANGUAGE_VERSION = 35724;
      this.STENCIL_BITS = 3415;
      this.VENDOR = 7936;
      this.VERSION = 7938;

      this.VERTEX_SHADER = 35633;
      this.FRAGMENT_SHADER = 35632;
      this.LINK_STATUS = 35714;

      this.HIGH_FLOAT = 36338;
      this.MEDIUM_FLOAT = 36337;
      this.LOW_FLOAT = 36336;
      this.HIGH_INT = 36341;
      this.MEDIUM_INT = 36340;
      this.LOW_INT = 36339;

      this.MAX_TEXTURE_MAX_ANISOTROPY_EXT = 34047;

      this.items = {};
      this.id = 0;
      this.boundTextures = {};
    }

    createBuffer() {
      let id = this.id++;
      this.items[id] = {
        which: 'buffer',
      };
      return {};
    };

    getExtension(ex) {
      if (ex === 'WEBGL_debug_renderer_info') {
        return glDebugInfo;
      }

      if (ex === 'EXT_texture_filter_anisotropic') {
        return {
          MAX_TEXTURE_MAX_ANISOTROPY_EXT: this.MAX_TEXTURE_MAX_ANISOTROPY_EXT,
        }
      }
      return 1;
    }

    deleteBuffer() {};
    bindBuffer() {};
    bufferData() {};
    getParameter(pname) {
      if (this === null) {
        throw TypeError('Illegal invocation');
      }

      switch (pname) {
        case 37445: return vendor;
        case 37446: return renderer;

        case this.ALIASED_LINE_WIDTH_RANGE: return glParams.ALIASED_LINE_WIDTH_RANGE;
        case this.ALIASED_POINT_SIZE_RANGE: return glParams.ALIASED_POINT_SIZE_RANGE;
        case this.ALPHA_BITS: return glParams.ALPHA_BITS;
        case this.BLUE_BITS: return glParams.BLUE_BITS;
        case this.DEPTH_BITS: return glParams.DEPTH_BITS;
        case this.GREEN_BITS: return glParams.GREEN_BITS;
        case this.MAX_TEXTURE_MAX_ANISOTROPY_EXT: return glParams.MAX_TEXTURE_MAX_ANISOTROPY_EXT;
        case this.MAX_COMBINED_TEXTURE_IMAGE_UNITS: return glParams.MAX_COMBINED_TEXTURE_IMAGE_UNITS;
        case this.MAX_CUBE_MAP_TEXTURE_SIZE: return glParams.MAX_CUBE_MAP_TEXTURE_SIZE;
        case this.MAX_FRAGMENT_UNIFORM_VECTORS: return glParams.MAX_FRAGMENT_UNIFORM_VECTORS;
        case this.MAX_RENDERBUFFER_SIZE: return glParams.MAX_RENDERBUFFER_SIZE;
        case this.MAX_TEXTURE_IMAGE_UNITS: return glParams.MAX_TEXTURE_IMAGE_UNITS;
        case this.MAX_TEXTURE_SIZE: return glParams.MAX_TEXTURE_SIZE;
        case this.MAX_VARYING_VECTORS: return glParams.MAX_VARYING_VECTORS;
        case this.MAX_VERTEX_ATTRIBS: return glParams.MAX_VERTEX_ATTRIBS;
        case this.MAX_VERTEX_TEXTURE_IMAGE_UNITS: return glParams.MAX_VERTEX_TEXTURE_IMAGE_UNITS;
        case this.MAX_VERTEX_UNIFORM_VECTORS: return glParams.MAX_VERTEX_UNIFORM_VECTORS;
        case this.MAX_VIEWPORT_DIMS: return glParams.MAX_VIEWPORT_DIMS;
        case this.RED_BITS: return glParams.RED_BITS;
        case this.RENDERER: return glParams.RENDERER;
        case this.SHADING_LANGUAGE_VERSION: return glParams.SHADING_LANGUAGE_VERSION;
        case this.STENCIL_BITS: return glParams.STENCIL_BITS;
        case this.VENDOR: return glParams.VENDOR;
        case this.VERSION: return glParams.VERSION;

        default: console.log('getParameter ' + pname + '?'); return 0;
      }
    };

    getSupportedExtensions() {
      return extensions;
    };

    createShader(type) {
      var id = this.id++;
      this.items[id] = {
        which: 'shader',
        deleted: false,
        type: type,
      };
      return id;
    };

    getShaderParameter(shader, pname) {
      switch (pname) {
        case 35663: return this.items[shader].type;
        case 35713: return true;
        case 35712: return this.items[shader].deleted;
        default:
          console.log('cant get shader param ' + pname);
          return true;
        // throw 'getShaderParameter ' + pname;
      }
    };

    getShaderPrecisionFormat(shader, precision) {
      let shaderObj;
      switch (shader) {
        case this.VERTEX_SHADER:
          shaderObj = glParams.VERTEX_SHADER;
          break;
        case this.FRAGMENT_SHADER:
          shaderObj = glParams.FRAGMENT_SHADER;
          break;

        default:
          throw Error(`Wrong shader: ${shader}`);
      }

      let precisionObj;
      switch (precision) {
        case this.HIGH_FLOAT:
          precisionObj = shaderObj.HIGH_FLOAT;
          break;
        case this.MEDIUM_FLOAT:
          precisionObj = shaderObj.MEDIUM_FLOAT;
          break;
        case this.LOW_FLOAT:
          precisionObj = shaderObj.LOW_FLOAT;
          break;
        case this.HIGH_INT:
          precisionObj = shaderObj.HIGH_INT;
          break;
        case this.MEDIUM_INT:
          precisionObj = shaderObj.MEDIUM_INT;
          break;
        case this.LOW_INT:
          precisionObj = shaderObj.LOW_INT;
          break;

        default:
          throw Error(`Wrong precision: ${precision}`);
      }

      return precisionObj;
    }

    getContextAttributes() {
      return {
        antialias: true,
      }
    }

    shaderSource() {};
    compileShader() {};
    createProgram() {
      var id = this.id++;
      this.items[id] = {
        which: 'program',
        shaders: [],
      };
      return id;
    };
    attachShader(program, shader) {
      this.items[program].shaders.push(shader);
    };
    bindAttribLocation() {};
    linkProgram() {};
    getProgramParameter(program, pname) {
      switch (pname) {
        case 35714: return true;
        case 35718: return 4;
        default: throw 'getProgramParameter ' + pname;
      }
    };

    deleteShader(id) {
      this.items[id].deleted = true;
    };
    deleteProgram() {};
    viewport() {};
    clearColor() {};
    clearDepth() {};
    depthFunc() {};
    enable() {};
    disable() {};
    frontFace() {};
    cullFace() {};
    activeTexture() {};

    createTexture() {
      var id = this.id++;
      this.items[id] = {
        which: 'texture',
      };
      return id;
    };
    deleteTexture() {};

    bindTexture(target, texture) {
      this.boundTextures[target] = texture;
    };
    texParameteri(){};
    pixelStorei(){};
    texImage2D(){};
    compressedTexImage2D(){};
    useProgram(){};
    getUniformLocation() {
      return null;
    };
    getActiveUniform(program, index) {
      return {
        size: 1,
        type: /* INT_VEC3 */ 0x8B54,
        name: 'activeUniform' + index,
      };
    };

    clear() {};
    uniform4fv() {};
    uniform1i() {};
    uniform2f() {};
    getAttribLocation() { return 1 };
    vertexAttribPointer() {};
    enableVertexAttribArray() {};
    disableVertexAttribArray() {};
    drawElements() {};
    drawArrays() {};
    depthMask() {};
    depthRange() {};
    bufferSubData() {};
    blendFunc() {};

    createFramebuffer() {
      var id = this.id++;
      this.items[id] = {
        which: 'framebuffer',
        shaders: [],
      };
      return id;
    };
    bindFramebuffer(){};
    framebufferTexture2D(){};
    checkFramebufferStatus() {
      return /* FRAMEBUFFER_COMPLETE */ 0x8CD5;
    };
    createRenderbuffer() {
      var id = this.id++;
      this.items[id] = {
        which: 'renderbuffer',
        shaders: [],
      };
      return id;
    };
    bindRenderbuffer(){};
    renderbufferStorage(){};
    framebufferRenderbuffer(){};
    scissor(){};
    colorMask(){};
    lineWidth(){};
    vertexAttrib4fv(){};
    readPixels() {};
  }

  const getContext = window.HTMLCanvasElement.prototype.getContext;
  window.HTMLCanvasElement.prototype.getContext = function (type, ...args) {
    if (type === 'webgl' ||
        type === 'webgl2' ||
        type === 'experimental-webgl'
    ) {
      this.usedForWebGL = true;
      return new WebGLRenderingContext(this);
    }
    return getContext.call(this, type, ...args);
  }

  window.WebGLRenderingContext = WebGLRenderingContext;
  window.WebGL2RenderingContext = WebGLRenderingContext;
}

module.exports = defineWebGL;
