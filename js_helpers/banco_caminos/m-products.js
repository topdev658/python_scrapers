import serviceProducts from '@services/s-products';
import { intervenersByTitle } from '@modules/products/product-interveners';
import { typesByTitle } from '@modules/products/product-types';
import { subtypesByTitle, subtypesById } from '@modules/products/product-subtypes';
import productFamilies from '@modules/products/product-families';
import sumAmounts from '@modules/products/product-sum-amounts';
import SessionCache from '@modules/session/session-cache';
import categorizeProducts from '@modules/products/product-sort';

const UPDATE_TIMESTAMP = 'UPDATE_TIMESTAMP';

const cache = new SessionCache('products');
const cacheKey = 'list';

export default {
    namespaced: true,

    state() {
        return {
            lastRequestTimestamp: null,
        };
    },

    mutations: {
        [UPDATE_TIMESTAMP](state, value) {
            state.lastRequestTimestamp = value;
        },
    },

    actions: {
        fetch({ commit, dispatch }, { refresh } = {}) {
            if (!refresh && cache.has(cacheKey)) {
                return cache.get(cacheKey);
            }

            SessionCache.clear('products');

            return dispatch(
                'service/request',
                {
                    service: serviceProducts,
                    params: { id: '' },
                },
                { root: true }
            ).then(async ({ data: { data } }) => {
                /* istanbul ignore next */
                if (!data?.length) {
                    commit(UPDATE_TIMESTAMP, new Date());
                    return [];
                }

                const collection = categorizeProducts(data);

                // Si existen carteras gestionadas, recuperamos los productos asociados a ellas
                const promises = collection
                    .filter(({ productType: { id } }) => id === typesByTitle['managed-portfolio'])
                    .map(async ({ id }) => {
                        const managedProducts = await dispatch('getPortfolio', { productId: id });

                        // Completamos el modelo agregando:
                        // 1. parentId para asociar el producto a la cartera gestionada
                        // 2. productSubtype sintético para diferenciar una cuenta gestionada de una cuenta
                        // 3. relationType de manera temporal, hasta que lo arreglen del servicio
                        const normalizedManagedProducts = managedProducts.map((product) => ({
                            ...product,
                            parentId: id,
                            productSubtype: { id: `m-${product.productSubtype.id}` },

                            // Está información no viene actualmente del servicio
                            // y debemos falsearla hasta que lo corrijan
                            // todo: eliminar cuando esté en el servicio
                            relationType: { id: '01' },
                        }));

                        return categorizeProducts(normalizedManagedProducts);
                    });

                const managedProducts = await Promise.all(promises);

                if (managedProducts) {
                    collection.push(...managedProducts.flat());
                }

                commit(UPDATE_TIMESTAMP, new Date());

                cache.set(cacheKey, collection);

                return collection;
            });
        },

        getPosition({ dispatch }, { productId }) {
            const key = `position/${productId}`;
            if (cache.has(key)) {
                return cache.get(key);
            }

            return dispatch(
                'service/request',
                {
                    service: serviceProducts,
                    params: { id: `${productId}/position` },
                },
                { root: true }
            )
                .then(({ data }) => {
                    cache.set(key, data);
                    return data;
                })
                .catch(() => {});
        },

        getPortfolio({ dispatch }, { productId }) {
            return dispatch(
                'service/request',
                {
                    service: serviceProducts,
                    params: { id: `${productId}/managedProducts` },
                },
                { root: true }
            )
                .then(({ data: { data } }) => data)
                .catch(() => {});
        },

        getCardCVV({ dispatch }, { productId }) {
            return dispatch(
                'service/request',
                {
                    service: serviceProducts,
                    params: { id: `${productId}/cvv` },
                },
                { root: true }
            ).then(({ data: { cvv } }) => cvv);
        },

        getCardPIN({ dispatch }, { productId }) {
            return dispatch(
                'service/request',
                {
                    service: serviceProducts,
                    params: { id: `${productId}/pin` },
                },
                { root: true }
            ).then(({ data: { pin } }) => pin);
        },

        byService({ dispatch }, byService) {
            const method = 'GET';
            const url = '/products';

            return dispatch(
                'service/request',
                {
                    service: { request: { url, method } },
                    queryParams: { byService },
                },
                { root: true }
            ).then(({ data: { data } }) => {
                /* istanbul ignore next */
                if (!data?.length) {
                    return;
                }

                const collection = categorizeProducts(data);

                return collection;
            });
        },

        async get({ dispatch }, id) {
            if (!cache.has(cacheKey)) {
                await dispatch('fetch');
            }

            const cacheResult = cache.get(cacheKey);
            const result = cacheResult.find(({ id: itemId }) => itemId === id);

            if (!result) {
                return Promise.reject();
            }

            return result;
        },

        getDetails({ dispatch }, id) {
            if (id.includes('/')) {
                const parts = id.split('/');
                const [productId, resource, resourceId] = parts;

                return dispatch('resources/get', { resource, productId, resourceId }, { root: true });
            }

            return dispatch(
                'service/request',
                {
                    service: serviceProducts,
                    params: { id },
                },
                { root: true }
            )
                .then(({ data }) => data)
                .catch(() => {});
        },

        getSiblings(store, id) {
            if (cache.has(cacheKey)) {
                const families = cache.get(cacheKey).reduce((reducer, item) => {
                    const productSubtype = subtypesById[item.productSubtype.id];
                    const fams = Object.entries(productFamilies);
                    const familyResult = fams.find(([, group]) => group.includes(productSubtype));

                    if (familyResult) {
                        const [family] = familyResult;

                        if (!reducer[family]) {
                            // eslint-disable-next-line no-param-reassign
                            reducer[family] = [];
                        }

                        reducer[family].push(item);
                    }

                    return reducer;
                }, {});

                const [family] = Object.entries(families).find(([, group]) =>
                    group.find(({ id: productId }) => productId === id)
                );

                return families[family];
            }

            return [];
        },

        getReceipt({ dispatch }, { productId, movementId, query = {}, reportType = 'pdf' }) {
            const urlDetail = `/products/${productId}/movements/${movementId}/document`;
            const urlList = `/products/${productId}/movements/document`;
            const method = 'GET';
            const url = movementId ? urlDetail : urlList;

            return dispatch(
                'service/request',
                {
                    service: { request: { url, method } },
                    queryParams: { reportType, ...query },
                },
                { root: true }
            ).then(({ data: { content } }) => content);
        },
    },

    getters: {
        balance: ({ lastRequestTimestamp }) => {
            if (lastRequestTimestamp && cache.has(cacheKey)) {
                const results = cache.get(cacheKey);

                return sumAmounts(results, 'balance', ({ productType, productSubtype, relationType }) => {
                    const isLegalRepresentative =
                        relationType.id === intervenersByTitle['legal-representative'];
                    const isAttorney = relationType.id === intervenersByTitle.attorney;
                    const isHolder = relationType.id === intervenersByTitle.holder;
                    const isAccount = productType.id === typesByTitle.account;
                    const isDeposit = productType.id === typesByTitle.deposit;
                    const isPremiumAccount = productSubtype.id === subtypesByTitle['premium-account'];
                    const isPremiumDeposit = productSubtype.id === subtypesByTitle['premium-deposit'];
                    const isNotManaged = !productSubtype.id.startsWith('m-');

                    // Sólo suman en el balance los productos que son de los siguientes tipos.
                    const isElegible = isAccount || isDeposit || isPremiumAccount || isPremiumDeposit;

                    return isElegible && (isHolder || isLegalRepresentative || isAttorney) && isNotManaged;
                });
            }
        },
    },
};
