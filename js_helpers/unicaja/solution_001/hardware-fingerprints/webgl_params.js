const glExtensionsLinuxNvidia001 = [
  'ANGLE_instanced_arrays',
  'EXT_blend_minmax',
  'EXT_color_buffer_half_float',
  'EXT_disjoint_timer_query',
  'EXT_float_blend',
  'EXT_frag_depth',
  'EXT_shader_texture_lod',
  'EXT_texture_compression_bptc',
  'EXT_texture_compression_rgtc',
  'EXT_texture_filter_anisotropic',
  'EXT_sRGB',
  'KHR_parallel_shader_compile',
  'OES_element_index_uint',
  'OES_fbo_render_mipmap',
  'OES_standard_derivatives',
  'OES_texture_float',
  'OES_texture_float_linear',
  'OES_texture_half_float',
  'OES_texture_half_float_linear',
  'OES_vertex_array_object',
  'WEBGL_color_buffer_float',
  'WEBGL_compressed_texture_s3tc',
  'WEBGL_compressed_texture_s3tc_srgb',
  'WEBGL_debug_renderer_info',
  'WEBGL_debug_shaders',
  'WEBGL_depth_texture',
  'WEBGL_draw_buffers',
  'WEBGL_lose_context',
  'WEBGL_multi_draw',
];

const glExtensionsWindowsNvidia001 = [
    "ANGLE_instanced_arrays",
    "EXT_blend_minmax",
    "EXT_color_buffer_half_float",
    "EXT_disjoint_timer_query",
    "EXT_float_blend",
    "EXT_frag_depth",
    "EXT_shader_texture_lod",
    "EXT_texture_compression_bptc",
    "EXT_texture_compression_rgtc",
    "EXT_texture_filter_anisotropic",
    "EXT_sRGB",
    "KHR_parallel_shader_compile",
    "OES_element_index_uint",
    "OES_fbo_render_mipmap",
    "OES_standard_derivatives",
    "OES_texture_float",
    "OES_texture_float_linear",
    "OES_texture_half_float",
    "OES_texture_half_float_linear",
    "OES_vertex_array_object",
    "WEBGL_color_buffer_float",
    "WEBGL_compressed_texture_s3tc",
    "WEBGL_compressed_texture_s3tc_srgb",
    "WEBGL_debug_renderer_info",
    "WEBGL_debug_shaders",
    "WEBGL_depth_texture",
    "WEBGL_draw_buffers",
    "WEBGL_lose_context",
    "WEBGL_multi_draw"
];

const glExtensionsWindowsGoogle001 = [
  "ANGLE_instanced_arrays",
  "EXT_blend_minmax",
  "EXT_color_buffer_half_float",
  "EXT_float_blend",
  "EXT_frag_depth",
  "EXT_shader_texture_lod",
  "EXT_texture_compression_bptc",
  "EXT_texture_compression_rgtc",
  "EXT_texture_filter_anisotropic",
  "EXT_sRGB",
  "OES_element_index_uint",
  "OES_fbo_render_mipmap",
  "OES_standard_derivatives",
  "OES_texture_float",
  "OES_texture_float_linear",
  "OES_texture_half_float",
  "OES_texture_half_float_linear",
  "OES_vertex_array_object",
  "WEBGL_color_buffer_float",
  "WEBGL_compressed_texture_astc",
  "WEBGL_compressed_texture_etc",
  "WEBGL_compressed_texture_etc1",
  "WEBGL_compressed_texture_s3tc",
  "WEBGL_compressed_texture_s3tc_srgb",
  "WEBGL_debug_renderer_info",
  "WEBGL_depth_texture",
  "WEBGL_draw_buffers",
  "WEBGL_lose_context",
  "WEBGL_multi_draw"
];

