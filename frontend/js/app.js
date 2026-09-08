console.log("🚀 APP.JS LOADED");

const API_BASE_URL = "https://letting-karaoke-arms-played.trycloudflare.com";

// ==========================================
// HTML ELEMENTS
// ==========================================

const indexButton = document.getElementById("indexButton");
const indexStatus = document.getElementById("indexStatus");

const documentInput = document.getElementById("documentInput");
const selectedFile = document.getElementById("selectedFile");
const fileName = document.getElementById("fileName");

const documentCount = document.getElementById("documentCount");
const chunkCount = document.getElementById("chunkCount");

const questionInput = document.getElementById("questionInput");
const askButton = document.getElementById("askButton");
const chatMessages = document.getElementById("chatMessages");

console.log("Index button:", indexButton);
console.log("Ask button:", askButton);


// ==========================================
// LOAD INDEX STATUS
// ==========================================

async function loadIndexStatus() {

    try {

        console.log("📊 Loading index status...");

        const response = await fetch(
            `${API_BASE_URL}/index/status`
        );

        const data = await response.json();

        console.log("📊 Index status:", data);

        if (data.indexed) {

            documentCount.textContent =
                data.documents;

            chunkCount.textContent =
                data.chunks;

            indexStatus.textContent =
                "✅ Documents are indexed.";

            indexStatus.classList.remove("hidden");

        } else {

            documentCount.textContent = "0";
            chunkCount.textContent = "0";

        }

    } catch (error) {

        console.error(
            "❌ Failed to load index status:",
            error
        );

    }
}


// ==========================================
// INDEX DOCUMENTS
// ==========================================

indexButton.addEventListener(
    "click",
    async function (event) {

        event.preventDefault();

        console.log("🔥 INDEX BUTTON CLICKED");

        indexButton.disabled = true;
        indexButton.textContent = "Indexing...";

        indexStatus.textContent =
            "Indexing documents...";

        indexStatus.classList.remove("hidden");

        try {

            console.log(
                "📡 Sending index request..."
            );

            const response = await fetch(
                `${API_BASE_URL}/index`,
                {
                    method: "POST"
                }
            );

            console.log(
                "📥 Index response received"
            );

            console.log(
                "Status:",
                response.status
            );

            const data =
                await response.json();

            console.log(
                "📦 Index response:",
                data
            );

            if (
                response.ok &&
                data.status === "success"
            ) {

                indexStatus.textContent =
                    "✅ Documents indexed successfully.";

                documentCount.textContent =
                    data.details.documents;

                chunkCount.textContent =
                    data.details.chunks;

            } else {

                indexStatus.textContent =
                    "❌ Document indexing failed.";

            }

        } catch (error) {

            console.error(
                "❌ Index API error:",
                error
            );

            indexStatus.textContent =
                "❌ Could not connect to backend.";

        } finally {

            indexButton.disabled = false;

            indexButton.textContent =
                "Index Documents";

        }

    }
);


// ==========================================
// ASK QUESTION
// ==========================================

askButton.addEventListener(
    "click",
    async function (event) {

        event.preventDefault();

        const question =
            questionInput.value.trim();


        // ------------------------------------------
        // Don't send empty questions
        // ------------------------------------------

        if (!question) {

            console.log(
                "⚠️ Empty question"
            );

            return;
        }


        console.log(
            "🔥 ASK BUTTON CLICKED"
        );

        console.log(
            "Question:",
            question
        );


        // ------------------------------------------
        // Show user's question
        // ------------------------------------------

        addMessage(
            question,
            "user"
        );


        // ------------------------------------------
        // Clear input
        // ------------------------------------------

        questionInput.value = "";


        // ------------------------------------------
        // Disable button while processing
        // ------------------------------------------

        askButton.disabled = true;

        askButton.textContent =
            "Thinking...";


        // ------------------------------------------
        // Show temporary assistant message
        // ------------------------------------------

        const loadingMessage =
            addMessage(
                "Thinking...",
                "assistant"
            );


        try {

            console.log(
                "📡 Sending question to /ask..."
            );


            // ------------------------------------------
            // Send request to FastAPI
            // ------------------------------------------

            const response = await fetch(
                `${API_BASE_URL}/ask`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    body: JSON.stringify({
                        question: question,
                        top_k: 3
                    })
                }
            );


            console.log(
                "📥 Question response received"
            );

            console.log(
                "HTTP Status:",
                response.status
            );


            // ------------------------------------------
            // Read response
            // ------------------------------------------

            const data =
                await response.json();

            console.log(
                "📦 Question response:",
                data
            );


            // ------------------------------------------
            // Handle backend error
            // ------------------------------------------

            if (!response.ok) {

                updateAssistantMessage(
                    loadingMessage,
                    "❌ " +
                    (
                        data.detail ||
                        "Failed to process the question."
                    )
                );

                return;
            }


            // ------------------------------------------
            // Display answer
            // ------------------------------------------

            updateAssistantMessage(
                loadingMessage,
                data.answer ||
                "No answer returned."
            );


            // ------------------------------------------
            // Display sources
            // ------------------------------------------

            if (
                data.sources &&
                data.sources.length > 0
            ) {

                addSources(
                    loadingMessage,
                    data.sources
                );

            }

        } catch (error) {

            console.error(
                "❌ Ask API error:",
                error
            );

            updateAssistantMessage(
                loadingMessage,
                "❌ Could not connect to the backend."
            );

        } finally {

            askButton.disabled = false;

            askButton.textContent =
                "Ask";

        }

    }
);


