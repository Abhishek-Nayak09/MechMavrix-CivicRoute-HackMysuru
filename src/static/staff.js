// ============================================================
// MECHMAVRIX CIVICROUTE
// STAFF DASHBOARD
// ============================================================


// ============================================================
// DOM
// ============================================================

const complaintList =
    document.getElementById("complaintList");

const statusFilter =
    document.getElementById("statusFilter");

const searchInput =
    document.getElementById("searchInput");

const refreshButton =
    document.getElementById("refreshButton");


const statTotal =
    document.getElementById("statTotal");

const statNew =
    document.getElementById("statNew");

const statAssigned =
    document.getElementById("statAssigned");

const statProgress =
    document.getElementById("statProgress");

const statResolved =
    document.getElementById("statResolved");


// ============================================================
// STATE
// ============================================================

let allComplaints = [];


// ============================================================
// SAFE HTML
// ============================================================

function escapeHtml(value) {

    return String(
        value ?? ""
    )
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// ============================================================
// FORMAT DATE
// ============================================================

function formatDateTime(
    value
) {

    if (!value) {

        return "-";
    }


    const date =
        new Date(
            value
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return value;
    }


    return date.toLocaleString(
        "en-IN",
        {

            dateStyle:
                "medium",

            timeStyle:
                "short"
        }
    );
}


// ============================================================
// PRIORITY SORT VALUE
// ============================================================

function priorityRank(
    priority
) {

    const ranks = {

        "CRITICAL": 5,

        "HIGH": 4,

        "MEDIUM": 3,

        "LOW": 2,

        "REVIEW REQUIRED": 1
    };


    return (
        ranks[
            priority
        ] || 0
    );
}


// ============================================================
// UPDATE STATS
// ============================================================

function updateStats() {

    statTotal.textContent =
        allComplaints.length;


    statNew.textContent =
        allComplaints.filter(
            complaint =>
                complaint.status === "NEW"
        ).length;


    statAssigned.textContent =
        allComplaints.filter(
            complaint =>
                complaint.status === "ASSIGNED"
        ).length;


    statProgress.textContent =
        allComplaints.filter(
            complaint =>
                complaint.status === "IN PROGRESS"
        ).length;


    statResolved.textContent =
        allComplaints.filter(
            complaint =>
                complaint.status === "RESOLVED"
        ).length;
}


// ============================================================
// FILTER
// ============================================================

function getFilteredComplaints() {

    const selectedStatus =
        statusFilter.value;


    const searchTerm =
        searchInput.value
            .trim()
            .toLowerCase();


    let filtered =
        [...allComplaints];


    if (
        selectedStatus
    ) {

        filtered =
            filtered.filter(
                complaint =>
                    complaint.status ===
                    selectedStatus
            );
    }


    if (
        searchTerm
    ) {

        filtered =
            filtered.filter(
                complaint => {

                    const haystack = [

                        complaint.complaint_id,

                        complaint.detected_issue,

                        complaint.detected_severity,

                        complaint.responsible_authority,

                        complaint.department,

                        complaint.detected_address,

                        complaint.priority,

                        complaint.status,

                        complaint.assigned_to

                    ]
                        .join(" ")
                        .toLowerCase();


                    return (
                        haystack.includes(
                            searchTerm
                        )
                    );
                }
            );
    }


    filtered.sort(
        (a, b) => {

            const priorityDifference =
                priorityRank(
                    b.priority
                )
                -
                priorityRank(
                    a.priority
                );


            if (
                priorityDifference !== 0
            ) {

                return (
                    priorityDifference
                );
            }


            return (
                new Date(
                    b.created_at
                )
                -
                new Date(
                    a.created_at
                )
            );
        }
    );


    return filtered;
}


// ============================================================
// STATUS BUTTONS
// ============================================================

function buildActionButtons(
    complaint
) {

    const id =
        escapeHtml(
            complaint.complaint_id
        );


    let buttons = "";


    if (
        complaint.status === "NEW"
        ||
        complaint.status === "REVIEW REQUIRED"
    ) {

        buttons += `
            <button
                class="action-button primary"
                type="button"
                data-action="assign"
                data-id="${id}"
            >
                Assign
            </button>
        `;
    }


    if (
        complaint.status === "ASSIGNED"
    ) {

        buttons += `
            <button
                class="action-button primary"
                type="button"
                data-action="progress"
                data-id="${id}"
            >
                Start Work
            </button>
        `;
    }


    if (
        complaint.status === "IN PROGRESS"
        ||
        complaint.status === "ASSIGNED"
    ) {

        buttons += `
            <button
                class="action-button"
                type="button"
                data-action="resolve"
                data-id="${id}"
            >
                Mark Resolved
            </button>
        `;
    }


    buttons += `
        <button
            class="action-button"
            type="button"
            data-action="history"
            data-id="${id}"
        >
            View History
        </button>
    `;


    return buttons;
}


// ============================================================
// RENDER ONE COMPLAINT
// ============================================================

function createComplaintCard(
    complaint
) {

    const card =
        document.createElement(
            "article"
        );


    card.className =
        "staff-complaint-card";


    const photoUrl =
        complaint.photo_url
        ||
        "";


    const photoHtml =
        photoUrl

        ? `
            <img
                class="staff-photo"
                src="${escapeHtml(photoUrl)}"
                alt="Complaint evidence"
                loading="lazy"
            >
          `

        : `
            <div
                class="staff-photo"
                style="
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    color:white;
                "
            >
                No photo available
            </div>
          `;


    card.innerHTML = `

        <div class="complaint-card-top">

            <div>

                <div class="complaint-number">
                    ${escapeHtml(
                        complaint.complaint_id
                    )}
                </div>

                <div class="complaint-time">
                    Submitted:
                    ${escapeHtml(
                        formatDateTime(
                            complaint.created_at
                        )
                    )}
                </div>

            </div>


            <div>

                <span class="status-pill">
                    ${escapeHtml(
                        complaint.status
                    )}
                </span>

                <span class="priority-pill">
                    ${escapeHtml(
                        complaint.priority
                    )}
                    •
                    ${escapeHtml(
                        complaint.priority_score
                    )}/100
                </span>

            </div>

        </div>


        <div class="complaint-card-body">

            <div>
                ${photoHtml}
            </div>


            <div class="complaint-details">


                <div class="detail-box">

                    <span>
                        Detected Issue
                    </span>

                    <strong>
                        ${escapeHtml(
                            complaint.detected_issue
                        )}
                    </strong>

                </div>


                <div class="detail-box">

                    <span>
                        Severity
                    </span>

                    <strong>
                        ${escapeHtml(
                            complaint.detected_severity
                        )}
                    </strong>

                </div>


                <div class="detail-box">

                    <span>
                        Location Risk
                    </span>

                    <strong>
                        ${escapeHtml(
                            complaint.location_risk
                        )}
                        (${escapeHtml(
                            complaint.location_score
                        )}/50)
                    </strong>

                </div>


                <div class="detail-box">

                    <span>
                        Responsible Authority
                    </span>

                    <strong>
                        ${escapeHtml(
                            complaint.responsible_authority
                        )}
                    </strong>

                </div>


                <div class="detail-box">

                    <span>
                        Department
                    </span>

                    <strong>
                        ${escapeHtml(
                            complaint.department
                        )}
                    </strong>

                </div>


                <div class="detail-box">

                    <span>
                        Assigned To
                    </span>

                    <strong>
                        ${escapeHtml(
                            complaint.assigned_to
                            ||
                            "Not assigned"
                        )}
                    </strong>

                </div>


                <div class="detail-box">

                    <span>
                        GPS
                    </span>

                    <strong>
                        ${escapeHtml(
                            Number(
                                complaint.latitude
                            ).toFixed(6)
                        )},
                        ${escapeHtml(
                            Number(
                                complaint.longitude
                            ).toFixed(6)
                        )}
                    </strong>

                </div>


                <div class="detail-box">

                    <span>
                        AI Issue Confidence
                    </span>

                    <strong>
                        ${escapeHtml(
                            complaint.issue_confidence
                        )}%
                    </strong>

                </div>


                <div class="detail-box">

                    <span>
                        AI Severity Confidence
                    </span>

                    <strong>
                        ${escapeHtml(
                            complaint.severity_confidence
                        )}%
                    </strong>

                </div>


                <div
                    class="
                        detail-box
                        complaint-address
                    "
                >

                    <span>
                        Complaint Location
                    </span>

                    <strong>
                        ${escapeHtml(
                            complaint.detected_address
                        )}
                    </strong>

                </div>


                ${
                    complaint.description

                    ? `
                        <div
                            class="
                                detail-box
                                complaint-address
                            "
                        >

                            <span>
                                Citizen Description
                            </span>

                            <strong>
                                ${escapeHtml(
                                    complaint.description
                                )}
                            </strong>

                        </div>
                      `

                    : ""
                }


                ${
                    complaint.resolution_note

                    ? `
                        <div
                            class="
                                detail-box
                                complaint-address
                            "
                        >

                            <span>
                                Resolution Note
                            </span>

                            <strong>
                                ${escapeHtml(
                                    complaint.resolution_note
                                )}
                            </strong>

                        </div>
                      `

                    : ""
                }


                <div
                    id="history-${escapeHtml(
                        complaint.complaint_id
                    )}"
                    class="
                        detail-box
                        complaint-address
                    "
                    style="display:none;"
                >
                </div>

            </div>

        </div>


        <div class="complaint-actions">

            ${buildActionButtons(
                complaint
            )}

        </div>
    `;


    return card;
}


// ============================================================
// RENDER ALL
// ============================================================

function renderComplaints() {

    const complaints =
        getFilteredComplaints();


    complaintList.innerHTML =
        "";


    if (
        complaints.length === 0
    ) {

        complaintList.innerHTML = `
            <div class="empty-state">

                <strong>
                    No complaints found
                </strong>

                <br>

                No complaints match the current filter.

            </div>
        `;

        return;
    }


    complaints.forEach(
        complaint => {

            complaintList.appendChild(
                createComplaintCard(
                    complaint
                )
            );
        }
    );
}


// ============================================================
// LOAD COMPLAINTS
// ============================================================

async function loadComplaints() {

    complaintList.innerHTML = `
        <div class="loading-state">
            Loading routed complaints...
        </div>
    `;


    refreshButton.disabled =
        true;


    try {

        const response =
            await fetch(
                "/api/staff/complaints"
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Unable to load complaints."
            );
        }


        allComplaints =
            data.complaints || [];


        updateStats();

        renderComplaints();

    }

    catch (error) {

        console.error(
            error
        );


        complaintList.innerHTML = `
            <div class="empty-state">

                <strong>
                    Dashboard unavailable
                </strong>

                <br>

                ${escapeHtml(
                    error.message
                )}

            </div>
        `;

    }

    finally {

        refreshButton.disabled =
            false;
    }
}


