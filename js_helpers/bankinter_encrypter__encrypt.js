'use strict';
const {cypher} = require('./bankinter_new/cypher.cjs');

(async () => {
    "{\"answers\": [{\"id\": \"694bHVWxMCLenXr\", \"challengeType\": \"USER\", \"pattern\": \"KD(1647723645041;tag:INPUT;id:694bHVWxMCLenXr;mod:2;code:17)KD(154;code:86)KU(69;code:86)KU(115;mod:0;code:17)\", \"challengeAnswer\": \"B09417932\"}, {\"id\": \"5a8dmt0S5zxbfPA\", \"challengeType\": \"PASSWORD\", \"pattern\": \"KD(1647723675222;tag:INPUT;id:5a8dmt0S5zxbfPA;mod:2;code:17)KD(372)KU(170)KU(33;mod:0;code:17)\", \"challengeAnswer\": \"e2754dabd916fa8acd4cb1d1e12cb26eae6031c477cad18149813f59fca9ee2e\"}], \"backToPrevious\": false}"
    let msgJSONStr = process.argv[2]
    "{\"kty\": \"RSA\", " +
    "\"n\": \"vmvj2edCo9DUrelSflnX6g97pzVZOIv1ZHC4WQuzy_5xS-xffKaP-LND02rGDvKvGJVBgTEIcSG1_VVRE-8cP_kxN-HfTt5MUOIG236pLwVIxBO8-xPI8YQmgsYlv3aEU1bw1FIxE-AtpNTzik-pmEvy8ucNJLkDyXbXQw5G71s\", \"e\": \"AQAB\", \"d\": \"WRlQhuAPrWkEas-Wuuo8_hb6i9WJhszuKG4ZxAiWu2e2CYlzcHbbPMpcfSsju1DQnxcPjGyt_4l_hycJheNG-tSDwpnBZ25f3xKz6AFIxKf4q_pZoJ642AsSTEjbGIQG9rQdrMLZjx-6T7qu5SkPfBtI0apVtV8VrZmfI05r5OE\", \"p\": \"8wKq6b926C6p9wgaX1HG_aqBlecqp4aFE0Y7n5SWCd_b-wBc9GX-9joMFLfT8KYRrBkUAa8i70TmIvtC9y3JSw\", \"q\": \"yJmZhU96MgMgNI9y_2T7LcAapSAhe1UkdFRVLs25uS8O6-b5rbvWhDUaENjtshC_hzloqHJarIa5MPlexZE4MQ\", \"dp\": \"ZMltc2bqfR-ldIRS08fJ_TkzZ6WppjN_i9_sKKJqnAvRY8fhxadr2Fl42zrm1v85gyQfjRdDKPNtc4K8YmIGAw\", \"dq\": \"laL2gRobRelNAcgr-VVjhOozNg_0yeJmUhyCempd60SuNczTXQSsbWyLKBwZm2Wg6YcqidTbzKymwmCSkH_WUQ\", \"qi\": \"OvFD2Vb1_rWlUlmLDFKY2le3abhIeh_rvEeaLotZixZ5PH6qg8N0RSDhXDDLTEl1TxLuEOSO2CfDTlYhADtOWg\"}"
    let clientPrivKeyStr = process.argv[3]
    "{\"kty\": \"RSA\", " +
    "\"kid\": \"server_76f6PkCuqC8TQWareQvd5HptSUnwd9fDl5p5r\", " +
    "\"n\": \"6fSUjFPu5xWxWTvqttq0v23wcZ2lXf-lVXsLtHTDLC4KK3Z7dWS0JIW9nKJy7q7VlQT38Z48CQqWpvY5ZsDmeSKKZ871CWYKk1HyG0u2bxTIT5_geNIte2EPrveTbHi1GcY9Yvk4hdlLKTiRWVLmL5IerK9xsJMX52UBbNIHHgCEXc6MkvWwkdI772mE-x0vyNpsE-dQML16ew3oubuT_2KJRX0_efRvovFY_IPLA6tiKl8gRaDpIQGkQh_qjRmvBPm0MolGTtWA0VpLEOvd4w6psCJsqq2BtUu8yV8Wl6TEChiyo3YlanpCGNAfyht-jz47lx2O4VgLpPP38FS6iQ\", " +
    "\"e\": \"AQAB\"}"
    let serverPubKeyStr = process.argv[4]
    let msgObj = JSON.parse(msgJSONStr)
    let clientPrivKeyObj = JSON.parse(clientPrivKeyStr)
    let serverPubKeyObj = JSON.parse(serverPubKeyStr)

    let res = await cypher.signEncryptReq(msgObj, clientPrivKeyObj, serverPubKeyObj);
    console.log(res)
})();
