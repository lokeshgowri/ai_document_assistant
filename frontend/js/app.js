//const API_BASE_URL = "https://ai-document-assistant-nu.vercel.app";
//for hosting 

const API_BASE_URL = "http://127.0.0.1:8000"; 
//for local 

// ========================================
// STATE
// ========================================

let currentConversationId = null;

// Keep the messages of the currently open
// conversation in frontend memory.
// This prevents UI refreshes from disturbing
// the visible chat history.
let currentMessages = [];   

// Track questions that are currently being processed.
// Each conversation can have its own active request.
const pendingAskRequests = new Map();

// Conversations whose background generation
// finished while the user was viewing another chat.
const completedAskRequests = new Set();

// Keep a separate unsent question for each conversation.
const conversationDrafts = new Map();

// Keep the conversation list locally so switching
// between conversations does not have to wait
// for another API request before updating the UI.
let conversationListCache = [];

// Cache loaded message history for each conversation.
// This lets us switch chats instantly without waiting
// for the network request to finish.
const conversationMessagesCache = new Map();

// Changes every time the user switches conversations.
// Older conversation-loading requests are ignored.
let conversationSwitchToken = 0;

function updateAskControls() {

    const conversationIsProcessing =
        currentConversationId !== null &&
        pendingAskRequests.has(currentConversationId);

    askButton.disabled = conversationIsProcessing;
    attachButton.disabled = conversationIsProcessing;

    askButton.textContent =
        conversationIsProcessing
            ? "Thinking..."
            : "Ask";
}


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

        conversationListCache =
            conversations;

        renderConversationList(
            conversations
        );

        if (conversations.length > 0) {

            if (currentConversationId === null) {

                await openConversation(
                    conversations[0].id
                );

            }

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


            // ====================================
            // STATUS DOT
            // ====================================

            const statusDot =
                document.createElement("span");

            statusDot.className =
                "conversation-status-dot";

            const isCurrentConversation =
                conversation.id ===
                currentConversationId;

            const isPending =
                pendingAskRequests.has(
                    conversation.id
                );

            const isCompleted =
                completedAskRequests.has(
                    conversation.id
                );

            if (
                !isCurrentConversation &&
                isPending
            ) {

                statusDot.classList.add(
                    "generating"
                );

            } else if (
                !isCurrentConversation &&
                isCompleted
            ) {

                statusDot.classList.add(
                    "completed"
                );
            }


            // ====================================
            // BUILD CONVERSATION ITEM
            // ====================================

            item.appendChild(statusDot);
            item.appendChild(title);


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

        completedAskRequests.delete(
            conversation.id
        );

        currentMessages = [];

        conversationMessagesCache.set(
            conversation.id,
            []
        );

        conversationDrafts.set(
            conversation.id,
            ""
        );

        chatTitle.textContent =
            conversation.title ||
            "New Conversation";

        questionInput.value = "";

        clearMessages();

        renderWelcomeMessage();

        // Refresh the sidebar without blocking
        // the newly selected conversation.
        await refreshConversationList();

        renderConversationList(
            conversationListCache
        );

        updateAskControls();

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

    const previousConversationId =
        currentConversationId;

    if (
        previousConversationId !== null
    ) {

        conversationDrafts.set(
            previousConversationId,
            questionInput.value
        );
    }

    // ----------------------------------------
    // SWITCH THE UI FIRST.
    // No network request is awaited here
    // before the selected conversation changes.
    // ----------------------------------------

    currentConversationId =
        conversationId;

    conversationSwitchToken += 1;

    const switchToken =
        conversationSwitchToken;

    completedAskRequests.delete(
        conversationId
    );

    const conversationSummary =
        conversationListCache.find(
            (conversation) =>
                conversation.id ===
                conversationId
        );

    chatTitle.textContent =
        conversationSummary?.title ||
        "New Conversation";

    questionInput.value =
        conversationDrafts.get(
            conversationId
        ) || "";

    // ----------------------------------------
    // Use cached history immediately.
    // ----------------------------------------

    const cachedMessages =
        conversationMessagesCache.get(
            conversationId
        );

    currentMessages =
        Array.isArray(cachedMessages)
            ? cachedMessages.map(
                (message) => ({
                    role: message.role,
                    content: message.content
                })
            )
            : [];

    renderConversationList(
        conversationListCache
    );

    renderCurrentMessages();

    // ----------------------------------------
    // If this conversation is already generating,
    // show Thinking immediately.
    // ----------------------------------------

    if (
        pendingAskRequests.has(
            conversationId
        )
    ) {

        const requestState =
            pendingAskRequests.get(
                conversationId
            );

        requestState.loadingMessage =
            addMessageToUI(
                "Thinking...",
                "assistant"
            );
    }

    updateAskControls();

    // ----------------------------------------
    // Load the latest history in the background.
    // This NEVER blocks conversation switching.
    // ----------------------------------------

    try {

        const conversation =
            await apiRequest(
                `/conversations/${conversationId}`
            );

        // The user switched again.
        // Ignore this response completely.
        if (
            switchToken !==
                conversationSwitchToken ||
            currentConversationId !==
                conversationId
        ) {

            return;
        }

        const serverMessages =
            Array.isArray(
                conversation.messages
            )
                ? conversation.messages.map(
                    (message) => ({
                        role: message.role,
                        content: message.content
                    })
                )
                : [];

        conversationMessagesCache.set(
            conversationId,
            serverMessages
        );

        chatTitle.textContent =
            conversation.title ||
            chatTitle.textContent ||
            "New Conversation";

        // ----------------------------------------
        // If a request is currently running,
        // preserve the local UI because it contains
        // the question that is being processed and
        // the Thinking message.
        // ----------------------------------------

        if (
            !pendingAskRequests.has(
                conversationId
            )
        ) {

            currentMessages =
                serverMessages;

            renderCurrentMessages();

        }

        questionInput.value =
            conversationDrafts.get(
                conversationId
            ) || "";

        // Re-add Thinking after a history render.
        if (
            pendingAskRequests.has(
                conversationId
            )
        ) {

            const requestState =
                pendingAskRequests.get(
                    conversationId
                );

            // The request state may already point
            // to an older DOM element if the history
            // was rendered again.
            if (
                !requestState.loadingMessage ||
                !requestState.loadingMessage.isConnected
            ) {

                requestState.loadingMessage =
                    addMessageToUI(
                        "Thinking...",
                        "assistant"
                    );

            }

        }

        updateAskControls();

    } catch (error) {

        // Do not move the user back to another
        // conversation just because this background
        // history request failed.
        console.error(
            `Could not load conversation ${conversationId}:`,
            error
        );

    }

}


