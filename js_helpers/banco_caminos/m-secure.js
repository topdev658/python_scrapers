// FROM webpack://src/store/secure

import publicService from '@modules/service/m-public-service';
import sKeyExchange from '@services/s-key-exchange';
import { generateKeyPair, decryptRSA, encryptAES, decryptAES, getAESKey } from './cypher';

const SET_SESSION_DATA = 'SET_SESSION_DATA';
const CLEAN_SESSION_DATA = 'CLEAN_SESSION_DATA';
const SET_AES_KEY = 'SET_AES_KEY';

export default {
    namespaced: true,

    modules: { publicService },

    /**
     * @typedef {Object} state
     * @property {Object} keyPair Crypto Key pair
     * @property {String} publicKey Base64 encoded public key
     * @property {Object} aesKey Crypto Symmetric Key
     * @property {String} seed Base64 encoded seed for AES
     * @property {String} symmetricKey Base64 encoded key for AES
     * @property {String} uuid Unique Session Id
     */
    state() {
        return {
            aesKey: null,
            seed: null,
            symmetricKey: null,
            uuid: null,
            identity: null,
        };
    },

    mutations: {
        [SET_SESSION_DATA](state, { seed, symmetricKey, uuid }) {
            state.seed = seed;
            state.symmetricKey = symmetricKey;
            state.uuid = uuid;
            state.identity = Symbol(uuid);
            state.aesKey = null;
        },

        [CLEAN_SESSION_DATA](state) {
            state.seed = null;
            state.symmetricKey = null;
            state.uuid = null;
            state.identity = null;
            state.aesKey = null;
        },

        [SET_AES_KEY](state, key) {
            state.aesKey = key;
        },
    },

    actions: {
        /**
         * Create a new session with a new uuid.
         * @param {Object} store
         * @param {state} store.state
         */
        async createSession({ dispatch, rootState }) {
            const { privateKey, publicKey } = await generateKeyPair();

            return new Promise((resolve, reject) => {
                dispatch('publicService/request', {
                    baseURL: rootState.service.baseURL,
                    headers: {
                        'Content-Type': 'application/json',
                        'public-key': publicKey,
                    },
                    ...sKeyExchange.request,
                })
                    .then(async (req) => {
                        const { data } = req;

                        if (data) {
                            const response = await decryptRSA(privateKey, data);
                            await dispatch('setSession', response);
                            return resolve(response);
                        }

                        reject(req);
                    })
                    .catch(reject);
            });
        },

        /**
         * Save and persist a session.
         * @param {Object} store
         * @param {Object} sessionData
         */
        setSession({ commit }, sessionData) {
            commit(SET_SESSION_DATA, sessionData);
        },

        /**
         * Close current session.
         * @param {Object} store
         */
        removeSession({ commit }) {
            commit(CLEAN_SESSION_DATA);
        },

        /**
         * Destroy and create a new session and set a new uuid.
         * @param {Object} store
         */
        refreshSession({ dispatch }) {
            dispatch('removeSession');
            return dispatch('createSession');
        },

        /**
         * Returns the crypto AES Key.
         * @param {Object} store
         * @param {state} store.state
         * @returns {Object} Crypto AES Key.
         */
        async getAESKey({ dispatch, commit, state }) {
            if (!state.uuid) {
                await dispatch('createSession');
            }

            const { symmetricKey, aesKey } = state;

            if (!aesKey) {
                const cryptoKey = await getAESKey(symmetricKey);

                commit(SET_AES_KEY, cryptoKey);
                return cryptoKey;
            }

            return aesKey;
        },

        /**
         * Encrypt data with the symmetric key.
         * @param {store} store
         * @param {state} store.state
         * @param {Object} payload Data to encrypt
         * @returns {String} A base64 encrypted data
         */
        async encrypt({ state, dispatch }, data) {
            const key = await dispatch('getAESKey');
            const { seed } = state;

            return encryptAES({ seed, key, data });
        },

        /**
         * Decrypt a base64 string with the symmetric key.
         * @param {store} store
         * @param {state} store.state
         * @param {String} data A base64 string data to decrypt.
         * @returns {Object} A clean payload.
         */
        async decrypt({ state, dispatch }, data) {
            const key = await dispatch('getAESKey');
            const { seed } = state;

            return decryptAES({ seed, key, data });
        },
    },
};
