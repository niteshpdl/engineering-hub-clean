// Chatbot.js - Engineering Hub Chatbot
console.log("Chatbot.js loaded completely");


// Global variables
let currentSessionId = null;
let currentFile = null;
let chatbotVisible = false;
let isExpanded = false;
let isMinimized = false;

// Helper functions for localStorage operations
function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, value);
        console.log(`Saved ${key} to localStorage:`, value);
    } catch (e) {
        console.warn(`Failed to save ${key} to localStorage:`, e);
    }
}

function getFromLocalStorage(key) {
    try {
        return localStorage.getItem(key);
    } catch (e) {
        console.warn(`Failed to get ${key} from localStorage:`, e);
        return null;
    }
}

// Try to restore session from localStorage
currentSessionId = getFromLocalStorage('currentChatSessionId');
if (currentSessionId) {
    console.log("Restored session ID from localStorage:", currentSessionId);
}

// Try to restore chatbot visibility state
const storedVisibility = getFromLocalStorage('chatbotVisible');
if (storedVisibility === 'true') {
    chatbotVisible = true;
}

// Get CSRF token from cookies
function getCsrfToken() {
    let csrfToken = null;
    
    // Try to get from cookie
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            csrfToken = cookie.substring('csrftoken='.length);
            break;
        }
    }
    
    // If not found in cookie, try to get from the form
    if (!csrfToken) {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenElement) {
            csrfToken = tokenElement.value;
        }
    }
    
    // If still not found, look for the meta tag
    if (!csrfToken) {
        const metaElement = document.querySelector('meta[name="csrf-token"]');
        if (metaElement) {
            csrfToken = metaElement.getAttribute('content');
        }
    }
    
    return csrfToken;
}

// Clear invalid session
function clearInvalidSession() {
    console.log("Clearing invalid session ID");
    currentSessionId = null;
    saveToLocalStorage('currentChatSessionId', '');
    
    // Also clear the hidden input
    const sessionInput = document.getElementById('eh-session-id');
    if (sessionInput) {
        sessionInput.value = '';
    }
}

// Add a message to the chat
function addMessage(message, sender, type = 'normal') {
    // Get the messages container
    const messagesContainer = document.getElementById('eh-chatbot-messages');
    if (!messagesContainer) return;
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.className = `eh-chatbot-message eh-${sender}-message`;
    
    // Create message content
    const messageContent = document.createElement('div');
    messageContent.className = 'eh-message-content';
    if (type === 'error') {
        messageContent.classList.add('eh-error-message');
    }
    
    // Process message content (handle markdown, code, etc.)
    if (sender === 'bot') {
        // Process markdown for bot messages
        messageContent.innerHTML = processMarkdown(message);
        
        // Add syntax highlighting for code blocks
        const codeBlocks = messageContent.querySelectorAll('pre code');
        if (codeBlocks.length > 0 && typeof hljs !== 'undefined') {
            codeBlocks.forEach(block => {
                hljs.highlightElement(block);
            });
        }
    } else {
        // Simple text for user messages
        messageContent.textContent = message;
    }
    
    // Add content to message
    messageElement.appendChild(messageContent);
    
    // Add message to container
    messagesContainer.appendChild(messageElement);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return messageElement;
}

// Process markdown in messages
function processMarkdown(text) {
    // Replace code blocks
    text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, function(match, language, code) {
        const lang = language || '';
        return `<pre><code class="language-${lang}">${escapeHtml(code.trim())}</code></pre>`;
    });
    
    // Replace inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Replace bold text
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Replace italic text
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Replace links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Replace line breaks
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

// Escape HTML to prevent XSS
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Add typing indicator
function addTypingIndicator() {
    // Get the template
    const template = document.getElementById('eh-typing-indicator-template');
    if (!template) {
        console.error("Typing indicator template not found");
        return;
    }
    
    // Clone the template content
    const indicator = document.importNode(template.content, true);
    
    // Get the messages container
    const messagesContainer = document.getElementById('eh-chatbot-messages');
    if (!messagesContainer) return;
    
    // Add the indicator
    messagesContainer.appendChild(indicator);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    console.log("Added typing indicator");
}

