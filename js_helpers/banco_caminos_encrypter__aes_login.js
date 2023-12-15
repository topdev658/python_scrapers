'use strict';
const {cypher} = require('./banco_caminos/cypher.cjs');

const enc = async (
    {
        username,
        password,
        deviceId,
        companyId,
        privateRSAKeyStr,
        signingDataEncrypted
    }
) => {
    let userdata = {
        documentId: username,
        password,
        companyId,
        channel: 'WEB',
        deviceId
    };
    let privateRSAKey = await cypher.getRSAPrivateKey(privateRSAKeyStr);
    let {symmetricKey, uuid, seed} = await cypher.decryptRSA(privateRSAKey, signingDataEncrypted);
    let aesKey = await cypher.getAESKey(symmetricKey);
    let encrypted = await cypher.encryptAES({seed: seed, key: aesKey, data: userdata});
    return {uuid, encrypted}
}

(async () => {
    let username = process.argv[2]
    let password = process.argv[3]
    let deviceId = process.argv[4]
    let companyId = process.argv[5]  // 'BC' - BancoCaminos, 'BF' - Bancofar
    let privateRSAKeyStr = process.argv[6]
    let signingDataEncrypted = process.argv[7]
    let res = await enc({username, password, deviceId, companyId, privateRSAKeyStr, signingDataEncrypted});
    console.log(JSON.stringify(res))
})();
