// ============================================================
// MECHMAVRIX CIVICROUTE
// SERVICE WORKER REGISTRATION
// ============================================================

if ("serviceWorker" in navigator) {

    window.addEventListener(
        "load",
        async () => {

            try {

                const registration =
                    await navigator.serviceWorker.register(
                        "/sw.js",
                        {
                            scope: "/"
                        }
                    );

                console.log(
                    "CivicRoute Service Worker registered:",
                    registration.scope
                );

            } catch (error) {

                console.error(
                    "CivicRoute Service Worker registration failed:",
                    error
                );
            }
        }
    );
}