// Remove typing indicator
function removeTypingIndicator() {
    const indicator = document.querySelector('.eh-typing-indicator');
    if (indicator) {
        const message = indicator.closest('.eh-chatbot-message');
        if (message) {
            message.remove();
        }
    }
}

// Handle message errors
function handleMessageError(error, inputElement) {
    console.error("Error sending message:", error);
    
    // Remove typing indicator
    removeTypingIndicator();
    
    // Add error message
    addMessage("Sorry, I couldn't process your message. Please try again later.", 'bot', 'error');
    
    // Re-enable input
    if (inputElement) {
        inputElement.disabled = false;
    }
}

// Process message response
function processMessageResponse(data, inputElement) {
    // Remove typing indicator
    removeTypingIndicator();
    
    // Add bot message
    if (data.response) {
        addMessage(data.response, 'bot');
    }
    
    // Re-enable input
    if (inputElement) {
        inputElement.disabled = false;
        inputElement.focus();
    }
}

// Send a message
// Fix the sendMessage function to re-enable input after response
function sendMessage(message) {
    if (!message || !currentSessionId) return;
    
    // Add user message to the chat
    addMessage(message, 'user');
    
    // Show typing indicator
    addTypingIndicator();
    
    // Get the input field to re-enable it later
    const chatInput = document.getElementById('eh-chatbot-input');
    
    // Sanitize the session ID - remove any special characters
    const sanitizedSessionId = currentSessionId.replace(/[\u2018\u2019\u201C\u201D]/g, '');
    console.log("Sending message with sanitized session ID:", sanitizedSessionId);
    
    // Send message to API
    fetch('/chatbot/api/message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
            message: message,
            session_id: sanitizedSessionId
        }),
        credentials: 'same-origin'
    })
    .then(response => {
        console.log("Response status:", response.status);
        if (!response.ok) {
            return response.text().then(text => {
                console.log("Error response body:", text);
                throw new Error(`Server responded with ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log("Received response data:", data);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add bot message
        if (data.response) {
            addMessage(data.response, 'bot');
        }
        
        // IMPORTANT: Re-enable the input field
        if (chatInput) {
            chatInput.disabled = false;
            chatInput.focus();
        }
    })
    .catch(error => {
        console.error("Error in sendMessage:", error);
        
        // If we get a UUID error, clear the session and create a new one
        if (error.message.includes("not a valid UUID")) {
            console.log("Invalid UUID detected, clearing session and creating a new one");
            clearInvalidSession();
            createNewSession();
            
            // Add an error message
            addMessage("I had to restart our conversation. Please try sending your message again in a moment.", 'bot', 'error');
            
            // Remove typing indicator
            removeTypingIndicator();
            
            // IMPORTANT: Re-enable the input field
            if (chatInput) {
                chatInput.disabled = false;
                chatInput.focus();
            }
            return;
        }
        
        // Handle other errors
        removeTypingIndicator();
        addMessage("Sorry, I couldn't process your message. Please try again later.", 'bot', 'error');
        
        // IMPORTANT: Re-enable the input field
        if (chatInput) {
            chatInput.disabled = false;
            chatInput.focus();
        }
    });
}

// Upload a file
function uploadFile(message) {
    if (!currentFile || !currentSessionId) {
        console.error("Missing file or session ID for upload");
        return;
    }
    
    console.log("Starting file upload process...");
    console.log("File:", currentFile.name, "Size:", currentFile.size, "Type:", currentFile.type);
    console.log("Session ID:", currentSessionId);
    
    // Create form data
    const formData = new FormData();
    formData.append('pdf_file', currentFile);
    formData.append('message', message || '');
    formData.append('session_id', currentSessionId);
    
    console.log("FormData created with fields: pdf_file, message, session_id");
    
    // Add user message to the chat
    if (message) {
        addMessage(message, 'user');
    } else {
        addMessage(`Uploading file: ${currentFile.name}`, 'user');
    }
    
    // Show typing indicator
    addTypingIndicator();
    
    // Send file to API
    console.log("Sending request to /chatbot/api/upload_pdf/");
    fetch('/chatbot/api/upload_pdf/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        console.log("Response received:", response.status, response.statusText);
        if (!response.ok) {
            return response.text().then(text => {
                console.error("Error response body:", text);
                throw new Error(`Server responded with ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log("Success response data:", data);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Clear the file
        currentFile = null;
        
        // Hide file preview
        const filePreview = document.getElementById('eh-file-preview');
        if (filePreview) {
            filePreview.style.display = 'none';
        }
        
        // Process response
        if (data.message) {
            addMessage(data.message, 'bot');
        } else if (data.response) {
            addMessage(data.response, 'bot');
        } else {
            addMessage("File processed successfully, but no response was provided.", 'bot');
        }
        
        // Re-enable input
        const chatInput = document.getElementById('eh-chatbot-input');
        if (chatInput) {
            chatInput.disabled = false;
            chatInput.focus();
        }
    })
    .catch(error => {
        console.error("Error uploading file:", error);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Clear the file
        currentFile = null;
        
        // Hide file preview
        const filePreview = document.getElementById('eh-file-preview');
        if (filePreview) {
            filePreview.style.display = 'none';
        }
        
        // Add error message
        addMessage("Sorry, I couldn't process your file. Please try again later.", 'bot', 'error');
        
        // Re-enable input
        const chatInput = document.getElementById('eh-chatbot-input');
        if (chatInput) {
            chatInput.disabled = false;
            chatInput.focus();
        }
    });
}

// Add this function to define `clearChat`
function clearChat() {
    console.log("Clearing chat...");
    const messagesContainer = document.getElementById('eh-chatbot-messages');
    if (messagesContainer) {
        messagesContainer.innerHTML = '<div class="eh-loading-messages"><i class="fas fa-spinner fa-spin"></i> Starting a new chat...</div>';
    }

    // Clear the current session ID
    currentSessionId = null;
    localStorage.removeItem('currentChatSessionId');

    // Create a new session
    createNewSession();
}

// Update the toggleChatbot function to ensure it works correctly
function toggleChatbot() {
    const container = document.getElementById('eh-chatbot-container');
    const toggleBtn = document.getElementById('eh-chatbot-toggle');
    
    if (!container || !toggleBtn) return;
    
    console.log("toggleChatbot called");
    
    // Get current display state
    const currentDisplay = window.getComputedStyle(container).display;
    console.log("Current display:", currentDisplay);
    
    if (currentDisplay === 'none') {
        // Show chatbot
        container.style.display = 'block';
        chatbotVisible = true;
        
        const messagesContainer = document.getElementById('eh-chatbot-messages');
        
        // If we have a saved session ID, restore it
        if (currentSessionId) {
            // Show loading indicator
            if (messagesContainer) {
                messagesContainer.innerHTML = '<div class="eh-loading-messages"><i class="fas fa-spinner fa-spin"></i> Loading chat...</div>';
            }
            
            // Load the session messages
            fetch(`/chatbot/api/sessions/${currentSessionId}/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Session not found');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.messages && data.messages.length > 0) {
                        // Display existing messages
                        messagesContainer.innerHTML = '';
                        data.messages.forEach(msg => {
                            addMessage(msg.content, msg.role === 'bot' ? 'bot' : 'user');
                        });
                    } else {
                        // No messages, create new session
                        createNewSession();
                    }
                })
                .catch(error => {
                    console.error("Error loading session:", error);
                    // If error loading session, create a new one
                    createNewSession();
                });
        } else {
            // No session ID, create a new one
            createNewSession();
        }
    } else {
        // Hide chatbot
        container.style.display = 'none';
        chatbotVisible = false;
        
        // Save current session ID before closing
        if (currentSessionId) {
            localStorage.setItem('currentChatSessionId', currentSessionId);
        }
    }
    
    // IMPORTANT FIX: Save state to localStorage as a string
    saveToLocalStorage('chatbotVisible', chatbotVisible.toString());
    
    // Mark the toggle button as having a click handler to prevent emergency handler
    toggleBtn._hasClickHandler = true;
    
    console.log("New display:", container.style.display);
}

// Fix the createNewSession function
function createNewSession() {
    console.log("Creating new session...");
    
    return new Promise((resolve, reject) => {
        // Get CSRF token before making the request
        const csrfToken = getCsrfToken();
        console.log("CSRF token obtained:", csrfToken ? "Yes" : "No");
        
        // Clear the messages container first
        const messagesContainer = document.getElementById('eh-chatbot-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '<div class="eh-loading-messages"><i class="fas fa-spinner fa-spin"></i> Creating new chat...</div>';
        }
        
        fetch('/chatbot/api/session/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin'
        })
        .then(response => {
            console.log("Session creation response status:", response.status);
            if (!response.ok) {
                return response.text().then(text => {
                    console.error("Session creation error response:", text);
                    throw new Error(`Failed to create session: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("Session created successfully:", data);
            
            // Check if session_id exists in the response
            if (!data.session_id) {
                throw new Error("Session ID not found in response");
            }
            
            // Set the current session ID
            currentSessionId = data.session_id;
            console.log("Current session ID set to:", currentSessionId);
            
            // Update session ID in form
            const sessionInput = document.getElementById('eh-session-id');
            if (sessionInput) {
                sessionInput.value = currentSessionId;
            }
            
            // Save session ID to localStorage
            saveToLocalStorage('currentChatSessionId', currentSessionId);
            
            // Clear loading message and add welcome message - THIS IS THE KEY PART
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
                
                // IMPORTANT: Always show a welcome message, even if not in the response
                const welcomeMessage = data.response || data.message || "Hello! I'm your Engineering Hub assistant. How can I help you today?";
                addMessage(welcomeMessage, 'bot');
            }
            
            resolve(data);
        })
        .catch(error => {
            console.error("Error creating session:", error);
            if (messagesContainer) {
                messagesContainer.innerHTML = '<div class="eh-error-message">Failed to start a new chat. Please try again later.</div>';
            }
            reject(error);
        });
    });
}

// Replace the handleSubmit function
function handleSubmit(e) {
    e.preventDefault();
    
    console.log("Handle submit called");
    
    // Check if we have a valid session ID
    if (!currentSessionId) {
        console.log("No valid session ID, creating new session first");
        createNewSession().then(() => {
            handleSubmit(e); // Try again after creating session
        });
        return;
    }
    
    // Get the chat input field
    const chatInput = document.getElementById('eh-chatbot-input');
    const message = chatInput.value.trim();
    
    // Check if we have a file or message
    if (!message && !currentFile) {
        console.log("No message or file to send");
        return;
    }
    
    // Clear input field immediately
    chatInput.value = '';
    
    // Disable input while processing
    chatInput.disabled = true;
    
    // If we have a file, handle it first
    if (currentFile) {
        console.log("File detected, calling uploadFile");
        uploadFile(message);
    } else {
        console.log("No file, calling sendMessage");
        sendMessage(message);
    }
}
        
// Handle file selection
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    console.log("File selected:", file.name, file.type, file.size);
    
    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('File size exceeds 5MB limit.');
        e.target.value = '';
        return;
    }
    
    // Store the file
    currentFile = file;
    
    // Show file preview
    const filePreview = document.getElementById('eh-file-preview');
    const fileNameElement = document.getElementById('eh-file-name');
    
    if (filePreview && fileNameElement) {
        fileNameElement.textContent = file.name;
        filePreview.style.display = 'flex';
        console.log("File preview displayed");
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' bytes';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Remove file
function removeFile() {
    console.log("Removing file");
    currentFile = null;
    
    // Hide file preview
    const filePreview = document.getElementById('eh-file-preview');
    if (filePreview) {
        filePreview.style.display = 'none';
    }
    
    // Clear file input
    const fileInput = document.getElementById('eh-file-upload');
    if (fileInput) {
        fileInput.value = '';
    }
}
// Toggle expanded mode
function toggleExpand() {
    console.log("Toggle expand called");
    const box = document.getElementById('eh-chatbot-box');
    const messagesContainer = document.getElementById('eh-chatbot-messages');
    
    if (!box || !messagesContainer) {
        console.error("Element not found:", {box, messagesContainer});
        return;
    }
    
    if (isExpanded) {
        // Collapse
        box.classList.remove('eh-expanded');
        isExpanded = false;
    } else {
        // Expand
        box.classList.add('eh-expanded');
        isExpanded = true;
    }
    console.log("Expand state:", isExpanded);
}

function toggleMinimize() {
    console.log("Toggle minimize called");
    const container = document.getElementById('eh-chatbot-container');
    const toggleBtn = document.getElementById('eh-chatbot-toggle');
    
    // Hide chatbot, show toggle button
    if (container) {
        container.style.display = 'none';
        chatbotVisible = false; // Add this line
        
        // Save current session ID to restore later
        localStorage.setItem('minimizedSessionId', currentSessionId);
        
        // IMPORTANT FIX: Set chatbotVisible to false in localStorage
        saveToLocalStorage('chatbotVisible', 'false');
        
        // Show toggle button
        if (toggleBtn) {
            toggleBtn.style.display = 'flex';
        }
    }
}

// Update the toggleMenu function to load chat history
function toggleMenu() {
    console.log("Toggle menu called");
    const menuPanel = document.getElementById('eh-chatbot-menu-panel');
    if (!menuPanel) return;

    if (menuPanel.style.display === 'block') {
        menuPanel.style.display = 'none';
    } else {
        menuPanel.style.display = 'block';

        // Load chat history
        const sessionsContainer = document.getElementById('eh-chatbot-sessions');
        if (sessionsContainer) {
            sessionsContainer.innerHTML = '<div class="eh-loading">Loading chat history...</div>';
            fetch('/chatbot/api/sessions/')
                .then(response => response.json())
                .then(data => {
                    const sessions = data.sessions || [];
                    if (sessions.length > 0) {
                        sessionsContainer.innerHTML = '';
                        sessions.forEach(session => {
                            const sessionElement = document.createElement('div');
                            sessionElement.className = 'eh-chatbot-session';
                            sessionElement.innerHTML = `
                                <div class="eh-session-info">
                                    <div class="eh-session-title">${session.title || 'Untitled Session'}</div>
                                    <div class="eh-session-date">${new Date(session.created_at).toLocaleString()}</div>
                                </div>
                                <button class="eh-delete-btn" data-session-id="${session.id}" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            `;
                            sessionsContainer.appendChild(sessionElement);

                            // Add click handler to load session (only for the info part)
                            const sessionInfo = sessionElement.querySelector('.eh-session-info');
                            sessionInfo.addEventListener('click', () => {
                                loadSession(session.id);
                                menuPanel.style.display = 'none'; // Close menu after selection
                            });
                            
                            // Add click handler for delete button
                            const deleteBtn = sessionElement.querySelector('.eh-delete-btn');
                            deleteBtn.addEventListener('click', (e) => {
                                e.stopPropagation(); // Prevent triggering the session load
                                deleteSession(session.id);
                            });
                        });
                    } else {
                        sessionsContainer.innerHTML = '<div class="eh-no-sessions">No chat history found.</div>';
                    }
                })
                .catch(error => {
                    console.error("Error loading chat history:", error);
                    sessionsContainer.innerHTML = '<div class="eh-error">Failed to load chat history.</div>';
                });
        }
    }
}

// Add this function to handle session deletion
function deleteSession(sessionId) {
    if (!confirm('Are you sure you want to delete this chat?')) {
        return;
    }
    
    fetch(`/chatbot/api/sessions/${sessionId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to delete session');
        }
        return response.json();
    })
    .then(data => {
        console.log('Session deleted successfully');
        // Refresh the menu to show updated list
        toggleMenu();
        toggleMenu();
        
        // If the deleted session was the current one, start a new chat
        if (currentSessionId === sessionId) {
            startNewChat();
        }
    })
    .catch(error => {
        console.error('Error deleting session:', error);
        alert('Failed to delete chat. Please try again.');
    });
}

function loadSession(sessionId) {
    console.log("Loading session:", sessionId);
    const messagesContainer = document.getElementById('eh-chatbot-messages');
    if (messagesContainer) {
        messagesContainer.innerHTML = '<div class="eh-loading-messages"><i class="fas fa-spinner fa-spin"></i> Loading chat...</div>';
        fetch(`/chatbot/api/sessions/${sessionId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.messages && data.messages.length > 0) {
                    messagesContainer.innerHTML = '';
                    data.messages.forEach(msg => {
                        if (msg.role === 'bot') {
                            addMessage(msg.content, 'bot');
                        } else if (msg.role === 'user') {
                            addMessage(msg.content, 'user');
                        }
                    });
                } else {
                    messagesContainer.innerHTML = '<div class="eh-no-messages">No messages in this session.</div>';
                }
            })
            .catch(error => {
                console.error("Error loading session:", error);
                messagesContainer.innerHTML = '<div class="eh-error">Failed to load chat.</div>';
            });
    }
}

