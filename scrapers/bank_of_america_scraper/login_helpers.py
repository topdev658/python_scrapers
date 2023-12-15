from collections import namedtuple

# to use as args for CONFIRMED_ENVIRONMENT_PATTERN
EnvPatternParams = namedtuple('EnvPatternParams', [
    'sid',  # "933928f25519a10e"
    'tid',  # "5687"
    't',  # "ZGNkY2U1MmYtMWI4ZC00MDQ4LWJjMjgtYjRlNjg0MTEzYjllOjE1NTEwNDM1NDMyNjM" for "_t"
    'cf_flags',  # 155687923
    'cookie_cc',  # "NTUzZTNhYzMtNjVlOS00ZjYz" for "cookie-_cc"
    'time_unix_epoch_ms',  # 1551043622006 for "time-unix-epoch-ms"
    'time_local',  # "2/25/2019, 12:27:02 AM" for "time-local"
    'time_string',  # "Mon Feb 25 2019 00:27:02 GMT+0300 (MSK)" for "time-string"
    # 'time_tz_offset_minutes',  # -180 for "time-tz-offset-minutes"
    'dom_session_tag',  # const DOM_SESSION_TAG for "dom-session-tag"
    'dom_local_tag'  # const DOM_LOCAL_TAG for "dom-local-tag"
])

CC_COOKIE = 'NTUzZTNhYzMtNjVlOS00ZjYz'  # necessary, expires in 2020
DOM_LOCAL_TAG = 'ODI5NDc1YzItYjIyMy00NTMw'  # necessary
# 1. _cc_ck in SESSION STORAGE (was the same as cookie-_cc in Chrome), should be constant
# BUT ALSO MAY CHANGE, in this case use 24 chars of _t (that is K from Fb), most recent was
_DOM_SESSION_TAG = 'YThmNjk5MDUtYzFlNS00OWFk'  # wrong, should gen as described above

PM_FP_PARAM = ('version=1&'
               'pm_fpua=mozilla/5.0 (x11; linux x86_64; rv:56.0) gecko/20100101 firefox/56.0|5.0 (X11)|'
               'Linux x86_64&pm_fpsc=24|1366|768|742&pm_fpsw=&pm_fptz=3'
               '&pm_fpln=lang=en-US|syslang=|userlang=&pm_fpjv=0&pm_fpco=1')

# 27 is unknown
# check:
# '27;-180;-240;{time_local};24;1366;742;0;0;;;;;;;;;;;;;;;;;;;19;' ->
# '27;0;0;{time_local};24;1366;742;0;0;;;;;;;;;;;;;;;;;;;19;' to calc as UTC
F_VAR_PARAM_PATERN = ('TF1;015;;;;;;;;;;;;;;;;;;;;;;'
                      'Mozilla;Netscape;5.0 (X11);20100101;undefined;true;Linux x86_64;true;'
                      'Linux x86_64;undefined;'
                      'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0;'
                      'en-US;undefined;www.bankofamerica.com;undefined;undefined;undefined;undefined;true;'
                      'false;%(time_unix_epoch_ms)s;3;6/7/2005, 9:33:44 PM;1366;768;;;;;;;'
                      '27;-180;-240;%(time_local)s;24;1366;742;0;0;;;;;;;;;;;;;;;;;;;19;')

