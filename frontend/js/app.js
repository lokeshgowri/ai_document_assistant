const API_BASE_URL = "http://127.0.0.1:8000";


// ========================================
// STATE
// ========================================

let currentConversationId = null;


// ========================================
// HTML ELEMENTS
// ========================================

const questionInput =
    document.getElementById("questionInput");

const askButton =
    document.getElementById("askButton");

const chatMessages =
    document.getElementById("chatMessages");

const newConversationButton =
    document.getElementById("newConversationButton");

const conversationList =
    document.getElementById("conversationList");

const chatTitle =
    document.getElementById("chatTitle");

const attachButton =
    document.getElementById("attachButton");

const documentInput =
    document.getElementById("documentInput");

const uploadStatus =
    document.getElementById("uploadStatus");


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
// CONVERSATIONS
// ========================================

async function loadConversations() {

    try {

        const conversations =
            await apiRequest("/conversations");

        renderConversationList(
            conversations
        );

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

function renderConversationList(
    conversations
) {

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


    conversations.forEach(
        (conversation) => {

            const item =
                document.createElement("div");

            item.className =
                "conversation-item";


            if (
                conversation.id ===
                currentConversationId
            ) {

                item.classList.add(
                    "active"
                );

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

            deleteButton.type =
                "button";

            deleteButton.className =
                "delete-conversation-button";

            deleteButton.textContent =
                "×";

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


            item.appendChild(
                title
            );

            item.appendChild(
                deleteButton
            );


            item.addEventListener(
                "click",
                () => {

                    openConversation(
                        conversation.id
                    );

                }
            );


            conversationList.appendChild(
                item
            );

        }
    );

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
                        title:
                            "New Conversation"
                    })
                }
            );


        currentConversationId =
            conversation.id;


        chatTitle.textContent =
            conversation.title;


        clearMessages();

        renderWelcomeMessage();


        const conversations =
            await apiRequest(
                "/conversations"
            );

        renderConversationList(
            conversations
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

async function openConversation(
    conversationId
) {

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
            await apiRequest(
                "/conversations"
            );


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

    const confirmed =
        confirm(
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
        <div class="welcome-icon">
            🤖
        </div>

        <h2>
            Welcome to Document Q&A
        </h2>

        <p>
            Upload a document using the + button
            and ask questions about its content.
        </p>
    `;


    chatMessages.appendChild(
        welcome
    );

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


    let loadingMessage = null;


    try {

        // Create conversation automatically
        // if this is the first question.

        if (
            currentConversationId ===
            null
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

        attachButton.disabled = true;

        askButton.textContent =
            "Thinking...";


        loadingMessage =
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

        if (loadingMessage) {

            updateAssistantMessage(
                loadingMessage,
                `Unable to process the question: ${error.message}`
            );

        } else {

            console.error(
                "Question failed:",
                error
            );

        }


    } finally {

        askButton.disabled = false;

        attachButton.disabled = false;

        askButton.textContent =
            "Ask";

    }

}


// ========================================
// REFRESH CONVERSATION LIST
// ========================================

async function refreshConversationList() {

    try {

        const conversations =
            await apiRequest(
                "/conversations"
            );


        renderConversationList(
            conversations
        );


    } catch {

        // Keep current UI
        // if refresh fails.

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


    messageBubble.textContent =
        text;


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

    messageElement.textContent =
        text;

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


    sources.forEach(
        (source) => {

            const sourceItem =
                document.createElement("div");


            sourceItem.textContent =
                source.source ||
                "Unknown source";


            sourcesContainer.appendChild(
                sourceItem
            );

        }
    );


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
    .querySelectorAll(
        ".example-question"
    )
    .forEach(
        (button) => {

            button.addEventListener(
                "click",
                () => {

                    questionInput.value =
                        button.textContent.trim();

                    questionInput.focus();

                }
            );

        }
    );


// ========================================
// ATTACH DOCUMENT
// ========================================

attachButton.addEventListener(
    "click",
    () => {

        documentInput.click();

    }
);


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


        try {

            // Create conversation automatically
            // if one does not exist.

            if (
                currentConversationId ===
                null
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


            attachButton.disabled = true;

            askButton.disabled = true;


            uploadStatus.textContent =
                "Uploading and indexing document...";


            uploadStatus.classList.remove(
                "hidden"
            );


            const formData =
                new FormData();


            formData.append(
                "file",
                file
            );


            formData.append(
                "conversation_id",
                currentConversationId
            );


            const data =
                await apiRequest(
                    "/upload",
                    {
                        method: "POST",

                        body: formData
                    }
                );


            uploadStatus.textContent =
                "✓ Document indexed successfully.";


            // Update conversation title

            if (
                data.filename
            ) {

                const filename =
                    data.filename;


                const cleanTitle =
                    filename
                        .replace(
                            /\.[^/.]+$/,
                            ""
                        )
                        .replace(
                            /[_-]+/g,
                            " "
                        )
                        .replace(
                            /\s+/g,
                            " "
                        )
                        .trim()
                        .replace(
                            /\b\w/g,
                            (char) =>
                                char.toUpperCase()
                        );


                chatTitle.textContent =
                    cleanTitle;

            }


            await refreshConversationList();


        } catch (error) {

            uploadStatus.textContent =
                `Upload failed: ${error.message}`;


            uploadStatus.classList.remove(
                "hidden"
            );

        } finally {

            attachButton.disabled = false;

            askButton.disabled = false;

            // Allow selecting the same file again.

            documentInput.value = "";

        }

    }
);


// ========================================
// INITIALIZE APPLICATION
// ========================================

async function initializeApp() {

    await loadConversations();

}


initializeApp();