// ============================================================
// ASSIGN COMPLAINT
// ============================================================

async function assignComplaint(
    complaintId
) {

    const assignedTo =
        window.prompt(
            "Assign this complaint to officer/team:"
        );


    if (
        !assignedTo ||
        !assignedTo.trim()
    ) {

        return;
    }


    await postJson(
        `/api/staff/complaints/${encodeURIComponent(
            complaintId
        )}/assign`,
        {

            assigned_to:
                assignedTo.trim()
        }
    );


    await loadComplaints();
}


// ============================================================
// START WORK
// ============================================================

async function startWork(
    complaintId
) {

    await postJson(
        `/api/staff/complaints/${encodeURIComponent(
            complaintId
        )}/status`,
        {

            status:
                "IN PROGRESS",

            note:
                "Civic staff started work on the complaint."
        }
    );


    await loadComplaints();
}


// ============================================================
// RESOLVE
// ============================================================

async function resolveComplaint(
    complaintId
) {

    const note =
        window.prompt(
            "Enter resolution note / action taken:"
        );


    if (
        !note ||
        !note.trim()
    ) {

        return;
    }


    await postJson(
        `/api/staff/complaints/${encodeURIComponent(
            complaintId
        )}/resolve`,
        {

            resolution_note:
                note.trim()
        }
    );


    await loadComplaints();
}


