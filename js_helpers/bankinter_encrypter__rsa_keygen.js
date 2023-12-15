'use strict';
const {cypher} = require('./bankinter_new/cypher.cjs');

(async () => {
    let res = await cypher.generateKeyPair();
    console.log(JSON.stringify(res))
})();
