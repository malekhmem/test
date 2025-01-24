document.addEventListener("DOMContentLoaded", function() {
    const chatInput = document.querySelector("#chat-input");
    const sendButton = document.querySelector("#send-btn");
    const chatContainer = document.querySelector(".chat-container");
    const themeButton = document.querySelector("#theme-btn");
    const deleteButton = document.querySelector("#delete-btn");
    const chatbotImage = document.body.getAttribute("data-chatbot-img");
    const chatInterfaceImageElement = document.querySelector("#chat-interface-image");
    const chatInterfaceImage = chatInterfaceImageElement ? chatInterfaceImageElement.getAttribute("data-image-url") : null;
    const profileCircle = document.querySelector(".profile-circle");
    const dropdownMenu = document.querySelector(".dropdown-menu");
    const body = document.querySelector('body');
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector(".toggle");
    const searchBtn = document.querySelector(".search-box");
    const modeText = document.querySelector(".mode-text");
    const conversationIdElement = document.querySelector("#conversation-id");
    let currentConversationId = conversationIdElement ? conversationIdElement.value : null;

    console.log("Initial conversation ID:", currentConversationId);

    const loadDataFromLocalStorage = () => {
        const themeColor = localStorage.getItem("themeColor");
        if (themeColor === "light_mode") {
            body.classList.add("light-mode");
            themeButton.innerText = "dark_mode";
            modeText.innerText = "Dark mode";
        } else {
            body.classList.remove("light-mode");
            themeButton.innerText = "light_mode";
            modeText.innerText = "Light mode";
        }

        const defaultText = `
        <div class="default-text">
            <img src="${chatInterfaceImage}" alt="Chat Interface" style="width: 200px; height: auto;">
            <p>Start a conversation and explore. Your chat history will be displayed here.</p>
        </div>`;

        chatContainer.innerHTML = localStorage.getItem("all-chats") || defaultText;
        chatContainer.scrollTo(0, chatContainer.scrollHeight);
    };

    const escapeHtml = (unsafe) => {
        return unsafe.replace(/&/g, "&amp;")
                     .replace(/</g, "&lt;")
                     .replace(/>/g, "&gt;")
                     .replace(/"/g, "&quot;")
                     .replace(/'/g, "&#039;");
    };

    const createChatElement = (message, isUser) => {
        const chatDiv = document.createElement("div");
        chatDiv.classList.add("chat-message-container", isUser ? "user-message" : "bot-message");

        if (isUser) {
            const userInitial = profileCircle ? profileCircle.textContent.trim() : "U"; // Get the initial from the profile circle
            chatDiv.innerHTML = `
                <div class="profile-circle-small">${userInitial}</div>
                <div class="chat-bubble">
                    ${message}
                </div>
            `;
        } else {
            chatDiv.innerHTML = `
                <div class="chat-avatar">
                    <img src="${chatbotImage}" alt="Bot">
                </div>
                <div class="chat-bubble">
                    <div class="chat-bubble-header">
                        <button class="copy-code-btn">Copy</button>
                    </div>
                    ${message}
                </div>
            `;
        }

        return chatDiv;
    };

    const showTypingAnimation = () => {
        const typingHTML = `
            <div class="chat incoming">
                <div class="chat-avatar"><img src="${chatbotImage}" alt="Chatbot"></div>
                <div class="chat-message typing-animation">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        const typingDiv = document.createElement("div");
        typingDiv.innerHTML = typingHTML;
        chatContainer.appendChild(typingDiv.firstChild);
        chatContainer.scrollTo(0, chatContainer.scrollHeight);
    };

    const typeMessage = (message, element) => {
        let index = 0;
        element.style.whiteSpace = "pre-wrap"; // Ensure text wraps correctly
        element.style.wordWrap = "break-word"; // Ensure text breaks words as needed
        const interval = setInterval(() => {
            if (index < message.length) {
                element.innerHTML += escapeHtml(message.charAt(index));
                index++;
                chatContainer.scrollTo(0, chatContainer.scrollHeight);
            } else {
                clearInterval(interval);
                Prism.highlightAll(); // Apply syntax highlighting after typing effect
                addCopyCodeEventListeners();
            }
        }, 4); // Adjust typing speed here
    };

    const submitMessageToBackend = (message) => {
        const formData = new FormData();
        formData.append('messageText', message);
        formData.append('conversationId', currentConversationId);

        fetch("/ask", {
            method: "POST",
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            chatContainer.querySelector('.typing-animation')?.parentNode.removeChild(chatContainer.querySelector('.typing-animation'));

            const botResponseDiv = createChatElement('<pre><code class="language-c typing-effect"></code></pre>', false);
            chatContainer.appendChild(botResponseDiv);
            const typingEffectElement = botResponseDiv.querySelector('.typing-effect');
            typeMessage(data.answer, typingEffectElement);

            if (!currentConversationId && data.conversationId) {
                currentConversationId = data.conversationId;
                console.log("New conversation ID set:", currentConversationId);
            }
        })
        .catch(error => console.error('Error:', error));
    };

    const handleOutgoingChat = () => {
        const userText = chatInput.value.trim();
        if (!userText) return;

        chatInput.value = "";

        const outgoingChatHTML = `<pre>${escapeHtml(userText)}</pre>`;
        const outgoingChatDiv = createChatElement(outgoingChatHTML, true);
        chatContainer.appendChild(outgoingChatDiv);
        chatContainer.scrollTo(0, chatContainer.scrollHeight);

        showTypingAnimation();
        submitMessageToBackend(userText);
    };

    const addCopyCodeEventListeners = () => {
        const copyCodeButtons = document.querySelectorAll('.copy-code-btn');
        copyCodeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const codeElement = button.parentNode.nextElementSibling;
                const codeText = codeElement.innerText;
                navigator.clipboard.writeText(codeText).then(() => {
                    button.textContent = "Copied";
                    setTimeout(() => {
                        button.textContent = "Copy";
                    }, 2000);
                }).catch(err => {
                    console.error("Could not copy text: ", err);
                });
            });
        });
    };

    if (profileCircle) {
        profileCircle.addEventListener("click", () => {
            dropdownMenu.classList.toggle("show");
        });
    }

    window.addEventListener('click', function(event) {
        if (profileCircle && !profileCircle.contains(event.target) && !dropdownMenu.contains(event.target)) {
            dropdownMenu.classList.remove('show');
        }
    });

    deleteButton.addEventListener("click", () => {
        if (confirm("Are you sure you want to delete all the chats?")) {
            localStorage.removeItem("all-chats");
            loadDataFromLocalStorage();
        }
    });

    themeButton.addEventListener("click", () => {
        body.classList.toggle("light-mode");
        const newThemeColor = body.classList.contains("light-mode") ? "light_mode" : "dark_mode";
        localStorage.setItem("themeColor", newThemeColor);
        themeButton.innerText = newThemeColor;
        modeText.innerText = body.classList.contains("light-mode") ? "Dark mode" : "Light mode";
    });

    toggle.addEventListener("click", () => {
        sidebar.classList.toggle("close");
    });

    searchBtn.addEventListener("click", () => {
        sidebar.classList.remove('close');
    });

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleOutgoingChat();
        }
    });

    loadDataFromLocalStorage();
    sendButton.addEventListener("click", handleOutgoingChat);
});
