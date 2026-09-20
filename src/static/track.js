// ============================================================
// MECHMAVRIX CIVICROUTE
// CITIZEN COMPLAINT TRACKING
// ============================================================


// ============================================================
// DOM
// ============================================================

const complaintIdInput =
    document.getElementById(
        "complaintIdInput"
    );

const trackButton =
    document.getElementById(
        "trackButton"
    );

const trackError =
    document.getElementById(
        "trackError"
    );

const trackResult =
    document.getElementById(
        "trackResult"
    );

const trackComplaintId =
    document.getElementById(
        "trackComplaintId"
    );

const trackStatus =
    document.getElementById(
        "trackStatus"
    );

const trackIssue =
    document.getElementById(
        "trackIssue"
    );

const trackPriority =
    document.getElementById(
        "trackPriority"
    );

const trackDepartment =
    document.getElementById(
        "trackDepartment"
    );

const trackAuthority =
    document.getElementById(
        "trackAuthority"
    );

const trackAssignedTo =
    document.getElementById(
        "trackAssignedTo"
    );

const trackCreatedAt =
    document.getElementById(
        "trackCreatedAt"
    );

const trackLocation =
    document.getElementById(
        "trackLocation"
    );

const resolutionBox =
    document.getElementById(
        "resolutionBox"
    );

const trackResolution =
    document.getElementById(
        "trackResolution"
    );

const trackTimeline =
    document.getElementById(
        "trackTimeline"
    );


// ============================================================
// SAFE HTML
// ============================================================

function escapeHtml(
    value
) {

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
// NORMALISE COMPLAINT ID
// ============================================================

function normaliseComplaintId(
    value
) {

    return String(
        value || ""
    )
        .trim()
        .toUpperCase();
}


// ============================================================
// SHOW ERROR
// ============================================================

function showError(
    message
) {

    trackError.textContent =
        message;


    trackError.classList.remove(
        "hidden"
    );


    trackResult.classList.add(
        "hidden"
    );
}


// ============================================================
// CLEAR ERROR
// ============================================================

function clearError() {

    trackError.textContent =
        "";


    trackError.classList.add(
        "hidden"
    );
}


// ============================================================
// RENDER TIMELINE
// ============================================================

function renderTimeline(
    history
) {

    trackTimeline.innerHTML =
        "";


    if (
        !Array.isArray(history) ||
        history.length === 0
    ) {

        trackTimeline.innerHTML = `

            <div class="timeline-event">

                <strong>
                    No history available
                </strong>

                <p>
                    No status events were found for this complaint.
                </p>

            </div>
        `;

        return;
    }


    history.forEach(
        event => {

            const eventElement =
                document.createElement(
                    "div"
                );


            eventElement.className =
                "timeline-event";


            const oldStatus =
                event.old_status || "-";


            const newStatus =
                event.new_status || "-";


            const statusText = (
                oldStatus === "-"
                &&
                newStatus !== "-"
            )

                ? `Status: ${newStatus}`

                : `${oldStatus} → ${newStatus}`;


            const noteHtml =
                event.note

                ? `
                    <p>
                        ${escapeHtml(
                            event.note
                        )}
                    </p>
                  `

                : "";


            eventElement.innerHTML = `

                <strong>
                    ${escapeHtml(
                        event.event_type
                        ||
                        "STATUS UPDATE"
                    )}
                </strong>

                <p>
                    ${escapeHtml(
                        statusText
                    )}
                </p>

                ${noteHtml}

                <small>
                    ${escapeHtml(
                        formatDateTime(
                            event.timestamp
                        )
                    )}

                    ${
                        event.actor

                        ? ` • ${escapeHtml(
                            event.actor
                          )}`

                        : ""
                    }
                </small>
            `;


            trackTimeline.appendChild(
                eventElement
            );
        }
    );
}


// ============================================================
// RENDER COMPLAINT
// ============================================================

function renderComplaint(
    complaint,
    history
) {

    trackComplaintId.textContent =
        complaint.complaint_id
        ||
        "-";


    trackStatus.textContent =
        complaint.status
        ||
        "-";


    trackIssue.textContent =
        complaint.detected_issue
        ||
        "-";


    const priority =
        complaint.priority
        ||
        "-";


    const priorityScore =
        complaint.priority_score;


    trackPriority.textContent =
        priorityScore !== null
        &&
        priorityScore !== undefined

        ? `${priority} (${priorityScore}/100)`

        : priority;


    trackDepartment.textContent =
        complaint.department
        ||
        "-";


    trackAuthority.textContent =
        complaint.responsible_authority
        ||
        "-";


    trackAssignedTo.textContent =
        complaint.assigned_to
        ||
        "Not assigned yet";


    trackCreatedAt.textContent =
        formatDateTime(
            complaint.created_at
        );


    trackLocation.textContent =
        complaint.detected_address
        ||
        "-";


    if (
        complaint.resolution_note
    ) {

        trackResolution.textContent =
            complaint.resolution_note;


        resolutionBox.classList.remove(
            "hidden"
        );

    }

    else {

        trackResolution.textContent =
            "-";


        resolutionBox.classList.add(
            "hidden"
        );
    }


    renderTimeline(
        history
    );


    trackResult.classList.remove(
        "hidden"
    );


    trackResult.scrollIntoView(
        {

            behavior:
                "smooth",

            block:
                "start"
        }
    );
}


// ============================================================
// TRACK COMPLAINT
// ============================================================

async function trackComplaint() {

    clearError();


    const complaintId =
        normaliseComplaintId(
            complaintIdInput.value
        );


    if (!complaintId) {

        showError(
            "Please enter your Complaint ID."
        );

        return;
    }


    if (
        !complaintId.startsWith(
            "CR-"
        )
    ) {

        showError(
            "Please enter a valid CivicRoute Complaint ID."
        );

        return;
    }


    trackButton.disabled =
        true;


    trackButton.textContent =
        "Checking...";


    try {

        const response =
            await fetch(
                `/api/complaints/${encodeURIComponent(
                    complaintId
                )}`
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error
                ||
                "Complaint not found."
            );
        }


        renderComplaint(

            data.complaint,

            data.history || []
        );

    }

    catch (error) {

        console.error(
            error
        );


        showError(
            error.message
        );

    }

    finally {

        trackButton.disabled =
            false;


        trackButton.textContent =
            "Track Complaint";
    }
}


// ============================================================
// BUTTON
// ============================================================

trackButton.addEventListener(
    "click",
    trackComplaint
);


// ============================================================
// ENTER KEY
// ============================================================

complaintIdInput.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter"
        ) {

            event.preventDefault();

            trackComplaint();
        }
    }
);


// ============================================================
// OPTIONAL URL QUERY
//
// Example:
// /track?id=CR-20260920-4D86D7
// ============================================================

const urlParameters =
    new URLSearchParams(
        window.location.search
    );


const complaintIdFromUrl =
    urlParameters.get(
        "id"
    );


if (
    complaintIdFromUrl
) {

    complaintIdInput.value =
        normaliseComplaintId(
            complaintIdFromUrl
        );


    trackComplaint();
}