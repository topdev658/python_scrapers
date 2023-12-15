'use strict';
const {cypher} = require('./bankinter_new/cypher.cjs');

(async () => {
    let msg = process.argv[2]
    let clientPrivKeyStr = process.argv[3]
    let clientPrivKeyObj = JSON.parse(clientPrivKeyStr)
    let res = await cypher.decrypt(msg, clientPrivKeyObj);
    console.log(res)
})();