// Update the closeChat function
function closeChat() {
    console.log("Close chat called");
    const container = document.getElementById('eh-chatbot-container');
    const toggleBtn = document.getElementById('eh-chatbot-toggle');

    if (container) {
        container.style.display = 'none';
        chatbotVisible = false;

        // CHANGE: Save the current session ID instead of clearing it
        if (currentSessionId) {
            localStorage.setItem('currentChatSessionId', currentSessionId);
        }
        
        // IMPORTANT FIX: Explicitly set chatbotVisible to 'false' in localStorage
        saveToLocalStorage('chatbotVisible', 'false');

        // Show toggle button
        if (toggleBtn) {
            toggleBtn.style.display = 'flex';
        }
    }
}

// Update the startNewChat function
function startNewChat() {
    console.log("Starting a new chat...");
    currentSessionId = null;
    localStorage.removeItem('currentChatSessionId');

    // Clear messages container
    const messagesContainer = document.getElementById('eh-chatbot-messages');
    if (messagesContainer) {
        messagesContainer.innerHTML = '<div class="eh-loading-messages"><i class="fas fa-spinner fa-spin"></i> Starting new chat...</div>';
    }

    // Create a new session
    createNewSession();
}        

// Initialize chatbot
// Initialize chatbot
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing chatbot...");
    
    // Check if the current session ID is valid
    if (currentSessionId && (
        currentSessionId.includes('\u201c') || 
        currentSessionId.includes('\u201d') ||
        !currentSessionId.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
    )) {
        console.log("Found invalid session ID format:", currentSessionId);
        clearInvalidSession();
    }
    
    // Set initial visibility
    const container = document.getElementById('eh-chatbot-container');
    if (container) {
        container.style.display = 'none';
        chatbotVisible = false;
        
        // Check if chatbot should be visible based on localStorage
        // IMPORTANT FIX: Use strict comparison to string 'true'
        const shouldBeVisible = localStorage.getItem('chatbotVisible') === 'true';
        console.log("Should chatbot be visible?", shouldBeVisible);
        
        if (shouldBeVisible) {
            // Show the chatbot
            container.style.display = 'block';
            chatbotVisible = true;
            
            // Load messages or create new session
            const messagesContainer = document.getElementById('eh-chatbot-messages');
            if (messagesContainer) {
                // Show loading indicator
                messagesContainer.innerHTML = '<div class="eh-loading-messages"><i class="fas fa-spinner fa-spin"></i> Loading chat...</div>';
                
                // Try to load existing session if we have a session ID
                if (currentSessionId) {
                    fetch(`/chatbot/api/sessions/${currentSessionId}/`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Session not found');
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data.messages && data.messages.length > 0) {
                                // Display existing messages
                                messagesContainer.innerHTML = '';
                                data.messages.forEach(msg => {
                                    addMessage(msg.content, msg.role === 'bot' ? 'bot' : 'user');
                                });
                            } else {
                                // No messages, create new session
                                createNewSession();
                            }
                        })
                        .catch(error => {
                            console.error("Error loading session:", error);
                            // If error loading session, create a new one
                            createNewSession();
                        });
                } else {
                    // No session ID, create a new one
                    createNewSession();
                }
            }
        }
    }

    // Fix for z-index issues
    const toggleBtn = document.getElementById('eh-chatbot-toggle');
    if (container && toggleBtn) {
        container.style.zIndex = '10000'; // Higher z-index
        toggleBtn.style.zIndex = '9999';  // Lower z-index
    }
    
    // Ensure submit button is visible
    const submitBtn = document.querySelector('.eh-chatbot-submit');
    if (submitBtn) {
        submitBtn.style.zIndex = '10001'; // Higher than container
        submitBtn.style.position = 'relative'; // Ensure z-index works
    }

    // Add event listeners
    const closeBtn = document.getElementById('eh-chatbot-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            console.log("Close button clicked");
            closeChat();
        });
    }
    
    // Add event listener for toggle button
    // Add event listener for toggle button
