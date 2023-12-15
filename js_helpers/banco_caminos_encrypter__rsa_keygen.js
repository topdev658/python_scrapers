'use strict';
const {cypher} = require('./banco_caminos/cypher.cjs');

(async () => {
    let res = await cypher.generateKeyPairForExport();
    console.log(JSON.stringify(res))
})();
