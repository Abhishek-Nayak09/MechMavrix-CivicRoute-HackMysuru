// ============================================================
// MECHMAVRIX CIVICROUTE
// SERVICE WORKER — OFFLINE APP SHELL
// ============================================================

const CACHE_NAME =
    "civicroute-shell-v1";


const CORE_ASSETS = [

    "/",

    "/track",

    "/static/styles.css",

    "/static/app.js",

    "/static/offline-db.js",

    "/static/track.js",

    "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",

    "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
];


// ============================================================
// INSTALL
// ============================================================

self.addEventListener(
    "install",
    event => {

        event.waitUntil(

            caches
                .open(
                    CACHE_NAME
                )
                .then(
                    async cache => {

                        for (
                            const asset
                            of CORE_ASSETS
                        ) {

                            try {

                                await cache.add(
                                    asset
                                );

                            }

                            catch (error) {

                                console.warn(
                                    "Unable to pre-cache:",
                                    asset,
                                    error
                                );
                            }
                        }
                    }
                )
        );


        self.skipWaiting();
    }
);


// ============================================================
// ACTIVATE
// ============================================================

self.addEventListener(
    "activate",
    event => {

        event.waitUntil(

            caches
                .keys()
                .then(
                    cacheNames => {

                        return Promise.all(

                            cacheNames.map(
                                cacheName => {

                                    if (
                                        cacheName !==
                                        CACHE_NAME
                                    ) {

                                        return caches.delete(
                                            cacheName
                                        );
                                    }

                                    return null;
                                }
                            )
                        );
                    }
                )
        );


        self.clients.claim();
    }
);


// ============================================================
// FETCH
// ============================================================

self.addEventListener(
    "fetch",
    event => {

        const request =
            event.request;


        // ----------------------------------------------------
        // API WRITES
        //
        // Never fake/cache complaint submissions.
        // app.js handles offline POST queue using IndexedDB.
        // ----------------------------------------------------

        if (
            request.method !==
            "GET"
        ) {

            return;
        }


        const url =
            new URL(
                request.url
            );


        // ----------------------------------------------------
        // API GET REQUESTS
        //
        // Do not cache complaint/status APIs because users
        // should see current server state whenever online.
        // ----------------------------------------------------

        if (
            url.origin ===
            self.location.origin

            &&

            url.pathname.startsWith(
                "/api/"
            )
        ) {

            return;
        }


        // ----------------------------------------------------
        // PAGE NAVIGATION
        //
        // Network first. If offline, serve cached page shell.
        // ----------------------------------------------------

        if (
            request.mode ===
            "navigate"
        ) {

            event.respondWith(

                fetch(
                    request
                )
                .then(
                    response => {

                        const copy =
                            response.clone();


                        caches
                            .open(
                                CACHE_NAME
                            )
                            .then(
                                cache => {

                                    cache.put(
                                        request,
                                        copy
                                    );
                                }
                            );


                        return response;
                    }
                )
                .catch(
                    async () => {

                        const exact =
                            await caches.match(
                                request
                            );


                        if (exact) {

                            return exact;
                        }


                        return caches.match(
                            "/"
                        );
                    }
                )
            );


            return;
        }


        // ----------------------------------------------------
        // STATIC ASSETS
        //
        // Cache first, network fallback.
        // ----------------------------------------------------

        event.respondWith(

            caches
                .match(
                    request
                )
                .then(
                    cached => {

                        if (cached) {

                            return cached;
                        }


                        return fetch(
                            request
                        )
                        .then(
                            response => {

                                if (
                                    !response
                                    ||
                                    response.status !== 200
                                ) {

                                    return response;
                                }


                                const copy =
                                    response.clone();


                                caches
                                    .open(
                                        CACHE_NAME
                                    )
                                    .then(
                                        cache => {

                                            cache.put(
                                                request,
                                                copy
                                            );
                                        }
                                    );


                                return response;
                            }
                        );
                    }
                )
        );
    }
);