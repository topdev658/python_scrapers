// from Escolors.js

function Mk(l){
  var tab = "0123456789ABCDEF0";
  var x = Math.floor(Math.random() * l) + 2;
  if (x & 1) x++;
  var s = "";
  for (var i = 0; i < x; i++)
    s += tab.charAt(Math.floor(Math.random() * 16));
  return s;
}
function char2hex(i){
  var hex_tab = "0123456789ABCDEF";
  return hex_tab.charAt(i >> 4) + hex_tab.charAt(i & 0x0F);
}

function hex2bin(data){
  var i,outs = "";
  for(i = 0; i < data.length; i+=2)
    outs += String.fromCharCode(parseInt(data.substr(i,2),16));
  return outs;
}

function bin2hex(data){
  var i,outs = "";
  for(i = 0; i < data.length; i++)
    outs += char2hex(data.charCodeAt(i));
  return outs;
}

function cvt1(key, text) {
 var i, x, y, t, x2;
 var s = new Array(256);

 if (key.substring(0,2) == "0x") key = hex2bin(key.substr(2));

 for (i=0; i<256; i++) s[i]=i
 y=0;
 i = 0;
 for (x=0; x < 256; x++) {
   y=(key.charCodeAt(i) + s[x] + y) % 256
   t=s[x]; s[x]=s[y]; s[y]=t
   if (++i == key.length) i = 0;
 }
 x=0;  y=0;
 var z="";
 for (x=0; x < text.length; x++) {
  x2=(x + 1 ) & 255
  y=( s[x2] + y) & 255
  t=s[x2]; s[x2]=s[y]; s[y]=t
  z+= String.fromCharCode((text.charCodeAt(x) ^ s[(s[x2] + s[y]) % 256]))
 }
 return bin2hex(z) + Mk(8);
}


/**
 * node novobanco_encrypter.js 7 jd8Jr$7bhtty86c7 918543
 */
(function () {
    // prefix and key from
    // function lmp(frm) { frm.nx.value='7'+cvt1('jd8Jr$7bhtty86c7', frm.pin.value); frm.pin.value=""; }
    var prefix = process.argv[2];
    var key  = process.argv[3];
    var userpass =  process.argv[4];

    var encrypted = prefix + cvt1(key, userpass);
    console.log(encrypted);
})();
