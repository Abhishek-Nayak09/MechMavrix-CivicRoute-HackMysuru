// ============================================================
// MECHMAVRIX CIVICROUTE
// OFFLINE COMPLAINT QUEUE — INDEXEDDB
// ============================================================

const CIVICROUTE_DB_NAME =
    "CivicRouteOfflineDB";

const CIVICROUTE_DB_VERSION =
    1;

const CIVICROUTE_STORE =
    "pendingComplaints";


// ============================================================
// OPEN DATABASE
// ============================================================

function openOfflineDatabase() {

    return new Promise(
        (resolve, reject) => {

            const request =
                indexedDB.open(
                    CIVICROUTE_DB_NAME,
                    CIVICROUTE_DB_VERSION
                );


            request.onupgradeneeded =
                event => {

                    const database =
                        event.target.result;


                    if (
                        !database.objectStoreNames.contains(
                            CIVICROUTE_STORE
                        )
                    ) {

                        const store =
                            database.createObjectStore(
                                CIVICROUTE_STORE,
                                {
                                    keyPath:
                                        "offline_id"
                                }
                            );


                        store.createIndex(
                            "created_at",
                            "created_at",
                            {
                                unique:
                                    false
                            }
                        );
                    }
                };


            request.onsuccess =
                () => {

                    resolve(
                        request.result
                    );
                };


            request.onerror =
                () => {

                    reject(
                        request.error
                    );
                };
        }
    );
}


// ============================================================
// GENERATE OFFLINE ID
// ============================================================

function generateOfflineId() {

    return (
        "OFFLINE-" +
        Date.now() +
        "-" +
        Math.random()
            .toString(16)
            .slice(2, 8)
            .toUpperCase()
    );
}


// ============================================================
// SAVE PENDING COMPLAINT
// ============================================================

async function saveOfflineComplaint(
    complaint
) {

    const database =
        await openOfflineDatabase();


    const record = {

        ...complaint,

        offline_id:
            complaint.offline_id
            ||
            generateOfflineId(),

        created_at:
            complaint.created_at
            ||
            new Date().toISOString(),

        sync_status:
            "PENDING"
    };


    return new Promise(
        (resolve, reject) => {

            const transaction =
                database.transaction(
                    CIVICROUTE_STORE,
                    "readwrite"
                );


            const store =
                transaction.objectStore(
                    CIVICROUTE_STORE
                );


            const request =
                store.put(
                    record
                );


            request.onsuccess =
                () => {

                    resolve(
                        record
                    );
                };


            request.onerror =
                () => {

                    reject(
                        request.error
                    );
                };


            transaction.oncomplete =
                () => {

                    database.close();
                };
        }
    );
}


// ============================================================
// GET ALL PENDING COMPLAINTS
// ============================================================

async function getOfflineComplaints() {

    const database =
        await openOfflineDatabase();


    return new Promise(
        (resolve, reject) => {

            const transaction =
                database.transaction(
                    CIVICROUTE_STORE,
                    "readonly"
                );


            const store =
                transaction.objectStore(
                    CIVICROUTE_STORE
                );


            const request =
                store.getAll();


            request.onsuccess =
                () => {

                    const records =
                        request.result || [];


                    records.sort(
                        (a, b) =>
                            new Date(
                                a.created_at
                            )
                            -
                            new Date(
                                b.created_at
                            )
                    );


                    resolve(
                        records
                    );
                };


            request.onerror =
                () => {

                    reject(
                        request.error
                    );
                };


            transaction.oncomplete =
                () => {

                    database.close();
                };
        }
    );
}


// ============================================================
// DELETE AFTER SUCCESSFUL SYNC
// ============================================================

async function deleteOfflineComplaint(
    offlineId
) {

    const database =
        await openOfflineDatabase();


    return new Promise(
        (resolve, reject) => {

            const transaction =
                database.transaction(
                    CIVICROUTE_STORE,
                    "readwrite"
                );


            const store =
                transaction.objectStore(
                    CIVICROUTE_STORE
                );


            const request =
                store.delete(
                    offlineId
                );


            request.onsuccess =
                () => {

                    resolve(
                        true
                    );
                };


            request.onerror =
                () => {

                    reject(
                        request.error
                    );
                };


            transaction.oncomplete =
                () => {

                    database.close();
                };
        }
    );
}


// ============================================================
// COUNT PENDING
// ============================================================

async function countOfflineComplaints() {

    const database =
        await openOfflineDatabase();


    return new Promise(
        (resolve, reject) => {

            const transaction =
                database.transaction(
                    CIVICROUTE_STORE,
                    "readonly"
                );


            const store =
                transaction.objectStore(
                    CIVICROUTE_STORE
                );


            const request =
                store.count();


            request.onsuccess =
                () => {

                    resolve(
                        request.result || 0
                    );
                };


            request.onerror =
                () => {

                    reject(
                        request.error
                    );
                };


            transaction.oncomplete =
                () => {

                    database.close();
                };
        }
    );
}


// ============================================================
// CLEAR ALL
// ============================================================

async function clearOfflineComplaints() {

    const database =
        await openOfflineDatabase();


    return new Promise(
        (resolve, reject) => {

            const transaction =
                database.transaction(
                    CIVICROUTE_STORE,
                    "readwrite"
                );


            const store =
                transaction.objectStore(
                    CIVICROUTE_STORE
                );


            const request =
                store.clear();


            request.onsuccess =
                () => {

                    resolve(
                        true
                    );
                };


            request.onerror =
                () => {

                    reject(
                        request.error
                    );
                };


            transaction.oncomplete =
                () => {

                    database.close();
                };
        }
    );
}