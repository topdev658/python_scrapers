// FROM webpack://src/store/secure
// VB
// import { Unibabel } from 'unibabel';
// to export private key:
// https://riptutorial.com/javascript/example/17845/generating-rsa-key-pair-and-converting-to-pem-format

(function (exports) {
    'use strict';

    const {Unibabel} = require('./unibabel.cjs');
    const crypto = require('crypto').webcrypto;

    const algorithmRSA = {
        name: 'RSA-OAEP',
        modulusLength: 2048,
        publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
        hash: {name: 'SHA-256'},
    };

    const algorithmAES = {
        name: 'AES-CBC',
        length: 256,
    };

    /**
     * Original function
     * @returns {Promise<{privateKey: CryptoKey, publicKey: string}>}
     */
    const generateKeyPair = async () => {
        const keyPair = await crypto.subtle.generateKey(algorithmRSA, true, ['encrypt', 'decrypt']);
        const publicKey = await crypto.subtle.exportKey('spki', keyPair.publicKey);
        const base64PublicKey = Unibabel.bufferToBase64(new Uint8Array(publicKey));

        return {
            privateKey: keyPair.privateKey,
            publicKey: base64PublicKey,
        };
    };

    // VB
    /**
     * Updated: exports privateKey
     * @returns {Promise<{privateKey: string, publicKey: string}>}
     */
    const generateKeyPairForExport = async () => {
        const keyPair = await crypto.subtle.generateKey(algorithmRSA, true, ['encrypt', 'decrypt']);

        const publicKey = await crypto.subtle.exportKey('spki', keyPair.publicKey);
        const base64PublicKey = Unibabel.bufferToBase64(new Uint8Array(publicKey));

        const privateKey = await crypto.subtle.exportKey('pkcs8', keyPair.privateKey);
        const base64PrivateKey = Unibabel.bufferToBase64(new Uint8Array(privateKey));

        return {
            privateKey: base64PrivateKey,
            publicKey: base64PublicKey,
        };
    };

    const getRSAKey = async (rawPublicKey) => {
        return crypto.subtle.importKey(
            'spki',
            Unibabel.base64ToArr(rawPublicKey).buffer,
            algorithmRSA,
            false,
            ['encrypt']
        );
    };

    // VB
    /**
     * @param {String} rawPrivateKey
     * @returns {Promise<CryptoKey>}
     */
    const getRSAPrivateKey = async (rawPrivateKey) => {
        return crypto.subtle.importKey(
            'pkcs8',
            Unibabel.base64ToArr(rawPrivateKey).buffer,
            algorithmRSA,
            false,
            ['decrypt']
        );
    };

    const generateSeed = () => {
        const rawSeed = window.crypto.getRandomValues(new Uint8Array(16));
        const token = Buffer.from(rawSeed).toString('base64');

        return token;
    };

    const generateAESKey = async () => {
        const key = await crypto.subtle.generateKey(algorithmAES, true, ['encrypt', 'decrypt']);
        const exportedKey = await crypto.subtle.exportKey('raw', key);
        const seed = generateSeed();
        const symmetricKey = Buffer.from(exportedKey).toString('base64');

        return {
            key,
            symmetricKey,
            seed,
        };
    };

    /**
     * @param {String} base64String
     * @returns {Promise<CryptoKey>}
     */
    const getAESKey = async (base64String) => {
        const symmetricKeyBuffer = Unibabel.base64ToArr(base64String).buffer;
        const key = await crypto.subtle.importKey(
            'raw',
            symmetricKeyBuffer,
            {name: algorithmAES.name},
            true,
            ['encrypt', 'decrypt']
        );
        return key;
    };

    /**
     *
     * @param {CryptoKey} privateKey
     * @param {String} data
     * @returns {Promise<Object>} like {
        // key to get key for encryptAES (from getAESKey())
        symmetricKey: 'Ftj0bLyOPGUonnJPwG+w+Rdu0IjBfRwzP/Y9FYNrx+o=',
        // will send as req header 'uuid: cb6be3d6-6508-4cc7-b85f-c1960d141629' for login/
        uuid: '108bdccf-2ac7-408b-bdc0-d5db54196893',
        // seed for encryptAES
        seed: 'xyx+N8S3ivOZlQuD9NLyrA==',
        uuidAssociated: null
        }
     */
    const decryptRSA = async (privateKey, data) => {
        const response = await crypto.subtle.decrypt(
            algorithmRSA,
            privateKey,
            Unibabel.base64ToArr(data)
        );
        return JSON.parse(Unibabel.bufferToUtf8(new Uint8Array(response)));
    };

    const encryptRSA = async (publicKey, data) => {
        const response = await crypto.subtle.encrypt(
            algorithmRSA,
            publicKey,
            Unibabel.utf8ToBuffer(JSON.stringify(data)).buffer
        );

        return Buffer.from(response).toString('base64');
    };

// VB: this one from m-secure
// 		/**
// 		 * Encrypt data with the symmetric key.
// 		 * @param {store} store
// 		 * @param {state} store.state
// 		 * @param {Object} payload Data to encrypt
// 		 * @returns {String} A base64 encrypted data
// 		 */
// 		async encrypt({ state, dispatch }, data) {
// 			const key = await dispatch('getAESKey');
// 			const { seed } = state;
//
// 			return encryptAES({ seed, key, data });
// 		},
    /**
     * @param {String} seed
     * @param {CryptoKey} key
     * @param {Object} data
     * @returns {Promise<string>}
     */
    const encryptAES = async ({seed, key, data}) => {
        const seedBuffer = Unibabel.base64ToArr(seed).buffer;

        const encryptedData = await crypto.subtle.encrypt(
            {
                name: algorithmAES.name,
                iv: seedBuffer,
            },
            key,
            Unibabel.utf8ToBuffer(JSON.stringify(data)).buffer
        );

        return Buffer.from(encryptedData).toString('base64');
    };

    const decryptAES = async ({seed, key, data}) => {
        const seedBuffer = Unibabel.base64ToArr(seed).buffer;

        const response = await crypto.subtle.decrypt(
            {
                name: algorithmAES.name,
                iv: seedBuffer,
            },
            key,
            Unibabel.base64ToBuffer(data).buffer
        );

        return JSON.parse(Unibabel.bufferToUtf8(new Uint8Array(response)));
    };

    const cypherSha256 = async (message) => {
        const msgUint8 = Unibabel.utf8ToBuffer(message).buffer;
        const hashBuffer = await crypto.subtle.digest('SHA-256', msgUint8);
        return Buffer.from(hashBuffer).toString('base64');
    };

    const stringToHash = function (str, seed = 0) {
        let h1 = 0xdeadbeef ^ seed;
        let h2 = 0x41c6ce57 ^ seed;
        for (let i = 0, ch; i < str.length; i += 1) {
            ch = str.charCodeAt(i);
            h1 = Math.imul(h1 ^ ch, 2654435761);
            h2 = Math.imul(h2 ^ ch, 1597334677);
        }
        h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
        h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
        return (h2 >>> 0).toString(16).padStart(8, 0) + (h1 >>> 0).toString(16).padStart(8, 0);
    }

    exports.cypher = {
        algorithmRSA
        , algorithmAES
        , generateKeyPair
        , generateKeyPairForExport
        , getRSAKey
        , getRSAPrivateKey
        , getAESKey
        , encryptAES
        , decryptRSA
        , decryptAES
    };
}('undefined' !== typeof exports && exports || 'undefined' !== typeof window && window || global));
