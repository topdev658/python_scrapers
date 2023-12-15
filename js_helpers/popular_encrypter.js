function encriptar(c) {
  for (var h = function (c) {
    for (c = 999 - c + ''; 3 > c.length; ) c = '0' + c;
    return c
  }, m = ~~(9 * Math.random() + 1), t = h(m), u = 0; u < c.length; u++) t += h(c.charCodeAt(u) + m);
  return t
}

/**
 * node popular_encrypter.js 12345678
 */
(function () {
    var userpass = process.argv[2];
    var encrypted = encriptar(userpass);
    console.log(encrypted);
})();