// ==========================================
// ADD CHAT MESSAGE
// ==========================================

function addMessage(text, sender) {

    // ------------------------------------------
    // Message row
    // ------------------------------------------

    const messageRow =
        document.createElement("div");

    messageRow.classList.add(
        "message-row",
        sender
    );


    // ------------------------------------------
    // Message container
    // ------------------------------------------

    const messageContainer =
        document.createElement("div");


    if (sender === "user") {

        messageContainer.className =
            "user-message-container";

    } else {

        messageContainer.className =
            "assistant-message-container";

    }


    // ------------------------------------------
    // Label
    // ------------------------------------------

    const label =
        document.createElement("div");


    if (sender === "user") {

        label.className =
            "user-label";

        label.textContent =
            "You";

    } else {

        label.className =
            "assistant-label";

        label.textContent =
            "AI Assistant";

    }


    // ------------------------------------------
    // Message bubble
    // ------------------------------------------

    const messageBubble =
        document.createElement("div");


    if (sender === "user") {

        messageBubble.className =
            "user-message";

    } else {

        messageBubble.className =
            "assistant-message";

    }


    messageBubble.textContent =
        text;


    // ------------------------------------------
    // Build message
    // ------------------------------------------

    messageContainer.appendChild(
        label
    );

    messageContainer.appendChild(
        messageBubble
    );

    messageRow.appendChild(
        messageContainer
    );

    chatMessages.appendChild(
        messageRow
    );


    // ------------------------------------------
    // Scroll to bottom
    // ------------------------------------------

    chatMessages.scrollTop =
        chatMessages.scrollHeight;


    // Return the bubble so we can update it
    return messageBubble;
}


// ==========================================
// UPDATE ASSISTANT MESSAGE
// ==========================================

function updateAssistantMessage(
    messageElement,
    text
) {

    messageElement.textContent =
        text;

    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


// ==========================================
// ADD SOURCES
// ==========================================

function addSources(
    messageElement,
    sources
) {

    const sourcesContainer =
        document.createElement("div");

    sourcesContainer.className =
        "message-sources";


    const sourcesTitle =
        document.createElement("strong");

    sourcesTitle.textContent =
        "Sources:";


    sourcesContainer.appendChild(
        sourcesTitle
    );


    sources.forEach(
        function (source) {

            const sourceItem =
                document.createElement("div");

            sourceItem.textContent =
                `${source.source || "Unknown source"}`
                +
                `${
                    source.section
                        ? " — " + source.section
                        : ""
                }`;

            sourcesContainer.appendChild(
                sourceItem
            );

        }
    );


    // messageElement is the assistant bubble.
    // Its parent is the message container.

    messageElement.parentElement.appendChild(
        sourcesContainer
    );


    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


// ==========================================
// UPLOAD DOCUMENT
// ==========================================

documentInput.addEventListener(
    "change",
    async function () {

        const file =
            documentInput.files[0];

        if (!file) {
            return;
        }


        console.log(
            "📄 Selected file:",
            file.name
        );


        // ------------------------------------------
        // Show selected filename
        // ------------------------------------------

        fileName.textContent =
            file.name;

        selectedFile.classList.remove(
            "hidden"
        );


        // ------------------------------------------
        // Create multipart form data
        // ------------------------------------------

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );


        try {

            console.log(
                "📡 Uploading document..."
            );

            indexStatus.textContent =
                "Uploading document...";

            indexStatus.classList.remove(
                "hidden"
            );


            const response =
                await fetch(
                    `${API_BASE_URL}/upload`,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            console.log(
                "📥 Upload response:",
                response.status
            );


            const data =
                await response.json();


            console.log(
                "📦 Upload data:",
                data
            );


            if (
                response.ok &&
                data.status === "success"
            ) {

                indexStatus.textContent =
                    `✅ ${data.filename} uploaded successfully.`;

            } else {

                indexStatus.textContent =
                    `❌ ${
                        data.detail ||
                        "Upload failed."
                    }`;

            }

        } catch (error) {

            console.error(
                "❌ Upload error:",
                error
            );

            indexStatus.textContent =
                "❌ Could not upload document.";

        }

    }
);


// ==========================================
// LOAD STATUS WHEN PAGE OPENS
// ==========================================

loadIndexStatus();