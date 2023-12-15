'use strict';
const {cypher} = require('./banco_caminos/cypher.cjs');

const dec = async ({privateRSAKeyStr, signingDataEncrypted, msg}) => {
    // see m-secure.decrypt
    let privateRSAKey = await cypher.getRSAPrivateKey(privateRSAKeyStr);
    let {symmetricKey, seed} = await cypher.decryptRSA(privateRSAKey, signingDataEncrypted);
    let aesKey = await cypher.getAESKey(symmetricKey);
    return cypher.decryptAES({seed, key: aesKey, data: msg})
}

(async () => {
    let privateRSAKeyStr = process.argv[2]
    let signingDataEncrypted = process.argv[3]
    let msg = process.argv[4]
    let res = await dec({privateRSAKeyStr, signingDataEncrypted, msg});
    console.log(JSON.stringify(res))
})();