// ============================================================
// HISTORY
// ============================================================

async function showHistory(
    complaintId
) {

    const container =
        document.getElementById(
            `history-${complaintId}`
        );


    if (!container) {

        return;
    }


    if (
        container.style.display !==
        "none"
    ) {

        container.style.display =
            "none";

        return;
    }


    container.style.display =
        "block";


    container.innerHTML =
        "Loading complaint history...";


    try {

        const response =
            await fetch(
                `/api/staff/complaints/${encodeURIComponent(
                    complaintId
                )}/history`
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Unable to load history."
            );
        }


        const history =
            data.history || [];


        if (
            history.length === 0
        ) {

            container.innerHTML =
                "<strong>No history available.</strong>";

            return;
        }


        container.innerHTML = `

            <span>
                Complaint Audit History
            </span>

            ${history.map(
                event => `

                    <div
                        style="
                            padding:10px 0;
                            border-bottom:1px solid #e5e7eb;
                        "
                    >

                        <strong>
                            ${escapeHtml(
                                event.event_type
                            )}
                        </strong>

                        <br>

                        ${escapeHtml(
                            event.old_status || "-"
                        )}
                        →
                        ${escapeHtml(
                            event.new_status || "-"
                        )}

                        <br>

                        <small>
                            ${escapeHtml(
                                formatDateTime(
                                    event.timestamp
                                )
                            )}
                            •
                            ${escapeHtml(
                                event.actor
                            )}
                        </small>

                        ${
                            event.note

                            ? `
                                <br>
                                <small>
                                    ${escapeHtml(
                                        event.note
                                    )}
                                </small>
                              `

                            : ""
                        }

                    </div>

                `
            ).join("")}
        `;

    }

    catch (error) {

        container.innerHTML =
            `<strong>
                ${escapeHtml(
                    error.message
                )}
            </strong>`;
    }
}


