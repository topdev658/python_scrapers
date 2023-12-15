// FROM https://www.bbva.com.uy/wps/wcm/connect/3d20d7b1-884d-4a1d-bb19-774ab8b6f567/s_code.js?MOD=...
(function () {
    let d = '0123456789ABCDEF', fid = '', h = '', l = '', i, j, m = 8, n = 4;
    for (i = 0; i < 16; i++) {
        j = Math.floor(Math.random() * m);
        h += d.substring(j, j + 1);
        j = Math.floor(Math.random() * n);
        l += d.substring(j, j + 1);
        m = n = 16
    }
    fid = h + '-' + l;
    console.log(fid)
})()