if (toggleBtn) {
    // Remove any existing click handlers first
    toggleBtn.removeEventListener('click', toggleChatbot);
    
    // Add our click handler
    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log("Toggle button clicked from main JS!");
        toggleChatbot();
    });
    
    // Mark the button as having a click handler
    toggleBtn._hasClickHandler = true;
}

    
    const chatForm = document.getElementById('eh-chatbot-form');
    if (chatForm) {
        chatForm.addEventListener('submit', handleSubmit);
    }
    
    const fileInput = document.getElementById('eh-file-upload');            
    if (fileInput) {
        console.log("Adding change event listener to file input");
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    const removeFileBtn = document.getElementById('eh-remove-file');
    if (removeFileBtn) {
        console.log("Adding click event listener to remove file button");
        removeFileBtn.addEventListener('click', removeFile);
    }
    
    const expandBtn = document.getElementById('eh-chatbot-expand');
    if (expandBtn) {
        expandBtn.addEventListener('click', toggleExpand);
    }
    
    const minimizeBtn = document.getElementById('eh-chatbot-minimize');            
    if (minimizeBtn) {
        minimizeBtn.addEventListener('click', toggleMinimize);
    }
    
    const menuBtn = document.getElementById('eh-chatbot-menu');
    if (menuBtn) {
        menuBtn.addEventListener('click', toggleMenu);
    }
    
    const fileButton = document.getElementById('eh-file-button');
    const fileUpload = document.getElementById('eh-file-upload');
    if (fileButton && fileUpload) {
        console.log("Adding click event listener to file button");
        fileButton.addEventListener('click', function(e) {
            e.preventDefault();
            console.log("File button clicked, triggering file input");
            fileUpload.click(); // Trigger the hidden file input
        });
    }
    
    const clearChatBtn = document.getElementById('eh-chatbot-new-chat');            
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', clearChat);
    }
    
    const newChatBtn = document.getElementById('eh-chatbot-new-chat');            
    if (newChatBtn) {
        newChatBtn.addEventListener('click', startNewChat);
    }
    
    // Close menu panel when clicking outside
    document.addEventListener('click', function(e) {
        const menuPanel = document.getElementById('eh-chatbot-menu-panel');
        const menuBtn = document.getElementById('eh-chatbot-menu');
        
        if (menuPanel && menuPanel.style.display === 'block') {
            // Check if the click is outside the menu panel and menu button
            if (!menuPanel.contains(e.target) && (!menuBtn || !menuBtn.contains(e.target))) {
                menuPanel.style.display = 'none';
            }
        }
    });
    
    // Add CSS for expanded and minimized states
    const style = document.createElement('style');
    style.textContent = `
        .eh-minimized {
            height: auto !important;
            overflow: hidden !important;
            transition: height 0.3s ease !important;
        }
        
        .eh-expanded {
            position: fixed !important;
            top: 10px !important;
            left: 10px !important;
            right: 10px !important;
            bottom: 10px !important;
            width: auto !important;
            height: auto !important;
            max-width: none !important;
            max-height: none !important;
            z-index: 10000 !important;
            display: flex !important;
            flex-direction: column !important;
        }
        
        .eh-expanded .eh-chatbot-messages {
            flex: 1 !important;
            height: auto !important;
            max-height: none !important;
        }
        
        .eh-expanded .eh-chatbot-footer {
            width: 100% !important;
            max-width: none !important;
        }
        
        .eh-expanded-input {
            width: 100% !important;
            max-width: none !important;
            flex: 1 !important;
        }
        
        .eh-expanded-footer {
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
        }
        
        .eh-expanded-footer form {
            flex: 1 !important;
            display: flex !important;
            width: 100% !important;
        }
    `;
    document.head.appendChild(style);
    
    console.log("Chatbot initialization complete");
});

window.addEventListener('load', function() {
    console.log("Window loaded - chatbot ready");
});
// Final check to ensure the script loaded completely
console.log("Chatbot.js file loaded completely without syntax errors");
