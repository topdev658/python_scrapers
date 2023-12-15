var cookieBite = {};

cookieBite.settings = {
    hashSalt: 510364800, // may change. look into js file with this data
    cookieName: 'ok-cookiebite',
    sessionExpiryTime: 30,
}
cookieBite.getDailyID = function () {
    var currentDate = new Date()
    return currentDate.getUTCFullYear().toString() + cookieBite.padLeft(currentDate.getUTCMonth() + 1, 2) + cookieBite.padLeft(currentDate.getUTCDate(), 2)
}

cookieBite.getExpiryTime = function () {
    var expiryTime = Date.now() + (cookieBite.settings.sessionExpiryTime * 60 * 1e3)
    return expiryTime
}

cookieBite.getFingerprint = function () {
    // from Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0
    return "0501186645602010010156004768136624"
}

// cookieBite.getFingerprint = function () {
//     var nav = window.navigator
//         , screen = window.screen
//         , fingerprint = nav.mimeTypes.length
//     fingerprint += nav.userAgent.replace(/\D+/g, '')
//     fingerprint += nav.plugins.length
//     fingerprint += nav.hardwareConcurrency || ''
//     fingerprint += screen.height || ''
//     fingerprint += screen.width || ''
//     fingerprint += screen.pixelDepth || ''
//     return fingerprint
// }

cookieBite.getSessionData = function () {
    var rawData = $.cookie(cookieBite.settings.cookieName).split('-')
        , processedData = {
        id: rawData[0] || 0,
        dailyId: parseInt(rawData[1]) || 0,
        session: parseInt(rawData[2]) || 0,
        expiration: new Date(parseInt(rawData[3]))
    }
    return processedData
}

cookieBite.getStringHash = function (string, seed) {
    var hash = seed || 5381
        , i = string.length
    while (i)
        hash = (hash * 33) ^ string.charCodeAt(--i)
    return hash >>> 0
}

cookieBite.getUserID = function () {
    var userID = cookieBite.getStringHash(cookieBite.getFingerprint(), cookieBite.settings.hashSalt);
    return userID
}

cookieBite.initialize = function () {
    let sessionData = {
        id: cookieBite.getUserID(),
        dailyId: cookieBite.getDailyID(),
        session: 1,
        expiration: cookieBite.getExpiryTime()
    }
    return sessionData

}

cookieBite.logMessage = function (message, data) {
    return '';
}

cookieBite.padLeft = function (val, quantity, character) {
    return Array(quantity - String(val).length + 1).join(character || '0') + val
}

cookieBite.renewSession = function (sessionData) {
    var session = sessionData || cookieBite.getSessionData()
    session.session = session.session + 1
    session.expiration = cookieBite.getExpiryTime()
    cookieBite.setCookie(session)
    cookieBite.logMessage('Session renewed...')
}

cookieBite.setCookie = function (sessionData) {
    var cookieValue = sessionData.id + '-' + sessionData.dailyId + '-' + cookieBite.padLeft(sessionData.session, 6) + '-' + sessionData.expiration
    // $.cookie(cookieBite.settings.cookieName, cookieValue, {
    //     path: '/',
    //     expires: 365,
    //     secure: true
    // })
    cookieBite.logMessage('Cookie created/updated with values: ', sessionData);
    return cookieValue
}

cookieBite.updateExpirationTime = function (sessionData) {
    var session = sessionData || cookieBite.getSessionData()
    session.expiration = cookieBite.getExpiryTime()
    cookieBite.setCookie(session)
    cookieBite.logMessage('Session time updated...')
};


(function () {
    let sessionData = cookieBite.initialize();
    console.log(cookieBite.setCookie(sessionData))
})()