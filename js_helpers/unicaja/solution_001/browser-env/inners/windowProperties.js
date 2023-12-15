function defineProperties(window, globalVariables, isLinux) {
    Object.defineProperties(window, {
        'WritableStreamDefaultController': {},
        'VirtualKeyboardGeometryChangeEvent': {},
        'TransformStreamDefaultController': {},
        'SVGComponentTransferFunctionElement': {},
        'SVGAnimatedPreserveAspectRatio': {},
        'ReadableStreamDefaultController': {},
        'RTCPeerConnectionIceErrorEvent': {},
        'OffscreenCanvasRenderingContext2D': {},
        'NavigationCurrentEntryChangeEvent': {},
        'MediaStreamAudioDestinationNode': {},
        'WebTransportBidirectionalStream': {},
        'WebTransportDatagramDuplexStream': {},
        'AuthenticatorAssertionResponse': {},
        'AuthenticatorAttestationResponse': {},
    });
    if (!isLinux) {
        Object.defineProperties(window, {
            'BluetoothCharacteristicProperties': {},
            'BluetoothRemoteGATTCharacteristic': {},
        });
    }
    Object.defineProperties(window, {
        'PresentationConnectionAvailableEvent': {},
        'PresentationConnectionCloseEvent': {},
        'USBIsochronousInTransferPacket': {},
        'USBIsochronousInTransferResult': {},
        'USBIsochronousOutTransferPacket': {},
        'USBIsochronousOutTransferResult': {},
        'WindowControlsOverlayGeometryChangeEvent': {},
        'oncontentvisibilityautostatechange': {},
        'BrowserCaptureMediaStreamTrack': {},
        'isSecureContext': {
            get: () => true
        },
        'crossOriginIsolated': {
            get: () => false
        },
        'PERSISTENT': {
            get: () => 1,
        },
        'TEMPORARY': {
            get: () => 0,
        },
        "CSSStartingStyleRule": {},
        "ContentVisibilityAutoStateChangeEvent": {},
        "DelegatedInkTrailPresenter": {},
        "Ink": {},
        "DocumentPictureInPictureEvent": {},
        "Highlight": {},
        "HighlightRegistry": {},
        "MediaMetadata": {},
        "MediaSession": {},
        "MutationEvent": {},
        "NavigatorUAData": {},
        "Notification": {},
        "PaymentManager": {},
        "PaymentRequestUpdateEvent": {},
        "PeriodicSyncManager": {},
        "PermissionStatus": {},
        "Permissions": {},
        "PushManager": {},
        "PushSubscription": {},
        "PushSubscriptionOptions": {},
        "RemotePlayback": {},
        "ScrollTimeline": {},
        "ViewTimeline": {},
        "SharedWorker": {},
        "SpeechSynthesisErrorEvent": {},
        "SpeechSynthesisEvent": {},
        "SpeechSynthesisUtterance": {},
        "VideoPlaybackQuality": {},
        "ViewTransition": {},
        "VisibilityStateEntry": {},
        "webkitSpeechGrammar": {},
        "webkitSpeechGrammarList": {},
        "webkitSpeechRecognition": {},
        "webkitSpeechRecognitionError": {},
        "webkitSpeechRecognitionEvent": {},
        "webkitRequestFileSystem": {},
        "webkitResolveLocalFileSystemURL": {},
    })

    Object.defineProperties(window, {
        'geetestLang': {
            value: undefined,
        },
        'recaptchaLang': {
            value: undefined,
        },
        'onProtectionInitialized': {
            value: function(protection) {},
        },
        'reeseSkipExpirationCheck': {
            value: true,
        }
    });

    globalVariables.forEach(it => {
        Object.defineProperty(window, it, {});
    });
}

module.exports = defineProperties;
