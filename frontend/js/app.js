const API_BASE_URL = "http://127.0.0.1:8000"; // Update this to your backend API URL

// ========================================
// STATE
// ========================================

let currentConversationId = null;

// ========================================
// HTML ELEMENTS
// ========================================

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

const newConversationButton =
    document.getElementById("newConversationButton");

const conversationList =
    document.getElementById("conversationList");

const chatTitle =
    document.getElementById("chatTitle");

// ========================================
// API HELPER
// ========================================

async function apiRequest(endpoint, options = {}) {
    const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        options
    );

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            data.detail ||
            data.message ||
            "Request failed."
        );
    }

    return data;
}

// ========================================
// INDEX STATUS
// ========================================

async function loadIndexStatus() {
    try {
        const data = await apiRequest("/index/status");

        if (data.indexed) {
            documentCount.textContent = data.documents;
            chunkCount.textContent = data.chunks;

            indexStatus.textContent =
                "Documents are indexed.";

            indexStatus.classList.remove("hidden");
        } else {
            documentCount.textContent = "0";
            chunkCount.textContent = "0";

            indexStatus.classList.add("hidden");
        }
    } catch {
        documentCount.textContent = "0";
        chunkCount.textContent = "0";
    }
}

// ========================================
// INDEX DOCUMENTS
// ========================================

indexButton.addEventListener("click", async () => {
    indexButton.disabled = true;
    indexButton.textContent = "Indexing...";

    indexStatus.textContent =
        "Indexing documents...";

    indexStatus.classList.remove("hidden");

    try {
        const data = await apiRequest("/index", {
            method: "POST"
        });

        documentCount.textContent =
            data.details.documents;

        chunkCount.textContent =
            data.details.chunks;

        indexStatus.textContent =
            "Documents indexed successfully.";
    } catch (error) {
        indexStatus.textContent =
            `Indexing failed: ${error.message}`;
    } finally {
        indexButton.disabled = false;
        indexButton.textContent = "Index Documents";
    }
});

// ========================================
// CONVERSATIONS
// ========================================

async function loadConversations() {
    try {
        const conversations =
            await apiRequest("/conversations");

        renderConversationList(conversations);

        if (conversations.length > 0) {
            await openConversation(
                conversations[0].id
            );
        } else {
            resetChat();
        }
    } catch (error) {
        conversationList.innerHTML = "";

        const emptyMessage =
            document.createElement("div");

        emptyMessage.className =
            "empty-conversations";

        emptyMessage.textContent =
            "Unable to load conversations.";

        conversationList.appendChild(
            emptyMessage
        );
    }
}

// ========================================
// RENDER CONVERSATION LIST
// ========================================

function renderConversationList(conversations) {
    conversationList.innerHTML = "";

    if (conversations.length === 0) {
        const emptyMessage =
            document.createElement("div");

        emptyMessage.className =
            "empty-conversations";

        emptyMessage.textContent =
            "No conversations yet.";

        conversationList.appendChild(
            emptyMessage
        );

        return;
    }

    conversations.forEach((conversation) => {
        const item =
            document.createElement("div");

        item.className = "conversation-item";

        if (
            conversation.id ===
            currentConversationId
        ) {
            item.classList.add("active");
        }

        const title =
            document.createElement("span");

        title.className =
            "conversation-title";

        title.textContent =
            conversation.title ||
            "New Conversation";

        title.title =
            conversation.title ||
            "New Conversation";

        title.addEventListener(
            "click",
            () => {
                openConversation(
                    conversation.id
                );
            }
        );

        const deleteButton =
            document.createElement("button");

        deleteButton.type = "button";
        deleteButton.className =
            "delete-conversation-button";

        deleteButton.textContent = "×";
        deleteButton.title =
            "Delete conversation";

        deleteButton.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();

                deleteConversation(
                    conversation.id
                );
            }
        );

        item.appendChild(title);
        item.appendChild(deleteButton);

        item.addEventListener(
            "click",
            () => {
                openConversation(
                    conversation.id
                );
            }
        );

        conversationList.appendChild(item);
    });
}