// ========================================
// RENDER CURRENT MESSAGE HISTORY
// ========================================

function renderCurrentMessages() {

    clearMessages();


    if (
        currentMessages.length === 0
    ) {

        renderWelcomeMessage();

        return;

    }


    currentMessages.forEach(
        (message) => {

            addMessageToUI(
                message.content,
                message.role
            );

        }
    );


    scrollToBottom();

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

            currentMessages = [];

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

    conversationSwitchToken += 1;

    currentConversationId = null;

    currentMessages = [];

    chatTitle.textContent =
        "New Conversation";

    questionInput.value = "";

    clearMessages();

    renderWelcomeMessage();

    updateAskControls();

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

    // Do not start another request for the
    // same conversation while one is running.
    if (
        currentConversationId !== null &&
        pendingAskRequests.has(
            currentConversationId
        )
    ) {
        return;
    }

    let requestConversationId =
        currentConversationId;

    try {

        // ------------------------------------
        // Create conversation automatically
        // if this is the first question.
        // ------------------------------------

        if (
            requestConversationId ===
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

            requestConversationId =
                conversation.id;

            currentConversationId =
                requestConversationId;

            currentMessages = [];

            conversationMessagesCache.set(
                requestConversationId,
                []
            );

            chatTitle.textContent =
                conversation.title ||
                "New Conversation";

            clearMessages();

            renderWelcomeMessage();

            await refreshConversationList();

        }

        // ------------------------------------
        // Add user question to this conversation.
        // ------------------------------------

        currentMessages.push({
            role: "user",
            content: question
        });

        conversationMessagesCache.set(
            requestConversationId,
            currentMessages.map(
                (message) => ({
                    role: message.role,
                    content: message.content
                })
            )
        );

        addMessageToUI(
            question,
            "user"
        );

        questionInput.value = "";

        conversationDrafts.set(
            requestConversationId,
            ""
        );

        // ------------------------------------
        // Create temporary assistant message.
        // ------------------------------------

        const loadingMessage =
            addMessageToUI(
                "Thinking...",
                "assistant"
            );

        // ------------------------------------
        // Store request state by conversation.
        // ------------------------------------

        pendingAskRequests.set(
            requestConversationId,
            {
                loadingMessage
            }
        );

        // Update the blue dot immediately.
        renderConversationList(
            conversationListCache
        );

        updateAskControls();

        // ------------------------------------
        // Send the request.
        //
        // IMPORTANT:
        // Always use requestConversationId.
        // Never use currentConversationId.
        // ------------------------------------

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
                        question:
                            question,

                        top_k:
                            3,

                        conversation_id:
                            requestConversationId
                    })
                }
            );

        const answer =
            data.answer ||
            "No answer returned.";

        const requestState =
            pendingAskRequests.get(
                requestConversationId
            );

        // ------------------------------------
        // Update the visible UI only when the
        // user is currently viewing this chat.
        // ------------------------------------

        if (
            currentConversationId ===
                requestConversationId &&
            requestState
        ) {

            updateAssistantMessage(
                requestState.loadingMessage,
                answer
            );

            currentMessages.push({
                role: "assistant",
                content: answer
            });

            conversationMessagesCache.set(
                requestConversationId,
                currentMessages.map(
                    (message) => ({
                        role: message.role,
                        content: message.content
                    })
                )
            );

            if (
                data.sources &&
                data.sources.length > 0
            ) {

                addSources(
                    requestState.loadingMessage,
                    data.sources
                );

            }

        } else {

            // --------------------------------
            // User is viewing another chat.
            // Keep the completed answer in the
            // background conversation cache.
            // --------------------------------

            const backgroundMessages =
                conversationMessagesCache.get(
                    requestConversationId
                ) || [];

            backgroundMessages.push({
                role: "assistant",
                content: answer
            });

            conversationMessagesCache.set(
                requestConversationId,
                backgroundMessages.map(
                    (message) => ({
                        role: message.role,
                        content: message.content
                    })
                )
            );

        }

        // Refresh only the sidebar.
        refreshConversationList();

    } catch (error) {

        const requestState =
            requestConversationId !== null
                ? pendingAskRequests.get(
                    requestConversationId
                )
                : null;

        if (
            currentConversationId ===
                requestConversationId &&
            requestState
        ) {

            updateAssistantMessage(
                requestState.loadingMessage,
                `Unable to process the question: ${error.message}`
            );

        } else {

            console.error(
                "Question failed:",
                error
            );

        }

    } finally {

        if (
            requestConversationId !==
            null
        ) {

            const userIsViewingThisConversation =
                currentConversationId ===
                requestConversationId;

            pendingAskRequests.delete(
                requestConversationId
            );

            if (
                !userIsViewingThisConversation
            ) {

                completedAskRequests.add(
                    requestConversationId
                );

            } else {

                completedAskRequests.delete(
                    requestConversationId
                );

            }

            // Update the status dot immediately.
            renderConversationList(
                conversationListCache
            );

            updateAskControls();

            // Refresh sidebar data in the background.
            // Do not wait for it.
            refreshConversationList();

        }

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

        conversationListCache =
            conversations;

        renderConversationList(
            conversations
        );

    } catch {

        // Keep current UI
        // if refresh fails.

    }

}


// ========================================
// ADD MESSAGE TO UI
// ========================================

function addMessageToUI(
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

            // --------------------------------
            // Create conversation automatically
            // if one does not exist.
            // --------------------------------

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

                completedAskRequests.delete(
                    conversation.id
                );

                currentMessages = [];

                conversationMessagesCache.set(
                    conversation.id,
                    []
                );

                conversationDrafts.set(
                    conversation.id,
                    ""
                );

                chatTitle.textContent =
                    conversation.title ||
                    "New Conversation";

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


            // --------------------------------
            // Update conversation title only.
            //
            // IMPORTANT:
            // We DO NOT clear the messages.
            // --------------------------------

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


            // --------------------------------
            // Refresh sidebar only.
            // --------------------------------

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