CONFIRMED_ENVIRONMENT_PATTERN = (
    '{"sid":"%(sid)s","tid":"%(tid)s","_t":"%(t)s","cf_flags":%(cf_flags)s,"cookie-_cc":"%(cookie_cc)s",'
    '"timing-sc":35,"time-unix-epoch-ms":%(time_unix_epoch_ms)s,"time-local":"%(time_local)s","time-string":"%('
    'time_string)s","time-tz-offset-minutes":-180,"time-tz-has-dst":"false","time-tz-dst-active":"false",'
    '"time-tz-std-offset":-180,"time-tz-fixed-locale-string":"3/6/2014, 7:58:39 AM","timing-ti":1,'
    '"dom-local-tag":"%(dom_local_tag)s","timing-ls":0,"dom-session-tag":"%(dom_session_tag)s","timing-ss":0,'
    '"navigator.appVersion":"5.0 (X11)","navigator.appName":"Netscape","navigator.buildID":"20171024165158",'
    '"navigator.product":"Gecko","navigator.platform":"Linux x86_64","navigator.language":"en-US",'
    '"navigator.oscpu":"Linux x86_64","navigator.userAgent":"Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 '
    'Firefox/56.0","navigator.cookieEnabled":"true","navigator.appCodeName":"Mozilla",'
    '"navigator.productSub":"20100101","timing-no":3,"window.devicePixelRatio":"1","window.history.length":"10",'
    '"window.screen.height":"768","window.screen.width":"1366","timing-wo":0,"timing-do":0,"plugin-suffixes":"",'
    '"plugin-mimes":"","timing-np":0,"timing-iepl":1,'
    '"canvas-print-100-999":"336d849b429a995b1b9db7916cb12a7e59da38ff","timing-cp":46,"timing-gief":0,"js-errors":['
    '"InvalidCharacterError: String contains an invalid character"],"font-Times New Roman CYR":false,"font-Arial '
    'CYR":false,"font-Courier New CYR":false,"font-宋体":false,"font-Arial Cyr":false,"font-Times New Roman '
    'Cyr":false,"font-Courier New Cyr":false,"font-华文细黑":false,"font-儷黑 Pro":false,"font-WP CyrillicB":false,'
    '"font-WP CyrillicA":false,"font-궁서체":true,"font-細明體":false,"font-小塚明朝 Pr6N B":false,"font-宋体-PUA":false,'
    '"font-方正流行体繁体":false,"font-汉仪娃娃篆简":false,"font-돋움":true,"font-GaramondNo4CyrTCYLig":false,'
    '"font-HelveticaInserat Cyr Upright":false,"font-HelveticaCyr Upright":false,"font-TL Help Cyrillic":false,'
    '"font-가는안상수체":false,"font-TLCyrillic2":false,"font-AGRevueCyr-Roman":false,"font-AGOptimaCyr":false,'
    '"font-HelveticaInseratCyrillicUpright":false,"font-HelveticaCyrillicUpright":false,'
    '"font-HelveticaCyrillic":false,"font-CyrillicRibbon":false,"font-CyrillicHover":false,"font-文鼎ＰＯＰ－４":false,'
    '"font-方正中倩简体":false,"font-创艺简中圆":false,"font-Zrnic Cyr":false,"font-Zipper1 Cyr":false,"font-Xorx_windy '
    'Cyr":false,"font-Xorx_Toothy Cyr":false,"font-소야솔9":false,"font-Цветные эмодзи Apple":false,"font-Chinese '
    'Generic1":false,"font-Korean Generic1":false,"font-Bullets 5(Korean)":true,"font-UkrainianFuturisExtra":false,'
    '"font-VNI-Viettay":false,"font-UkrainianCompact":false,"font-UkrainianBrushScript":false,'
    '"font-TiffanyUkraine":false,"font-Baltica_Russian-ITV":false,"font-Vietnamese font":false,"font-Unicorn '
    'Ukrainian":false,"font-UkrainianTimesET":false,"font-UkrainianCourier":false,"font-Tiff-HeavyUkraine":false,'
    '"font-䡵湧䱡渠䅲瑤敳楧渠㈰〲‭⁁汬⁲楧桴猠牥獥牶敤⹔桵⁰桡瀠噎周畦慰〲†乯牭慬ㄮ〠䍯摥⁖义⁦潲⁗楮摯睳周畦慰〲乯牭慬HungLan Artdesign - '
    'http://www.vietcomic.comVNI-Thufap2 Normalv2.0 Code VNI for WindowsVNI-Thufap2 Normal\u0002":true,'
    '"font-Vietnam":false,"font-Bwviet":false, "font-Soviet":false,"font-Soviet Expanded":false,"font-Soviet '
    'Bold":false,"font-Russian":false,"font-UVN Han Viet":false,"font-UkrainianAcademy":false,"font-Symbol":true,'
    '"font-Verdana":false,"font-Webdings":false, "font-Arial":true,"font-Georgia":false,"font-Courier New":true,'
    '"font-Trebuchet MS":false,"font-Times New Roman":true,"font-Impact":false,"font-Comic Sans MS":false,'
    '"font-Wingdings":false,"font-Tahoma":false, "font-Microsoft Sans Serif":false,"font-Arial Black":false,'
    '"font-Plantagenet Cherokee":false,"font-Arial Narrow":true,"font-Wingdings 2":true,"font-Wingdings 3":true,'
    '"font-Arial Unicode MS":false,"font-Papyrus":false, "font-Calibri":false,"font-Cambria":false,'
    '"font-Consolas":false,"font-Candara":false,"font-Franklin Gothic Medium":false,"font-Corbel":false,'
    '"font-Constantia":false,"font-Marlett":false,"font-Lucida Console":false, "font-Lucida Sans Unicode":false,'
    '"font-MS Mincho":false,"font-Arial Rounded MT Bold":false,"font-Palatino Linotype":false,"font-Batang":true,'
    '"font-MS Gothic":false,"font-PMingLiU":false,"font-SimSun":false, "font-MS PGothic":false,'
    '"font-MS PMincho":false,"font-Gulim":true,"font-Cambria Math":false,"font-Garamond":false, "font-Bookman Old '
    'Style":false,"font-Book Antiqua":false,"font-Century Gothic":false,"font-Monotype Corsiva":false, '
    '"font-Courier":true,"font-Meiryo":false,"font-Century":false,"font-MT Extra":false,"font-MS Reference Sans '
    'Serif":false,"font-MS Reference Specialty":false,"font-Mistral":false,"font-Bookshelf Symbol 7":true,'
    '"font-Lucida Bright":false,"font-Cooper Black":false,"font-Modern No. 20":true,"font-Bernard MT '
    'Condensed":false,"font-Bell MT":false,"font-Baskerville Old Face":false,"font-Bauhaus 93":true,"font-Britannic '
    'Bold":false,"font-Wide Latin":false,"font-Playbill":false,"font-Harrington":false,"font-Onyx":false,'
    '"font-Footlight MT Light":false, "font-Stencil":false,"font-Colonna MT":false,"font-Matura MT Script '
    'Capitals":false,"font-Copperplate Gothic Bold":false,"font-Copperplate Gothic Light":false,"font-Edwardian '
    'Script ITC":false,"font-Rockwell":false, "font-Curlz MT":false,"font-Engravers MT":false,"font-Rockwell Extra '
    'Bold":false,"font-Haettenschweiler":false, "font-MingLiU":false,"font-Mongolian Baiti":false,"font-Microsoft Yi '
    'Baiti":false,"font-Microsoft Himalaya":false,"font-SimHei":false,"font-SimSun-ExtB":false,'
    '"font-PMingLiU-ExtB":false,"font-MingLiU-ExtB":false, "font-MingLiU_HKSCS-ExtB":false,'
    '"font-MingLiU_HKSCS":false,"font-Gabriola":false,"font-Goudy Old Style":false, "font-Calisto MT":false,'
    '"font-Imprint MT Shadow":false,"font-Gill Sans Ultra Bold":false,"font-Century Schoolbook":false,'
    '"font-Gloucester MT Extra Condensed":false,"font-Perpetua":false,"font-Franklin Gothic Book":false,"font-Brush '
    'Script MT":false,"font-Microsoft Tai Le":false,"font-Gill Sans MT":false,"font-Tw Cen MT":false,"font-Lucida '
    'Handwriting":false,"font-Lucida Sans":false,"font-Segoe UI":false,"font-Lucida Fax":false, '
    '"font-MV Boli":false,"font-Sylfaen":false,"font-Estrangelo Edessa":false,"font-Mangal":false,'
    '"font-Gautami":false, "font-Tunga":false,"font-Shruti":false,"font-Raavi":false,"font-Latha":false,"font-Lucida '
    'Calligraphy":false, "font-Lucida Sans Typewriter":false,"font-Kartika":false,"font-Vrinda":false,"font-Perpetua '
    'Titling MT":false, "font-Cordia New":false,"font-Angsana New":false,"font-IrisUPC":false,'
    '"font-CordiaUPC":false, "font-FreesiaUPC":false,"font-Miriam":false,"font-Traditional Arabic":false,'
    '"font-Miriam Fixed":false, "font-JasmineUPC":false,"font-KodchiangUPC":false,"font-LilyUPC":false,"font-Levenim '
    'MT":false, "font-EucrosiaUPC":false,"font-DilleniaUPC":false,"font-Rod":false,"font-Narkisim":false,'
    '"font-FrankRuehl":false, "font-David":false,"font-Andalus":false,"font-Browallia New":false,'
    '"font-AngsanaUPC":false, "font-BrowalliaUPC":false,"font-MS UI Gothic":false,"font-Aharoni":false,'
    '"font-Simplified Arabic Fixed":false, "font-Simplified Arabic":false,"font-GulimChe":true,"font-Dotum":true,'
    '"font-DotumChe":true,"font-GungsuhChe":true, "font-Gungsuh":true,"font-BatangChe":true,"font-Meiryo UI":false,'
    '"font-NSimSun":false,"font-Segoe Script":false, "font-Segoe Print":false,"font-DaunPenh":false,'
    '"font-Kalinga":false,"font-Iskoola Pota":false, "font-Euphemia":false,"font-DokChampa":false,'
    '"font-Nyala":false,"font-MoolBoran":false,"font-Leelawadee":false, "font-Gisha":false,"font-Microsoft '
    'Uighur":false,"font-Arabic Typesetting":false,"font-Malgun Gothic":true, "font-Microsoft JhengHei":true,'
    '"font-DFKai-SB":false,"font-Microsoft YaHei":true,"font-FangSong":false, "font-KaiTi":false,'
    '"font-Helvetica":true,"font-Segoe UI Light":false,"font-Segoe UI Semibold":false,"font-Andale Mono":false,'
    '"font-Palatino":true,"font-Geneva":false,"font-Monaco":false,"font-Lucida Grande":false,"font-Gill Sans":false,'
    '"font-Helvetica Neue":false,"font-Baskerville":false,"font-Hoefler Text":false,"font-Thonburi":false, '
    '"font-Herculanum":false,"font-Apple Chancery":false,"font-Didot":false,"font-Zapf Dingbats":true,"font-Apple '
    'Symbols":false,"font-Copperplate":false,"font-American Typewriter":false,"font-Zapfino":false,'
    '"font-Cochin":false, "font-Chalkboard":false,"font-Sathu":false,"font-Osaka":false,"font-BiauKai":false,'
    '"font-Segoe UI Symbol":false, "font-Aparajita":false,"font-Krungthep":false,"font-Ebrima":false,'
    '"font-Silom":false,"font-Kokila":false, "font-Shonar Bangla":false,"font-Sakkal Majalla":false,"font-Microsoft '
    'PhagsPa":false,"font-Microsoft New Tai Lue":false,"font-Khmer UI":false,"font-Vijaya":false,'
    '"font-Utsaah":false,"font-Charcoal CY":false, "font-Ayuthaya":false,"font-InaiMathi":false,"font-Euphemia '
    'UCAS":false,"font-Vani":false,"font-Lao UI":false, "font-GB18030 Bitmap":false,"font-KufiStandardGK":false,'
    '"font-Geeza Pro":false,"font-Chalkduster":false, "font-Tempus Sans ITC":false,"font-Kristen ITC":false,'
    '"font-Apple Braille":false,"font-Juice ITC":false, "font-STHeiti":false,"font-LiHei Pro":false,"font-DecoType '
    'Naskh":false,"font-New Peninim MT":false, "font-Nadeem":false,"font-Mshtakan":false,"font-Gujarati MT":false,'
    '"font-Devanagari MT":false,"font-Arial Hebrew":false,"font-Corsiva Hebrew":false,"font-Baghdad":false,'
    '"font-STFangsong":false,"timing-kf":175, "webgl-supported":true,"webgl-extensions":["ANGLE_instanced_arrays",'
    '"EXT_blend_minmax", "EXT_color_buffer_half_float","EXT_frag_depth","EXT_sRGB","EXT_shader_texture_lod", '
    '"EXT_texture_filter_anisotropic","EXT_disjoint_timer_query","OES_element_index_uint",'
    '"OES_standard_derivatives", "OES_texture_float","OES_texture_float_linear","OES_texture_half_float",'
    '"OES_texture_half_float_linear", "OES_vertex_array_object","WEBGL_color_buffer_float",'
    '"WEBGL_compressed_texture_etc", "WEBGL_compressed_texture_s3tc","WEBGL_compressed_texture_s3tc_srgb",'
    '"WEBGL_debug_renderer_info", "WEBGL_debug_shaders","WEBGL_depth_texture","WEBGL_draw_buffers",'
    '"WEBGL_lose_context","MOZ_WEBGL_lose_context", "MOZ_WEBGL_compressed_texture_s3tc","MOZ_WEBGL_depth_texture"],'
    '"webgl-max-aa":16,"webgl-version":"WebGL 1.0", "webgl-glsl-version":"WebGL GLSL ES 1.0",'
    '"webgl-vendor":"Mozilla","webgl-renderer":"Mozilla", "webgl-vendor-real":"Intel Open Source Technology Center",'
    '"webgl-renderer-real":"Mesa DRI Intel(R) Sandybridge Mobile ","timing-wgl":13,"timing-bfdm":0,"timing-bfdc":0,'
    '"webrtc-addrs":{"192.168.1.41":{"type":"host"}, "109.252.19.20":{"type":"srflx"}},'
    '"webrtc-sdp":"v=0\r\no=mozilla...d-56.0.2 1323442930290208797 0 IN IP4 0.0.0.0\r\ns=-\r\nt=0 '
    '0\r\na=sendrecv\r\na=fingerprint:sha-256 '
    'E6:1D:DE:2B:87:68:DC:49:40:F8:90:F3:10:6E:E6:BF:80:6C:28:F5:9F:E0:54:6F:28:29:90:8E:8E:0A:BD:26\r\na=group'
    ':BUNDLE sdparta_0\r\na=ice-options:trickle\r\na=msid-semantic:WMS *\r\nm=application 4783 DTLS/SCTP '
    '5000\r\nc=IN IP4 109.252.19.20\r\na=candidate:0 1 UDP 2122252543 192.168.1.41 34129 typ host\r\na=candidate:2 1 '
    'TCP 2105524479 192.168.1.41 9 typ host tcptype active\r\na=candidate:1 1 UDP 1686052863 109.252.19.20 4783 typ '
    'srflx raddr 192.168.1.41 rport 34129\r\na=sendrecv\r\na=end-of-candidates\r\na=ice-pwd'
    ':4dc4832f351f68b34d3369d5b4f0bd0c\r\na =ice-ufrag:ce80f7ac\r\na=mid:sdparta_0\r\na=sctpmap:5000 '
    'webrtc-datachannel 256\r\na=setup:actpass\r\n", "timing-wr":878}"'
)