// ========================================
// CREATE NEW CONVERSATION
// ========================================

async function createConversation() {
    try {
        const conversation =
            await apiRequest(
                "/conversations",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        title: "New Conversation"
                    })
                }
            );

        currentConversationId =
            conversation.id;

        chatTitle.textContent =
            conversation.title;

        clearMessages();

        renderWelcomeMessage();

        await loadConversations();

        currentConversationId =
            conversation.id;

        renderConversationList(
            await apiRequest("/conversations")
        );
    } catch (error) {
        alert(
            `Could not create conversation: ${error.message}`
        );
    }
}

// ========================================
// NEW CONVERSATION BUTTON
// ========================================

newConversationButton.addEventListener(
    "click",
    createConversation
);

// ========================================
// OPEN CONVERSATION
// ========================================

async function openConversation(conversationId) {
    if (
        conversationId ===
        currentConversationId
    ) {
        return;
    }

    try {
        const conversation =
            await apiRequest(
                `/conversations/${conversationId}`
            );

        currentConversationId =
            conversation.id;

        chatTitle.textContent =
            conversation.title ||
            "New Conversation";

        clearMessages();

        if (
            conversation.messages &&
            conversation.messages.length > 0
        ) {
            conversation.messages.forEach(
                (message) => {
                    addMessage(
                        message.content,
                        message.role
                    );
                }
            );
        } else {
            renderWelcomeMessage();
        }

        const conversations =
            await apiRequest("/conversations");

        renderConversationList(
            conversations
        );
    } catch (error) {
        alert(
            `Could not load conversation: ${error.message}`
        );
    }
}

// ========================================
// DELETE CONVERSATION
// ========================================

async function deleteConversation(
    conversationId
) {
    const confirmed = confirm(
        "Delete this conversation?"
    );

    if (!confirmed) {
        return;
    }

    try {
        await apiRequest(
            `/conversations/${conversationId}`,
            {
                method: "DELETE"
            }
        );

        if (
            conversationId ===
            currentConversationId
        ) {
            currentConversationId = null;
            resetChat();
        }

        await loadConversations();
    } catch (error) {
        alert(
            `Could not delete conversation: ${error.message}`
        );
    }
}

// ========================================
// RESET CHAT
// ========================================

function resetChat() {
    currentConversationId = null;

    chatTitle.textContent =
        "New Conversation";

    clearMessages();

    renderWelcomeMessage();
}

// ========================================
// CLEAR MESSAGE AREA
// ========================================

function clearMessages() {
    chatMessages.innerHTML = "";
}

// ========================================
// WELCOME MESSAGE
// ========================================

function renderWelcomeMessage() {
    const welcome =
        document.createElement("div");

    welcome.className =
        "welcome-message";

    welcome.innerHTML = `
        <h3>Welcome to the AI Document Q&A Assistant</h3>
        <p>
            Ask questions about your indexed documents.
        </p>
    `;

    chatMessages.appendChild(welcome);
}

// ========================================
// ASK QUESTION
// ========================================

askButton.addEventListener(
    "click",
    askQuestion
);

questionInput.addEventListener(
    "keydown",
    (event) => {
        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {
            event.preventDefault();

            if (!askButton.disabled) {
                askQuestion();
            }
        }
    }
);

// ========================================
// ASK QUESTION FUNCTION
// ========================================

