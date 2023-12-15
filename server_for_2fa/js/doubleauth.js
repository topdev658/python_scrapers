;function app2FAInit(srvUrl, app, appElId, customerIdVarName, fetchInterval) {
    // variables/fields received from API are under_scored
    // variables created here are camelCased

    app.pageData = {
        // list of queries in format
        // {query_id: {query_id: str, question: str, answer: str, status: str}, ...}
        queries: {}
    };

    // Add the query to pageData if it not exists yet
    app.processNewQuery = function (q) {
        // add new query to pageData
        var qId = q.query_id;
        if (app.pageData.queries[qId]) return;
        console.debug('new query: ' + qId);
        app.pageData.queries[qId] = q;
    };

    // Read user input
    // Upd query for backend
    // Upd qyery as pageData
    app.processQuerySubmit = function (q) {
        var qId = q.query_id;
        return function (e) {
            var qClone = {};
            Object.assign(qClone, q);
            var inpEl = document.getElementById('inp_' + qId);
            var btnEl = document.getElementById('btn_' + qId);

            // handle empty
            if (inpEl.value.length === 0) return;

            qClone.answer = inpEl.value;
            qClone.status = 'answered';
            inpEl.disabled = true;
            btnEl.disabled = true;

            m.request({
                method: "PUT",
                url: srvUrl + "/api/v1/q",
                timeout: 10000,
                body: qClone,
            }).then(function (respObj) {
                // clean up possible reusable els
                inpEl.value = '';
                inpEl.disabled = false;
                btnEl.disabled = false;

                if (respObj.meta.code !== 200) {
                    console.warn('failed answer for ' + qId + ' ' + JSON.stringify(respObj))
                } else {
                    console.debug('answered for ' + qId + ' ' + respObj.status);
                    // delete on success to be ready for the next same queries
                    delete app.pageData.queries[qId];
                    console.log('cleared')
                }
            }).catch(function (e) {
                inpEl.disabled = false;
                btnEl.disabled = false;
                console.warn(e)
            })
        }
    };

    app.fetchNewQueries = function () {
        m.request({
            method: "GET",
            url: srvUrl + "/api/v1/q/" + window[customerIdVarName] + "/new",
            timeout: 10000
        }).then(function (respObj) {
            console.debug('fetched new queries');
            var queries = respObj.data.queries || [];
            queries.forEach(function (q) {
                app.processNewQuery(q)
            })
        }).catch(function (e) {
            console.warn(e)
        })
    };

    app.QueriesList = {
        oninit: setInterval(app.fetchNewQueries, fetchInterval),
        view: function () {
            var qIds = Object.keys(app.pageData.queries).filter(function (qId) {
                // more explicit here than Object.entries();
                return app.pageData.queries[qId].status === 'new'
            });
            return qIds.length === 0
                ? null
                : m('div', [
                    // subtitle
                    m('h2', '2FA'),
                    qIds.map(function (qId) {
                        var q = app.pageData.queries[qId];
                        var inpId = 'inp_' + qId;
                        var btnId = 'btn_' + qId;
                        // one query input
                        return (
                            m('div.control-group', {style: 'margin-top:20px;'}, [
                                m('div', [
                                    m('label', {
                                        class: 'control-label',
                                        for: inpId
                                    }, q.question)
                                ]),
                                m('div', [
                                    m('input', {
                                        id: inpId,
                                        class: 'field'
                                    })
                                ]),

                                m('div', [
                                    m('button.btn.btn-success', {
                                        id: btnId,
                                        type: 'submit',
                                        onclick: app.processQuerySubmit(q),
                                        style: 'margin-top: 10px;'
                                    }, 'Enviar')
                                ]),
                            ])
                        )
                    })
                ])
        }
    };

    var appEl = document.getElementById(appElId);
    m.mount(appEl, app.QueriesList);
}