const glParamsLinuxNvidia001 = {
  ALIASED_LINE_WIDTH_RANGE: new Float32Array([1, 10]),
  ALIASED_POINT_SIZE_RANGE: new Float32Array([1, 2047]),
  ALPHA_BITS: 8,
  BLUE_BITS: 8,
  DEPTH_BITS: 24,
  GREEN_BITS: 8,
  MAX_TEXTURE_MAX_ANISOTROPY_EXT: 16,
  MAX_COMBINED_TEXTURE_IMAGE_UNITS: 64,
  MAX_CUBE_MAP_TEXTURE_SIZE: 32768,
  MAX_FRAGMENT_UNIFORM_VECTORS: 1024,
  MAX_RENDERBUFFER_SIZE: 32768,
  MAX_TEXTURE_IMAGE_UNITS: 32,
  MAX_TEXTURE_SIZE: 32768,
  MAX_VARYING_VECTORS: 31,
  MAX_VERTEX_ATTRIBS: 16,
  MAX_VERTEX_TEXTURE_IMAGE_UNITS: 32,
  MAX_VERTEX_UNIFORM_VECTORS: 1024,
  MAX_VIEWPORT_DIMS: new Int32Array([32768, 32768]),
  RED_BITS: 8,
  RENDERER: 'WebKit WebGL',
  SHADING_LANGUAGE_VERSION: 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)',
  STENCIL_BITS: 0,
  VENDOR: 'WebKit',
  VERSION: 'WebGL 1.0 (OpenGL ES 2.0 Chromium)',

  VERTEX_SHADER: {
    HIGH_FLOAT:   { precision: 23, rangeMin: 127, rangeMax: 127 },
    MEDIUM_FLOAT: { precision: 10, rangeMin: 15, rangeMax: 15 },
    LOW_FLOAT:    { precision: 10, rangeMin: 15, rangeMax: 15 },

    HIGH_INT:     { precision: 0, rangeMin: 31, rangeMax: 30 },
    MEDIUM_INT:   { precision: 0, rangeMin: 31, rangeMax: 30 },
    LOW_INT:      { precision: 0, rangeMin: 31, rangeMax: 30 },
  },
  FRAGMENT_SHADER: {
    HIGH_FLOAT:   { precision: 23, rangeMin: 127, rangeMax: 127 },
    MEDIUM_FLOAT: { precision: 10, rangeMin: 15, rangeMax: 15 },
    LOW_FLOAT:    { precision: 10, rangeMin: 15, rangeMax: 15 },

    HIGH_INT:     { precision: 0, rangeMin: 31, rangeMax: 30 },
    MEDIUM_INT:   { precision: 0, rangeMin: 31, rangeMax: 30 },
    LOW_INT:      { precision: 0, rangeMin: 31, rangeMax: 30 },
  },
}

const glParamsWindowsNvidia001 = {
    "ALIASED_LINE_WIDTH_RANGE": new Float32Array([1, 1]),
    "ALIASED_POINT_SIZE_RANGE": new Float32Array([1, 1024]),
    "ALPHA_BITS": 8,
    "BLUE_BITS": 8,
    "DEPTH_BITS": 24,
    "GREEN_BITS": 8,
    "MAX_TEXTURE_MAX_ANISOTROPY_EXT": 16,
    "MAX_COMBINED_TEXTURE_IMAGE_UNITS": 32,
    "MAX_CUBE_MAP_TEXTURE_SIZE": 16384,
    "MAX_FRAGMENT_UNIFORM_VECTORS": 1024,
    "MAX_RENDERBUFFER_SIZE": 16384,
    "MAX_TEXTURE_IMAGE_UNITS": 16,
    "MAX_TEXTURE_SIZE": 16384,
    "MAX_VARYING_VECTORS": 30,
    "MAX_VERTEX_ATTRIBS": 16,
    "MAX_VERTEX_TEXTURE_IMAGE_UNITS": 16,
    "MAX_VERTEX_UNIFORM_VECTORS": 4095,
    "MAX_VIEWPORT_DIMS": new Int32Array([32767, 32767]),
    "RED_BITS": 8,
    "RENDERER": "WebKit WebGL",
    "SHADING_LANGUAGE_VERSION": "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
    "STENCIL_BITS": 0,
    "VENDOR": "WebKit",
    "VERSION": "WebGL 1.0 (OpenGL ES 2.0 Chromium)",
    "VERTEX_SHADER": {
      "HIGH_FLOAT":   { "precision": 23, "rangeMin": 127, "rangeMax": 127 },
      "MEDIUM_FLOAT": { "precision": 23, "rangeMin": 127, "rangeMax": 127 },
      "LOW_FLOAT":    { "precision": 23, "rangeMin": 127, "rangeMax": 127 },

      "HIGH_INT":     { "precision": 0, "rangeMin": 31, "rangeMax": 30 },
      "MEDIUM_INT":   { "precision": 0, "rangeMin": 31, "rangeMax": 30 },
      "LOW_INT":      { "precision": 0, "rangeMin": 31, "rangeMax": 30 },
    },
    "FRAGMENT_SHADER": {
      "HIGH_FLOAT":   { "precision": 23, "rangeMin": 127, "rangeMax": 127 },
      "MEDIUM_FLOAT": { "precision": 23, "rangeMin": 127, "rangeMax": 127 },
      "LOW_FLOAT":    { "precision": 23, "rangeMin": 127, "rangeMax": 127 },

      "HIGH_INT":     { "precision": 0, "rangeMin": 31, "rangeMax": 30 },
      "MEDIUM_INT":   { "precision": 0, "rangeMin": 31, "rangeMax": 30 },
      "LOW_INT":      { "precision": 0, "rangeMin": 31, "rangeMax": 30 },
    }
};