async function askQuestion() {
    const question =
        questionInput.value.trim();

    if (!question) {
        return;
    }

    try {
        // Create conversation automatically
        // if this is the first question.
        if (
            currentConversationId === null
        ) {
            const conversation =
                await apiRequest(
                    "/conversations",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body: JSON.stringify({
                            title:
                                "New Conversation"
                        })
                    }
                );

            currentConversationId =
                conversation.id;

            chatTitle.textContent =
                conversation.title;
        }

        addMessage(
            question,
            "user"
        );

        questionInput.value = "";

        askButton.disabled = true;
        askButton.textContent =
            "Thinking...";

        const loadingMessage =
            addMessage(
                "Thinking...",
                "assistant"
            );

        const data =
            await apiRequest(
                "/ask",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        question: question,
                        top_k: 3,
                        conversation_id:
                            currentConversationId
                    })
                }
            );

        updateAssistantMessage(
            loadingMessage,
            data.answer ||
            "No answer returned."
        );

        if (
            data.sources &&
            data.sources.length > 0
        ) {
            addSources(
                loadingMessage,
                data.sources
            );
        }

        await refreshConversationList();

    } catch (error) {
        updateAssistantMessage(
            loadingMessage,
            `Unable to process the question: ${error.message}`
        );
    } finally {
        askButton.disabled = false;
        askButton.textContent = "Ask";
    }
}

// ========================================
// REFRESH CONVERSATION LIST
// ========================================

async function refreshConversationList() {
    try {
        const conversations =
            await apiRequest("/conversations");

        renderConversationList(
            conversations
        );
    } catch {
        // Keep the current UI if refresh fails.
    }
}

// ========================================
// ADD MESSAGE
// ========================================

function addMessage(
    text,
    sender
) {
    const messageRow =
        document.createElement("div");

    messageRow.classList.add(
        "message-row",
        sender
    );

    const messageContainer =
        document.createElement("div");

    messageContainer.className =
        sender === "user"
            ? "user-message-container"
            : "assistant-message-container";

    const label =
        document.createElement("div");

    label.className =
        sender === "user"
            ? "user-label"
            : "assistant-label";

    label.textContent =
        sender === "user"
            ? "You"
            : "AI Assistant";

    const messageBubble =
        document.createElement("div");

    messageBubble.className =
        sender === "user"
            ? "user-message"
            : "assistant-message";

    messageBubble.textContent = text;

    messageContainer.appendChild(label);
    messageContainer.appendChild(
        messageBubble
    );

    messageRow.appendChild(
        messageContainer
    );

    chatMessages.appendChild(
        messageRow
    );

    scrollToBottom();

    return messageBubble;
}

// ========================================
// UPDATE ASSISTANT MESSAGE
// ========================================

function updateAssistantMessage(
    messageElement,
    text
) {
    messageElement.textContent = text;

    scrollToBottom();
}

// ========================================
// ADD SOURCES
// ========================================

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

    sources.forEach((source) => {
        const sourceItem =
            document.createElement("div");

        sourceItem.textContent =
            source.source ||
            "Unknown source";

        sourcesContainer.appendChild(
            sourceItem
        );
    });

    messageElement.parentElement.appendChild(
        sourcesContainer
    );

    scrollToBottom();
}

// ========================================
// SCROLL CHAT TO BOTTOM
// ========================================

function scrollToBottom() {
    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}

// ========================================
// EXAMPLE QUESTIONS
// ========================================

document
    .querySelectorAll(".example-question")
    .forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                questionInput.value =
                    button.textContent.trim();

                questionInput.focus();
            }
        );
    });

// ========================================
// UPLOAD DOCUMENT
// ========================================

documentInput.addEventListener(
    "change",
    async () => {
        const file =
            documentInput.files[0];

        if (!file) {
            return;
        }

        fileName.textContent =
            file.name;

        selectedFile.classList.remove(
            "hidden"
        );

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );

        indexStatus.textContent =
            "Uploading document...";

        indexStatus.classList.remove(
            "hidden"
        );

        try {
            const data =
                await apiRequest(
                    "/upload",
                    {
                        method: "POST",
                        body: formData
                    }
                );

            indexStatus.textContent =
                `${data.filename} uploaded successfully.`;
        } catch (error) {
            indexStatus.textContent =
                `Upload failed: ${error.message}`;
        }
    }
);

// ========================================
// INITIALIZE APPLICATION
// ========================================

async function initializeApp() {
    await loadIndexStatus();
    await loadConversations();
}

initializeApp();