// ============================================================
// POST JSON
// ============================================================

async function postJson(
    url,
    payload
) {

    const response =
        await fetch(
            url,
            {

                method:
                    "POST",

                headers: {

                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify(
                        payload
                    )
            }
        );


    const data =
        await response.json();


    if (
        !response.ok ||
        !data.success
    ) {

        throw new Error(
            data.error ||
            "Operation failed."
        );
    }


    return data;
}


// ============================================================
// ACTION CLICK HANDLER
// ============================================================

complaintList.addEventListener(
    "click",
    async event => {

        const button =
            event.target.closest(
                "[data-action]"
            );


        if (!button) {

            return;
        }


        const action =
            button.dataset.action;


        const complaintId =
            button.dataset.id;


        button.disabled =
            true;


        try {

            if (
                action === "assign"
            ) {

                await assignComplaint(
                    complaintId
                );
            }


            else if (
                action === "progress"
            ) {

                await startWork(
                    complaintId
                );
            }


            else if (
                action === "resolve"
            ) {

                await resolveComplaint(
                    complaintId
                );
            }


            else if (
                action === "history"
            ) {

                await showHistory(
                    complaintId
                );
            }

        }

        catch (error) {

            console.error(
                error
            );


            alert(
                error.message
            );

        }

        finally {

            button.disabled =
                false;
        }
    }
);


// ============================================================
// FILTER EVENTS
// ============================================================

statusFilter.addEventListener(
    "change",
    renderComplaints
);


searchInput.addEventListener(
    "input",
    renderComplaints
);


refreshButton.addEventListener(
    "click",
    loadComplaints
);


// ============================================================
// INITIAL LOAD
// ============================================================

loadComplaints();