const glParamsWindowsGoogle001 = {
  "ALIASED_LINE_WIDTH_RANGE": new Float32Array([1, 1]),
  "ALIASED_POINT_SIZE_RANGE": new Float32Array([1, 1023]),
  "ALPHA_BITS": 8,
  "BLUE_BITS": 8,
  "DEPTH_BITS": 24,
  "GREEN_BITS": 8,
  "MAX_TEXTURE_MAX_ANISOTROPY_EXT": 16,
  "MAX_COMBINED_TEXTURE_IMAGE_UNITS": 64,
  "MAX_CUBE_MAP_TEXTURE_SIZE": 16384,
  "MAX_FRAGMENT_UNIFORM_VECTORS": 4096,
  "MAX_RENDERBUFFER_SIZE": 8192,
  "MAX_TEXTURE_IMAGE_UNITS": 32,
  "MAX_TEXTURE_SIZE": 8192,
  "MAX_VARYING_VECTORS": 31,
  "MAX_VERTEX_ATTRIBS": 16,
  "MAX_VERTEX_TEXTURE_IMAGE_UNITS": 32,
  "MAX_VERTEX_UNIFORM_VECTORS": 4096,
  "MAX_VIEWPORT_DIMS": new Int32Array([8192, 8192]),
  "RED_BITS": 8,
  "RENDERER": "WebKit WebGL",
  "SHADING_LANGUAGE_VERSION": "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
  "STENCIL_BITS": 0,
  "VENDOR": "WebKit",
  "VERSION": "WebGL 1.0 (OpenGL ES 2.0 Chromium)",

  "VERTEX_SHADER": {
    "HIGH_FLOAT":   { "precision": 23, "rangeMin": 127, "rangeMax": 127 },
    "MEDIUM_FLOAT": { "precision": 10, "rangeMin": 15, "rangeMax": 15 },
    "LOW_FLOAT":    { "precision": 10, "rangeMin": 15, "rangeMax": 15 },

    "HIGH_INT":     { "precision": 0, "rangeMin": 31, "rangeMax": 30 },
    "MEDIUM_INT":   { "precision": 0, "rangeMin": 15, "rangeMax": 14 },
    "LOW_INT":      { "precision": 0, "rangeMin": 15, "rangeMax": 14 }
  },
  "FRAGMENT_SHADER": {
    "HIGH_FLOAT":   { "precision": 23, "rangeMin": 127, "rangeMax": 127 },
    "MEDIUM_FLOAT": { "precision": 10, "rangeMin": 15, "rangeMax": 15 },
    "LOW_FLOAT":    { "precision": 10, "rangeMin": 15, "rangeMax": 15 },

    "HIGH_INT":     { "precision": 0, "rangeMin": 31, "rangeMax": 30 },
    "MEDIUM_INT":   { "precision": 0, "rangeMin": 15, "rangeMax": 14 },
    "LOW_INT":      { "precision": 0, "rangeMin": 15, "rangeMax": 14 },
  }
}

function getWebGlParamsForPreset(preset) {
  switch (preset) {
    // My Ubuntu
    case 'linux_nvidia_001':
      return [glExtensionsLinuxNvidia001, glParamsLinuxNvidia001];
    // My Windows
    case 'windows_nvidia_001':
      return [glExtensionsWindowsNvidia001, glParamsWindowsNvidia001];
    // Windows VM in VBox
    case 'windows_google_001':
      return [glExtensionsWindowsGoogle001, glParamsWindowsGoogle001];
    default:
      throw new Error(`Unknown webgl preset: ${preset}`)
  }
}

module.exports = getWebGlParamsForPreset;