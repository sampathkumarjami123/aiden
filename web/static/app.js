const chat = document.getElementById("chat");
const form = document.getElementById("chatForm");
const sendBtn = document.getElementById("sendBtn");
const stopStreamingBtn = document.getElementById("stopStreamingBtn");
const messageInput = document.getElementById("message");
const modeInput = document.getElementById("mode");
const nameInput = document.getElementById("name");
const shortInput = document.getElementById("short");
const learningStyleInput = document.getElementById("learningStyle");
const focusGoalInput = document.getElementById("focusGoal");
const interestsInput = document.getElementById("interests");
const resetBtn = document.getElementById("resetBtn");
const exportBtn = document.getElementById("exportBtn");
const runtimePill = document.getElementById("runtimePill");
const localBanner = document.getElementById("localBanner");
const copyEnvBtn = document.getElementById("copyEnvBtn");
const runtimeInfoBtn = document.getElementById("runtimeInfoBtn");
const runtimeInfoPanel = document.getElementById("runtimeInfoPanel");
const runtimeModelValue = document.getElementById("runtimeModelValue");
const runtimeDevValue = document.getElementById("runtimeDevValue");
const runtimeProfileValue = document.getElementById("runtimeProfileValue");
const copyRuntimeBtn = document.getElementById("copyRuntimeBtn");
const copyProfileBtn = document.getElementById("copyProfileBtn");
const copyDebugBtn = document.getElementById("copyDebugBtn");
const lastCopiedAt = document.getElementById("lastCopiedAt");
const settingsBtn = document.getElementById("settingsBtn");
const settingsPanel = document.getElementById("settingsPanel");
const statsBtn = document.getElementById("statsBtn");
const statsPanel = document.getElementById("statsPanel");
const themeSelect = document.getElementById("themeSelect");
const bookmarksBtn = document.getElementById("bookmarksBtn");
const bookmarksPanel = document.getElementById("bookmarksPanel");
const bookmarksList = document.getElementById("bookmarksList");
const conversationTag = document.getElementById("conversationTag");
const addTagBtn = document.getElementById("addTagBtn");
const conversationTags = document.getElementById("conversationTags");
const darkModeToggle = document.getElementById("darkModeToggle");
const fontSizeSlider = document.getElementById("fontSizeSlider");
const fontSizeValue = document.getElementById("fontSizeValue");
const compactModeToggle = document.getElementById("compactModeToggle");
const soundToggle = document.getElementById("soundToggle");
const resetSettingsBtn = document.getElementById("resetSettingsBtn");

let currentRuntime = null;
let _copiedClearTimer = null;

const DEFAULT_SETTINGS = {
  darkMode: false,
  fontSize: 16,
  compactMode: false,
  soundEnabled: true,
};

const chatSearchInput = document.getElementById("chatSearchInput");
const chatSearchCounter = document.getElementById("chatSearchCounter");
const chatSearchPrevBtn = document.getElementById("chatSearchPrevBtn");
const chatSearchNextBtn = document.getElementById("chatSearchNextBtn");
const chatSearchClearBtn = document.getElementById("chatSearchClearBtn");

let chatSearchMatches = [];
let chatSearchCurrentIndex = -1;

const messageContextMenu = document.getElementById("messageContextMenu");
const contextCopyText = document.getElementById("contextCopyText");
const contextCopyFull = document.getElementById("contextCopyFull");
const contextDelete = document.getElementById("contextDelete");
const contextPin = document.getElementById("contextPin");

let currentContextMessage = null;
let pinnedMessages = new Set();

const conversationPanel = document.getElementById("conversationPanel");
const currentConversation = document.getElementById("currentConversation");
const toggleConversationListBtn = document.getElementById("toggleConversationListBtn");
const conversationActions = document.getElementById("conversationActions");
const conversationList = document.getElementById("conversationList");
const newConversationBtn = document.getElementById("newConversationBtn");
const renameConversationBtn = document.getElementById("renameConversationBtn");
const deleteConversationBtn = document.getElementById("deleteConversationBtn");

let conversations = {};
let currentConversationId = null;

const profileSelect = document.getElementById("profileSelect");
const newProfileNameInput = document.getElementById("newProfileName");
const createProfileBtn = document.getElementById("createProfileBtn");
const switchProfileBtn = document.getElementById("switchProfileBtn");
const deleteProfileBtn = document.getElementById("deleteProfileBtn");
const exportProfileBtn = document.getElementById("exportProfileBtn");
const importProfileBtn = document.getElementById("importProfileBtn");
const profileJsonInput = document.getElementById("profileJsonInput");

const taskInput = document.getElementById("taskInput");
const taskDueDateInput = document.getElementById("taskDueDate");
const taskPriorityInput = document.getElementById("taskPriority");
const taskEditIdInput = document.getElementById("taskEditId");
const addTaskBtn = document.getElementById("addTaskBtn");
const editTaskBtn = document.getElementById("editTaskBtn");
const postponeTaskBtn = document.getElementById("postponeTaskBtn");
const clearTasksBtn = document.getElementById("clearTasksBtn");
const taskList = document.getElementById("taskList");
const overdueBadge = document.getElementById("overdueBadge");
const filterAllBtn = document.getElementById("filterAll");
const filterPendingBtn = document.getElementById("filterPending");
const filterDoneBtn = document.getElementById("filterDone");
const taskSortSelect = document.getElementById("taskSort");

let cachedTasks = [];
let taskFilterMode = "all";
const memoryInput = document.getElementById("memoryInput");
const addMemoryBtn = document.getElementById("addMemoryBtn");
const clearMemoryBtn = document.getElementById("clearMemoryBtn");
const memoryList = document.getElementById("memoryList");
const memorySearchInput = document.getElementById("memorySearchInput");
const searchMemoryBtn = document.getElementById("searchMemoryBtn");
const memorySearchResults = document.getElementById("memorySearchResults");
const autocompleteList = document.getElementById("autocompleteList");
const typingIndicator = document.getElementById("typingIndicator");

const AUTOCOMPLETE_PREFIXES = [
  { prefix: "summarize:", desc: "Get key points" },
  { prefix: "plan:", desc: "Build an action plan" },
  { prefix: "checklist:", desc: "Create a checklist" },
  { prefix: "focus:", desc: "Set focus goal" },
  { prefix: "break:", desc: "Record a break" },
  { prefix: "reflect:", desc: "Reflection prompt" },
  { prefix: "learn:", desc: "Learning goal" },
];

let autocompleteIndex = -1;
let activeChatAbortController = null;

function setStreamingUiState(isStreaming) {
  if (sendBtn) sendBtn.disabled = isStreaming;
  if (messageInput) messageInput.disabled = isStreaming;
  if (stopStreamingBtn) {
    stopStreamingBtn.classList.toggle("hidden", !isStreaming);
    stopStreamingBtn.disabled = !isStreaming;
  }
}
function getLocalDateStamp() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatRelativeTime(date) {
  if (!date) return "now";
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return "now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

function addMessage(role, text) {
  const wrapper = document.createElement("article");
  wrapper.className = `msg ${role}`;
  const timestamp = new Date();

  const tag = document.createElement("div");
  tag.className = "tag";
  tag.textContent = role === "user" ? "YOU" : "AIDEN";

  const time = document.createElement("div");
  time.className = "msg-time";
  time.textContent = formatRelativeTime(timestamp);
  time.title = timestamp.toLocaleTimeString();

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  const bookmarkBtn = document.createElement("button");
  bookmarkBtn.className = "bookmark-msg-btn";
  bookmarkBtn.textContent = "📌";
  bookmarkBtn.type = "button";
  bookmarkBtn.title = "Bookmark message";
  bookmarkBtn.addEventListener("click", () => {
    bookmarkMessage(wrapper);
  });

  wrapper.appendChild(tag);
  wrapper.appendChild(time);
  wrapper.appendChild(bubble);
  wrapper.appendChild(bookmarkBtn);

  if (role === "aiden") {
    const reactions = document.createElement("div");
    reactions.className = "reactions";
    const reactionEmojis = [
      { emoji: "👍", label: "helpful" },
      { emoji: "❤️", label: "great" },
      { emoji: "🎯", label: "onpoint" },
      { emoji: "😕", label: "confused" },
    ];
    reactionEmojis.forEach((r) => {
      const btn = document.createElement("button");
      btn.className = "reaction-btn";
      btn.textContent = r.emoji;
      btn.title = r.label;
      btn.type = "button";
      btn.addEventListener("click", () => recordReaction(r.label, text));
      reactions.appendChild(btn);
    });
    wrapper.appendChild(reactions);

    const suggestedReplies = document.createElement("div");
    suggestedReplies.className = "suggested-replies";
    const suggestions = generateSuggestedReplies(text);
    suggestions.forEach((suggestion) => {
      const btn = document.createElement("button");
      btn.className = "suggested-reply-btn";
      btn.textContent = suggestion;
      btn.type = "button";
      btn.addEventListener("click", () => sendSuggestedReply(suggestion));
      suggestedReplies.appendChild(btn);
    });
    wrapper.appendChild(suggestedReplies);
  }

  wrapper.addEventListener("contextmenu", (e) => showMessageContextMenu(e, wrapper));

  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
  
  saveMessageToCurrentConversation(role, text);
}

function createStreamingMessage(role) {
  const wrapper = document.createElement("article");
  wrapper.className = `msg ${role}`;
  const timestamp = new Date();

  const tag = document.createElement("div");
  tag.className = "tag";
  tag.textContent = role === "user" ? "YOU" : "AIDEN";

  const time = document.createElement("div");
  time.className = "msg-time";
  time.textContent = formatRelativeTime(timestamp);
  time.title = timestamp.toLocaleTimeString();

  const bubble = document.createElement("div");
  bubble.className = "bubble streaming";
  bubble.textContent = "";

  wrapper.appendChild(tag);
  wrapper.appendChild(time);
  wrapper.appendChild(bubble);
  wrapper.addEventListener("contextmenu", (e) => showMessageContextMenu(e, wrapper));
  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;

  return {
    append(text) {
      bubble.textContent += text;
      chat.scrollTop = chat.scrollHeight;
    },
    finalize() {
      bubble.classList.remove("streaming");
      saveMessageToCurrentConversation(role, bubble.textContent || "");
      if (role === "aiden") {
        const reactions = document.createElement("div");
        reactions.className = "reactions";
        [
          { emoji: "👍", label: "helpful" },
          { emoji: "❤️", label: "great" },
          { emoji: "🎯", label: "onpoint" },
          { emoji: "😕", label: "confused" },
        ].forEach((r) => {
          const btn = document.createElement("button");
          btn.className = "reaction-btn";
          btn.textContent = r.emoji;
          btn.title = r.label;
          btn.type = "button";
          btn.addEventListener("click", () => recordReaction(r.label, bubble.textContent || ""));
          reactions.appendChild(btn);
        });
        wrapper.appendChild(reactions);

        const suggestedReplies = document.createElement("div");
        suggestedReplies.className = "suggested-replies";
        const suggestions = generateSuggestedReplies(bubble.textContent || "");
        suggestions.forEach((suggestion) => {
          const btn = document.createElement("button");
          btn.className = "suggested-reply-btn";
          btn.textContent = suggestion;
          btn.type = "button";
          btn.addEventListener("click", () => sendSuggestedReply(suggestion));
          suggestedReplies.appendChild(btn);
        });
        wrapper.appendChild(suggestedReplies);
      }
    },
    remove() {
      wrapper.remove();
    },
    getText() {
      return bubble.textContent || "";
    },
  };
}

async function streamChatReply(text, signal, options = {}) {
  const preservePartialOnError = options.preservePartialOnError === true;
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal,
    body: JSON.stringify({
      message: text,
      mode: modeInput.value,
      name: nameInput.value,
      short_responses: shortInput.checked,
      learning_style: learningStyleInput.value,
      focus_goal: focusGoalInput.value,
      interests: interestsInput.value,
    }),
  });

  if (!response.ok || !response.body) {
    const errorText = await response.text();
    throw new Error(errorText || "Request failed");
  }

  const assistant = createStreamingMessage("aiden");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalPayload = null;
  let streamError = "";
  let finalized = false;

  const applyStreamEvent = (item) => {
    if (!item || typeof item !== "object") {
      return;
    }
    if (item.type === "chunk") {
      assistant.append(item.text || "");
      return;
    }
    if (item.type === "final") {
      finalPayload = item;
      return;
    }
    if (item.type === "error") {
      streamError = item.error || "Streaming request failed.";
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let lineBreak = buffer.indexOf("\n");
      while (lineBreak >= 0) {
        const line = buffer.slice(0, lineBreak).trim();
        buffer = buffer.slice(lineBreak + 1);
        if (line) {
          try {
            applyStreamEvent(JSON.parse(line));
          } catch (_parseError) {
            // Ignore malformed stream lines and continue consuming.
          }
        }
        lineBreak = buffer.indexOf("\n");
      }
    }

    buffer += decoder.decode();
    const trailing = buffer.trim();
    if (trailing) {
      try {
        applyStreamEvent(JSON.parse(trailing));
      } catch (_parseError) {
        // Ignore malformed trailing chunk.
      }
    }
  } finally {
    const built = assistant.getText().trim();
    if (built) {
      if (streamError && !preservePartialOnError) {
        assistant.remove();
      } else {
        assistant.finalize();
      }
      finalized = true;
    } else {
      assistant.remove();
      finalized = true;
    }
  }

  if (!finalized) {
    assistant.finalize();
  }

  if (streamError) {
    throw new Error(streamError);
  }

  return finalPayload;
}

async function streamChatReplyWithRetry(text, signal) {
  let attempt = 0;
  while (attempt < 2) {
    try {
      return await streamChatReply(text, signal, {
        preservePartialOnError: false,
      });
    } catch (error) {
      if (error && error.name === "AbortError") {
        throw error;
      }
      attempt += 1;
      if (attempt >= 2) {
        throw error;
      }
      addMessage("aiden", "Stream interrupted, retrying once...");
      await new Promise((resolve) => setTimeout(resolve, 300));
    }
  }
  return null;
}

async function fetchChatFallback(text) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: text,
      mode: modeInput.value,
      name: nameInput.value,
      short_responses: shortInput.checked,
      learning_style: learningStyleInput.value,
      focus_goal: focusGoalInput.value,
      interests: interestsInput.value,
    }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Fallback request failed");
  }
  return data;
}

function recordReaction(label, messageText) {
  addMessage("aiden", `Feedback recorded: ${label}. Thanks for helping me improve!`);
}

function generateSuggestedReplies(messageText) {
  const suggestions = [];
  const lower = messageText.toLowerCase();

  if (lower.includes("question") || lower.includes("?")) {
    suggestions.push("Can you elaborate?", "How does that work?", "Tell me more");
  } else if (
    lower.includes("help") ||
    lower.includes("problem") ||
    lower.includes("issue")
  ) {
    suggestions.push(
      "What should I do?",
      "Can you help me fix this?",
      "Do you have a solution?"
    );
  } else if (lower.includes("plan") || lower.includes("schedule")) {
    suggestions.push(
      "When should I start?",
      "What's the timeline?",
      "How long will it take?"
    );
  } else if (lower.includes("idea") || lower.includes("suggest")) {
    suggestions.push(
      "I like that idea",
      "Can we try it?",
      "What's next?"
    );
  } else if (lower.includes("summary") || lower.includes("recap")) {
    suggestions.push("That's clear", "Any other points?", "Let's move on");
  } else {
    suggestions.push("Tell me more", "What else?", "I understand");
  }

  return suggestions.slice(0, 3);
}

function sendSuggestedReply(text) {
  messageInput.value = text;
  messageInput.focus();
  form.dispatchEvent(new Event("submit"));
}

function calculateStatistics() {
  if (!conversations || Object.keys(conversations).length === 0) {
    renderStatistics({ totalMessages: 0, userMessages: 0, aidenMessages: 0, totalWords: 0, avgLength: 0, duration: "0m", topWords: [] });
    return;
  }

  let totalMessages = 0;
  let userMessages = 0;
  let aidenMessages = 0;
  let totalWords = 0;
  let wordFrequency = {};
  let oldestTime = Date.now();
  let newestTime = 0;

  Object.values(conversations).forEach((conv) => {
    if (conv.messages && Array.isArray(conv.messages)) {
      conv.messages.forEach((msg) => {
        totalMessages++;
        const isUser = msg.sender === "user";
        if (isUser) userMessages++;
        else aidenMessages++;

        const words = (msg.text || "").toLowerCase().split(/\s+/).filter((w) => w.length > 2);
        totalWords += words.length;

        words.forEach((word) => {
          wordFrequency[word] = (wordFrequency[word] || 0) + 1;
        });
      });
    }

    if (conv.created) oldestTime = Math.min(oldestTime, new Date(conv.created).getTime());
    if (conv.updated) newestTime = Math.max(newestTime, new Date(conv.updated).getTime());
  });

  const avgLength = totalMessages > 0 ? Math.round(totalWords / totalMessages) : 0;

  // Calculate duration
  let duration = "0m";
  if (newestTime > oldestTime) {
    const durationMs = newestTime - oldestTime;
    const days = Math.floor(durationMs / (1000 * 60 * 60 * 24));
    const hours = Math.floor((durationMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));

    if (days > 0) duration = `${days}d ${hours}h`;
    else if (hours > 0) duration = `${hours}h ${minutes}m`;
    else duration = `${minutes}m`;
  }

  // Get top 5 words
  const topWords = Object.entries(wordFrequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([word, count]) => ({ word, count }));

  renderStatistics({
    totalMessages,
    userMessages,
    aidenMessages,
    totalWords,
    avgLength,
    duration,
    topWords,
  });
}

function renderStatistics(stats) {
  const statTotalMessages = document.getElementById("statTotalMessages");
  const statUserMessages = document.getElementById("statUserMessages");
  const statAidenMessages = document.getElementById("statAidenMessages");
  const statTotalWords = document.getElementById("statTotalWords");
  const statAvgLength = document.getElementById("statAvgLength");
  const statDuration = document.getElementById("statDuration");
  const statTopWords = document.getElementById("statTopWords");

  if (statTotalMessages) statTotalMessages.textContent = stats.totalMessages;
  if (statUserMessages) statUserMessages.textContent = stats.userMessages;
  if (statAidenMessages) statAidenMessages.textContent = stats.aidenMessages;
  if (statTotalWords) statTotalWords.textContent = stats.totalWords;
  if (statAvgLength) statAvgLength.textContent = stats.avgLength + " words";
  if (statDuration) statDuration.textContent = stats.duration;

  if (statTopWords) {
    statTopWords.innerHTML = (stats.topWords || [])
      .map((item) => `<div class="top-word-item"><span class="word">${item.word}</span><span class="count">${item.count}</span></div>`)
      .join("");
  }
}

// Bookmarks Feature
let bookmarkedMessages = JSON.parse(localStorage.getItem("bookmarkedMessages")) || [];

function bookmarkMessage(messageElement) {
  const text = messageElement.querySelector(".bubble")?.textContent || messageElement.textContent;
  const sender = messageElement.classList.contains("user") ? "user" : "aiden";
  const timestamp = new Date().toISOString();
  
  const bookmark = { id: Date.now(), text: text.substring(0, 100), fullText: text, sender, timestamp };
  bookmarkedMessages.push(bookmark);
  localStorage.setItem("bookmarkedMessages", JSON.stringify(bookmarkedMessages));
  
  messageElement.classList.add("bookmarked");
  if (bookmarksBtn) bookmarksBtn.textContent = `📌 Bookmarks (${bookmarkedMessages.length})`;
}

function renderBookmarks() {
  if (!bookmarksList) return;
  bookmarksList.innerHTML = bookmarkedMessages
    .map((b) => `<div class="bookmark-item">${b.sender === "user" ? "👤" : "🤖"} ${b.text}<span class="bookmark-remove" data-id="${b.id}">✕</span></div>`)
    .join("");
  
  document.querySelectorAll(".bookmark-remove")?.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      bookmarkedMessages = bookmarkedMessages.filter((b) => b.id !== Number(e.target.dataset.id));
      localStorage.setItem("bookmarkedMessages", JSON.stringify(bookmarkedMessages));
      renderBookmarks();
      if (bookmarksBtn) bookmarksBtn.textContent = `📌 Bookmarks (${bookmarkedMessages.length})`;
    });
  });
}

// Theme Feature
function setTheme(theme) {
  const root = document.documentElement;
  const themeMap = {
    light: { bg0: "#ffffff", bg1: "#f5f5f5", card: "#ffffff", ink: "#1a1a1a", muted: "#666", line: "#ddd", brand: "#007acc", accent: "#007acc" },
    dark: { bg0: "#1a1f28", bg1: "#232a36", card: "rgba(35, 42, 54, 0.92)", ink: "#e8e9eb", muted: "#8a92a0", line: "#3a4455", brand: "#00d4ff", accent: "#00d4ff" },
    nord: { bg0: "#252932", bg1: "#2e3440", card: "rgba(46, 52, 64, 0.92)", ink: "#eceff4", muted: "#81a1c1", line: "#4c566a", brand: "#88c0d0", accent: "#88c0d0" },
    dracula: { bg0: "#282a36", bg1: "#21222c", card: "rgba(33, 34, 44, 0.92)", ink: "#f8f8f2", muted: "#6272a4", line: "#44475a", brand: "#ff79c6", accent: "#ff79c6" },
    solarized: { bg0: "#fdf6e3", bg1: "#eee8d5", card: "#fdf6e3", ink: "#657b83", muted: "#93a1a1", line: "#d6d0be", brand: "#268bd2", accent: "#268bd2" },
  };
  
  const colors = themeMap[theme] || themeMap.light;
  Object.entries(colors).forEach(([key, value]) => {
    root.style.setProperty(`--${key}`, value);
  });
  
  localStorage.setItem("selectedTheme", theme);
  if (themeSelect) themeSelect.value = theme;
}

// Conversation Tagging Feature
function addConversationTag(tag) {
  if (!currentConversationId || !conversations[currentConversationId]) return;
  
  if (!conversations[currentConversationId].tags) {
    conversations[currentConversationId].tags = [];
  }
  
  const tags = tag.split(",").map((t) => t.trim().toLowerCase()).filter((t) => t);
  conversations[currentConversationId].tags = [...new Set([...conversations[currentConversationId].tags, ...tags])];
  saveConversations();
  renderConversationTags();
}

function renderConversationTags() {
  if (!conversationTags || !currentConversationId) return;
  
  const tags = conversations[currentConversationId]?.tags || [];
  conversationTags.innerHTML = tags
    .map((tag) => `<span class="tag">#${tag} <button class="tag-remove" data-tag="${tag}">✕</button></span>`)
    .join("");
  
  document.querySelectorAll(".tag-remove")?.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const tag = e.target.dataset.tag;
      conversations[currentConversationId].tags = conversations[currentConversationId].tags.filter((t) => t !== tag);
      saveConversations();
      renderConversationTags();
    });
  });
}

function loadSettings() {
  const stored = localStorage.getItem("aidenSettings");
  if (!stored) return DEFAULT_SETTINGS;
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

function saveSettings(settings) {
  localStorage.setItem("aidenSettings", JSON.stringify(settings));
  applySettings(settings);
}

function applySettings(settings) {
  const root = document.documentElement;
  
  if (settings.darkMode) {
    root.classList.add("dark-mode");
  } else {
    root.classList.remove("dark-mode");
  }
  
  root.style.setProperty("--font-size-base", settings.fontSize + "px");
  
  if (settings.compactMode) {
    root.classList.add("compact-mode");
  } else {
    root.classList.remove("compact-mode");
  }
  
  if (settings.soundEnabled) {
    root.classList.remove("no-sound");
  } else {
    root.classList.add("no-sound");
  }
}

function playNotificationSound() {
  const settings = loadSettings();
  if (!settings.soundEnabled) return;
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.frequency.value = 800;
    oscillator.type = "sine";
    gain.gain.setValueAtTime(0.3, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.1);
  } catch (e) {
  }
}

function searchChatMessages(query) {
  chatSearchMatches = [];
  chatSearchCurrentIndex = -1;
  
  if (!query.trim()) {
    clearChatSearch();
    return;
  }

  const messages = chat.querySelectorAll(".msg");
  const lowerQuery = query.toLowerCase();

  messages.forEach((msg, idx) => {
    const bubble = msg.querySelector(".bubble");
    if (!bubble) return;

    const text = bubble.textContent;
    if (text.toLowerCase().includes(lowerQuery)) {
      chatSearchMatches.push(idx);
    }
  });

  if (chatSearchMatches.length > 0) {
    goToChatSearchMatch(0);
  }

  updateChatSearchCounter();
}

function goToChatSearchMatch(index) {
  const messages = chat.querySelectorAll(".msg");

  messages.forEach((msg) => {
    msg.classList.remove("search-match", "search-active");
    const bubble = msg.querySelector(".bubble");
    if (bubble) {
      const highlighted = bubble.innerHTML;
      bubble.innerHTML = highlighted.replace(/<mark[^>]*>|<\/mark>/g, "");
    }
  });

  if (index < 0 || index >= chatSearchMatches.length) {
    updateChatSearchCounter();
    return;
  }

  chatSearchCurrentIndex = index;
  const msgIndex = chatSearchMatches[index];
  const msg = messages[msgIndex];

  if (!msg) return;

  msg.classList.add("search-match");
  const bubble = msg.querySelector(".bubble");
  if (bubble && chatSearchInput.value.trim()) {
    const query = chatSearchInput.value.trim();
    const text = bubble.textContent;
    const regex = new RegExp(`(${query})`, "gi");
    bubble.innerHTML = text.replace(regex, "<mark>$1</mark>");
    msg.classList.add("search-active");
  }

  msg.scrollIntoView({ behavior: "smooth", block: "center" });
  updateChatSearchCounter();
}

function clearChatSearch() {
  const messages = chat.querySelectorAll(".msg");
  messages.forEach((msg) => {
    msg.classList.remove("search-match", "search-active");
    const bubble = msg.querySelector(".bubble");
    if (bubble) {
      bubble.innerHTML = bubble.textContent;
    }
  });
  chatSearchMatches = [];
  chatSearchCurrentIndex = -1;
  updateChatSearchCounter();
}

function updateChatSearchCounter() {
  const total = chatSearchMatches.length;
  const current = chatSearchCurrentIndex >= 0 ? chatSearchCurrentIndex + 1 : 0;
  chatSearchCounter.textContent = `${current} / ${total}`;
}

function showMessageContextMenu(event, msgElement) {
  event.preventDefault();
  currentContextMessage = msgElement;
  
  const isUserMessage = msgElement.classList.contains("user");
  contextDelete.style.display = isUserMessage ? "block" : "none";
  contextPin.textContent = pinnedMessages.has(msgElement) ? "Unpin Message" : "Pin Message";
  
  messageContextMenu.classList.remove("hidden");
  messageContextMenu.style.left = event.clientX + "px";
  messageContextMenu.style.top = event.clientY + "px";
}

function hideMessageContextMenu() {
  messageContextMenu.classList.add("hidden");
  currentContextMessage = null;
}

function copyMessageText() {
  if (!currentContextMessage) return;
  const bubble = currentContextMessage.querySelector(".bubble");
  if (bubble) {
    const text = bubble.textContent;
    navigator.clipboard.writeText(text).then(() => {
      hideMessageContextMenu();
      addMessage("aiden", "Message copied to clipboard.");
    }).catch(() => {
      addMessage("aiden", "Failed to copy message.");
    });
  }
}

function copyMessageFull() {
  if (!currentContextMessage) return;
  const tag = currentContextMessage.querySelector(".tag");
  const time = currentContextMessage.querySelector(".msg-time");
  const bubble = currentContextMessage.querySelector(".bubble");
  
  const fullText = `[${tag?.textContent || ""}] ${time?.textContent || ""}\n${bubble?.textContent || ""}`;
  navigator.clipboard.writeText(fullText).then(() => {
    hideMessageContextMenu();
    addMessage("aiden", "Full message copied to clipboard.");
  }).catch(() => {
    addMessage("aiden", "Failed to copy message.");
  });
}

function deleteMessage() {
  if (!currentContextMessage || !currentContextMessage.classList.contains("user")) {
    return;
  }
  hideMessageContextMenu();
  currentContextMessage.style.opacity = "0.5";
  currentContextMessage.style.textDecoration = "line-through";
  currentContextMessage.insertAdjacentHTML("beforeend", " <small style=\"color: var(--muted);\"> (deleted)</small>");
  addMessage("aiden", "Message marked as deleted.");
}

function togglePinnedMessage() {
  if (!currentContextMessage) return;
  
  if (pinnedMessages.has(currentContextMessage)) {
    pinnedMessages.delete(currentContextMessage);
    currentContextMessage.classList.remove("pinned");
    hideMessageContextMenu();
    addMessage("aiden", "Message unpinned.");
  } else {
    pinnedMessages.add(currentContextMessage);
    currentContextMessage.classList.add("pinned");
    hideMessageContextMenu();
    addMessage("aiden", "Message pinned to top.");
  }
}

function loadConversations() {
  const stored = localStorage.getItem("aidenConversations");
  const meta = localStorage.getItem("aidenConversationsMeta");
  
  if (!stored || !meta) {
    createNewConversation("Conversation 1");
    return;
  }
  
  try {
    conversations = JSON.parse(stored);
    const { currentId, count } = JSON.parse(meta);
    currentConversationId = currentId && conversations[currentId] ? currentId : Object.keys(conversations)[0];
  } catch {
    conversations = {};
    createNewConversation("Conversation 1");
  }
}

function saveConversations() {
  localStorage.setItem("aidenConversations", JSON.stringify(conversations));
  localStorage.setItem("aidenConversationsMeta", JSON.stringify({
    currentId: currentConversationId,
    count: Object.keys(conversations).length,
  }));
}

function createNewConversation(name) {
  const id = "conv_" + Date.now();
  conversations[id] = {
    id,
    name: name || `Conversation ${Object.keys(conversations).length + 1}`,
    messages: [],
    created: new Date().toISOString(),
    updated: new Date().toISOString(),
  };
  currentConversationId = id;
  saveConversations();
  updateConversationUI();
  switchConversation(id);
}

function switchConversation(id) {
  if (!conversations[id]) return;
  
  currentConversationId = id;
  const conv = conversations[id];
  currentConversation.textContent = conv.name;
  chat.innerHTML = "";
  
  if (Array.isArray(conv.messages) && conv.messages.length > 0) {
    conv.messages.forEach((msg) => {
      const wrapper = document.createElement("article");
      wrapper.className = `msg ${msg.role}`;
      wrapper.setAttribute("data-timestamp", msg.timestamp || new Date().toISOString());
      
      const tag = document.createElement("div");
      tag.className = "tag";
      tag.textContent = msg.role === "user" ? "YOU" : "AIDEN";
      
      const time = document.createElement("div");
      time.className = "msg-time";
      time.textContent = formatRelativeTime(new Date(msg.timestamp));
      time.title = new Date(msg.timestamp).toLocaleTimeString();
      
      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = msg.text;
      
      wrapper.appendChild(tag);
      wrapper.appendChild(time);
      wrapper.appendChild(bubble);
      
      if (msg.role === "aiden") {
        const reactions = document.createElement("div");
        reactions.className = "reactions";
        [
          { emoji: "👍", label: "helpful" },
          { emoji: "❤️", label: "great" },
          { emoji: "🎯", label: "onpoint" },
          { emoji: "😕", label: "confused" },
        ].forEach((r) => {
          const btn = document.createElement("button");
          btn.className = "reaction-btn";
          btn.textContent = r.emoji;
          btn.title = r.label;
          btn.type = "button";
          btn.addEventListener("click", () => recordReaction(r.label, msg.text));
          reactions.appendChild(btn);
        });
        wrapper.appendChild(reactions);

        const suggestedReplies = document.createElement("div");
        suggestedReplies.className = "suggested-replies";
        const suggestions = generateSuggestedReplies(msg.text);
        suggestions.forEach((suggestion) => {
          const btn = document.createElement("button");
          btn.className = "suggested-reply-btn";
          btn.textContent = suggestion;
          btn.type = "button";
          btn.addEventListener("click", () => sendSuggestedReply(suggestion));
          suggestedReplies.appendChild(btn);
        });
        wrapper.appendChild(suggestedReplies);
      }
      
      wrapper.addEventListener("contextmenu", (e) => showMessageContextMenu(e, wrapper));
      chat.appendChild(wrapper);
    });
  } else {
    addMessage("aiden", `Welcome to this conversation: ${conv.name}. Ready to chat!`);
  }
  
  chat.scrollTop = chat.scrollHeight;
  saveConversations();
  renderConversationTags();
  updateConversationUI();
}

function renameConversation() {
  if (!currentConversationId) return;
  const newName = prompt("Enter new conversation name:", conversations[currentConversationId].name);
  if (newName && newName.trim()) {
    conversations[currentConversationId].name = newName.trim();
    conversations[currentConversationId].updated = new Date().toISOString();
    currentConversation.textContent = newName.trim();
    saveConversations();
    updateConversationUI();
    addMessage("aiden", `Conversation renamed to "${newName.trim()}".`);
  }
}

function deleteConversation(id) {
  if (!conversations[id]) return;
  if (!confirm(`Delete conversation "${conversations[id].name}"? This cannot be undone.`)) return;
  
  delete conversations[id];
  
  if (currentConversationId === id) {
    const remaining = Object.keys(conversations);
    if (remaining.length === 0) {
      createNewConversation("Conversation 1");
    } else {
      switchConversation(remaining[0]);
    }
  }
  
  saveConversations();
  updateConversationUI();
  addMessage("aiden", "Conversation deleted.");
}

function updateConversationUI() {
  conversationList.innerHTML = "";
  
  Object.entries(conversations).forEach(([id, conv]) => {
    const li = document.createElement("li");
    li.className = "conversation-item";
    if (id === currentConversationId) li.classList.add("active");
    
    const name = document.createElement("span");
    name.className = "conversation-name";
    name.textContent = conv.name;
    name.addEventListener("click", () => switchConversation(id));
    
    const msgCount = document.createElement("span");
    msgCount.className = "conversation-count";
    msgCount.textContent = `${conv.messages?.length || 0} msgs`;
    
    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "conversation-delete";
    deleteBtn.textContent = "✕";
    deleteBtn.addEventListener("click", () => deleteConversation(id));
    
    li.appendChild(name);
    li.appendChild(msgCount);
    li.appendChild(deleteBtn);
    conversationList.appendChild(li);
  });
}

function saveMessageToCurrentConversation(role, text, timestamp) {
  if (!currentConversationId || !conversations[currentConversationId]) {
    createNewConversation("Conversation 1");
  }
  
  conversations[currentConversationId].messages.push({
    role,
    text,
    timestamp: timestamp?.toISOString() || new Date().toISOString(),
  });
  
  conversations[currentConversationId].updated = new Date().toISOString();
  saveConversations();
  calculateStatistics();
}

function syncPrefs(prefs) {
  if (!prefs) {
    return;
  }
  if (typeof prefs.mode === "string") {
    modeInput.value = prefs.mode;
  }
  if (typeof prefs.name === "string") {
    nameInput.value = prefs.name;
  }
  if (typeof prefs.short_responses === "string") {
    shortInput.checked = prefs.short_responses === "true";
  }
  if (typeof prefs.learning_style === "string") {
    learningStyleInput.value = prefs.learning_style;
  }
  if (typeof prefs.focus_goal === "string") {
    focusGoalInput.value = prefs.focus_goal;
  }
  if (typeof prefs.interests === "string") {
    interestsInput.value = prefs.interests;
  }
  if (typeof prefs.active_profile === "string") {
    profileSelect.value = prefs.active_profile;
  }
  if (runtimeProfileValue) {
    runtimeProfileValue.textContent = prefs?.active_profile || "default";
  }
}

function syncProfiles(profiles, activeProfile) {
  if (!Array.isArray(profiles)) {
    return;
  }
  profileSelect.innerHTML = "";
  for (const profile of profiles) {
    const option = document.createElement("option");
    option.value = profile;
    option.textContent = profile;
    if (profile === activeProfile) {
      option.selected = true;
    }
    profileSelect.appendChild(option);
  }
}

function syncRuntime(runtime) {
  if (!runtimePill || !runtime) {
    return;
  }
  currentRuntime = runtime;
  const isLive = runtime.has_model === true;
  runtimePill.classList.remove("live", "local");
  runtimePill.classList.add(isLive ? "live" : "local");
  runtimePill.textContent = isLive ? "Live Model" : "Local Dev Mode";
  if (localBanner) {
    localBanner.classList.toggle("hidden", isLive);
  }
  if (runtimeModelValue) {
    runtimeModelValue.textContent = isLive ? "connected" : "disconnected";
  }
  if (runtimeDevValue) {
    runtimeDevValue.textContent = runtime.dev_mode ? "enabled" : "disabled";
  }
}

async function copyEnvSetup() {
  const envSnippet = "OPENAI_API_KEY=your_api_key_here\nAIDEN_MODEL=gpt-5.3-codex\nAIDEN_DEV_MODE=true\n";
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(envSnippet);
    addMessage("aiden", "Copied .env setup snippet to clipboard.");
    return;
  }
  addMessage("aiden", "Clipboard API unavailable. Paste this into .env:\n" + envSnippet);
}

async function copyRuntimeJson() {
  const payload = {
    ...(currentRuntime || {}),
    active_profile: runtimeProfileValue?.textContent || "default",
  };
  const text = JSON.stringify(payload, null, 2);
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(text);
    addMessage("aiden", "Copied runtime JSON to clipboard.");
    setLastCopied("runtime JSON");
    return;
  }
  addMessage("aiden", "Clipboard API unavailable. Runtime JSON:\n" + text);
}

async function copyProfileName() {
  const profileName = runtimeProfileValue?.textContent || "default";
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(profileName);
    addMessage("aiden", "Copied active profile name to clipboard.");
    setLastCopied("profile name");
    return;
  }
  addMessage("aiden", "Clipboard API unavailable. Active profile: " + profileName);
}

function buildDebugSnapshot() {
  const taskItems = Array.from(taskList?.querySelectorAll(".task-item") || []);
  const doneTasks = taskItems.filter((item) => item.classList.contains("done")).length;
  const pendingTasks = taskItems.length - doneTasks;

  const memoryItems = Array.from(memoryList?.querySelectorAll("li") || []);
  const emptyMemory = memoryItems.length === 1 && memoryItems[0].textContent === "No memory notes yet.";
  const memoryCount = emptyMemory ? 0 : memoryItems.length;

  return {
    captured_at: new Date().toISOString(),
    runtime: currentRuntime,
    ui: {
      mode: modeInput?.value || "",
      name: nameInput?.value || "",
      short_responses: !!shortInput?.checked,
      learning_style: learningStyleInput?.value || "",
      focus_goal: focusGoalInput?.value || "",
      interests: interestsInput?.value || "",
      active_profile: runtimeProfileValue?.textContent || profileSelect?.value || "default",
      profile_count: profileSelect?.options?.length || 0,
    },
    counts: {
      tasks_total: taskItems.length,
      tasks_done: doneTasks,
      tasks_pending: pendingTasks,
      memory_notes: memoryCount,
    },
    environment: {
      user_agent: navigator.userAgent,
      language: navigator.language,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    },
  };
}

async function copyDebugSnapshot() {
  const snapshot = buildDebugSnapshot();
  const text = JSON.stringify(snapshot, null, 2);
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(text);
    addMessage("aiden", "Copied full debug snapshot to clipboard.");
    setLastCopied("debug snapshot");
    return;
  }
  addMessage("aiden", "Clipboard API unavailable. Debug snapshot:\n" + text);
}

function setLastCopied(label) {
  if (!lastCopiedAt) return;
  if (_copiedClearTimer) clearTimeout(_copiedClearTimer);
  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  lastCopiedAt.textContent = `${label} \u00b7 ${time}`;
  lastCopiedAt.classList.add("visible");
  _copiedClearTimer = setTimeout(() => {
    lastCopiedAt.classList.remove("visible");
    _copiedClearTimer = null;
  }, 4000);
}

function setTaskCache(tasks) {
  cachedTasks = Array.isArray(tasks) ? tasks : [];
  syncFilterCounts();
  syncOverdueBadge();
  applyTaskView();
}

function syncFilterCounts() {
  const total = cachedTasks.length;
  const done = cachedTasks.filter((t) => t.done).length;
  const pending = total - done;
  if (filterAllBtn) filterAllBtn.textContent = `All (${total})`;
  if (filterPendingBtn) filterPendingBtn.textContent = `Pending (${pending})`;
  if (filterDoneBtn) filterDoneBtn.textContent = `Done (${done})`;
}

function syncOverdueBadge() {
  if (!overdueBadge) return;
  const today = getLocalDateStamp();
  const overdue = cachedTasks.filter((t) => !t.done && t.due_date && t.due_date < today).length;
  if (overdue > 0) {
    overdueBadge.textContent = overdue + (overdue === 1 ? " overdue" : " overdue");
    overdueBadge.classList.remove("hidden");
  } else {
    overdueBadge.classList.add("hidden");
  }
}

function applyTaskView() {
  const sortBy = taskSortSelect?.value || "added";
  const priorityOrder = { high: 0, medium: 1, low: 2 };

  let list = cachedTasks.slice();

  if (taskFilterMode === "pending") list = list.filter((t) => !t.done);
  else if (taskFilterMode === "done") list = list.filter((t) => t.done);

  if (sortBy === "due") {
    list.sort((a, b) => {
      if (!a.due_date && !b.due_date) return 0;
      if (!a.due_date) return 1;
      if (!b.due_date) return -1;
      return a.due_date.localeCompare(b.due_date);
    });
  } else if (sortBy === "priority") {
    list.sort((a, b) => {
      const pa = priorityOrder[(a.priority || "medium").toLowerCase()] ?? 1;
      const pb = priorityOrder[(b.priority || "medium").toLowerCase()] ?? 1;
      return pa - pb;
    });
  }
  // "added" keeps original server order

  renderTasks(list);
}

function renderTasks(tasks) {
  taskList.innerHTML = "";
  if (!Array.isArray(tasks) || tasks.length === 0) {
    const empty = document.createElement("li");
    empty.textContent = "No tasks yet.";
    empty.style.color = "#4a5f7a";
    taskList.appendChild(empty);
    return;
  }

  const today = getLocalDateStamp();

  for (const task of tasks) {
    const item = document.createElement("li");
    const priority = (task.priority || "medium").toLowerCase();
    item.className = `task-item p-${priority} ${task.done ? "done" : ""}`;
    if (!task.done && task.due_date && task.due_date < today) {
      item.classList.add("overdue");
    }

    const summary = document.createElement("div");

    const text = document.createElement("div");
    text.textContent = `[${task.id}] ${task.text}`;

    const meta = document.createElement("span");
    meta.className = "task-meta";
    const due = task.due_date || "none";
    meta.textContent = `priority: ${priority} | due: ${due}`;
    summary.appendChild(text);
    summary.appendChild(meta);

    const doneBtn = document.createElement("button");
    doneBtn.type = "button";
    doneBtn.textContent = "Done";
    doneBtn.disabled = !!task.done;
    doneBtn.addEventListener("click", () => markTaskDone(task.id));

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "Remove";
    removeBtn.className = "danger";
    removeBtn.addEventListener("click", () => removeTask(task.id));

    const editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.textContent = "Edit";
    editBtn.addEventListener("click", () => loadTaskIntoEditor(task));

    item.appendChild(summary);
    item.appendChild(doneBtn);
    item.appendChild(editBtn);
    item.appendChild(removeBtn);
    taskList.appendChild(item);
  }
}

function fuzzyHighlight(text, query) {
  if (!query || !text) return text;
  const queryLower = query.toLowerCase();
  const textLower = text.toLowerCase();
  let out = "";
  let queryIdx = 0;
  for (let i = 0; i < text.length; i++) {
    if (queryIdx < queryLower.length && textLower[i] === queryLower[queryIdx]) {
      out += `<mark>${text[i]}</mark>`;
      queryIdx++;
    } else {
      out += text[i];
    }
  }
  return out;
}

function updateAutocomplete() {
  const val = messageInput.value;
  const lastWordMatch = val.match(/[\w:]*$/);
  const lastWord = (lastWordMatch ? lastWordMatch[0] : "").toLowerCase();

  if (!lastWord || lastWord.length === 0) {
    autocompleteList.classList.add("hidden");
    autocompleteIndex = -1;
    return;
  }

  const matches = AUTOCOMPLETE_PREFIXES.filter((item) =>
    item.prefix.toLowerCase().startsWith(lastWord)
  );

  if (matches.length === 0) {
    autocompleteList.classList.add("hidden");
    autocompleteIndex = -1;
    return;
  }

  autocompleteList.innerHTML = "";
  matches.forEach((item, idx) => {
    const li = document.createElement("li");
    li.className = "autocomplete-item";
    li.textContent = item.prefix + " — " + item.desc;
    li.dataset.prefix = item.prefix;
    li.addEventListener("click", () => insertAutocomplete(item.prefix));
    autocompleteList.appendChild(li);
  });
  autocompleteList.classList.remove("hidden");
  autocompleteIndex = -1;
  highlightAutocompleteItem(0);
}

function insertAutocomplete(prefix) {
  const val = messageInput.value;
  const lastWordMatch = val.match(/[\w:]*$/);
  const lastWord = lastWordMatch ? lastWordMatch[0] : "";
  const beforeWord = val.slice(0, val.length - lastWord.length);
  messageInput.value = beforeWord + prefix;
  messageInput.focus();
  autocompleteList.classList.add("hidden");
  autocompleteIndex = -1;
}

function highlightAutocompleteItem(idx) {
  const items = autocompleteList.querySelectorAll(".autocomplete-item");
  items.forEach((item) => item.classList.remove("highlighted"));
  if (idx >= 0 && idx < items.length) {
    items[idx].classList.add("highlighted");
    items[idx].scrollIntoView({ block: "nearest" });
  }
}

messageInput?.addEventListener("input", updateAutocomplete);
messageInput?.addEventListener("keydown", (event) => {
  if (autocompleteList.classList.contains("hidden")) return;
  const items = autocompleteList.querySelectorAll(".autocomplete-item");
  const count = items.length;

  if (event.key === "ArrowDown") {
    event.preventDefault();
    autocompleteIndex = (autocompleteIndex + 1) % count;
    highlightAutocompleteItem(autocompleteIndex);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    autocompleteIndex = (autocompleteIndex - 1 + count) % count;
    highlightAutocompleteItem(autocompleteIndex);
  } else if (event.key === "Enter" && autocompleteIndex >= 0) {
    event.preventDefault();
    const selected = items[autocompleteIndex]?.dataset.prefix;
    if (selected) insertAutocomplete(selected);
  } else if (event.key === "Escape") {
    event.preventDefault();
    autocompleteList.classList.add("hidden");
    autocompleteIndex = -1;
  }
});

function renderMemorySearchResults(results, query = "") {
  memorySearchResults.innerHTML = "";
  if (!Array.isArray(results) || results.length === 0) {
    const empty = document.createElement("li");
    empty.textContent = "No memory matches.";
    memorySearchResults.appendChild(empty);
    return;
  }
  for (const note of results) {
    const item = document.createElement("li");
    item.innerHTML = fuzzyHighlight(note, query);
    memorySearchResults.appendChild(item);
  }
}

function loadTaskIntoEditor(task) {
  taskEditIdInput.value = String(task.id);
  taskInput.value = task.text || "";
  taskDueDateInput.value = task.due_date || "";
  taskPriorityInput.value = task.priority || "medium";
}

function renderMemoryNotes(notes) {
  memoryList.innerHTML = "";
  if (!Array.isArray(notes) || notes.length === 0) {
    const empty = document.createElement("li");
    empty.textContent = "No memory notes yet.";
    memoryList.appendChild(empty);
    return;
  }

  for (const note of notes) {
    const item = document.createElement("li");
    item.textContent = note;
    memoryList.appendChild(item);
  }
}

async function fetchState() {
  const response = await fetch("/api/state");
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not load state");
  }
  syncPrefs(data.prefs);
  syncProfiles(data.profiles, data.prefs?.active_profile);
  syncRuntime(data.runtime);
  setTaskCache(data.tasks);
  renderMemoryNotes(data.memory_notes || []);
}

async function createProfile() {
  const name = newProfileNameInput.value.trim();
  if (!name) {
    addMessage("aiden", "Enter a profile name first.");
    return;
  }

  const response = await fetch("/api/profiles/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not create profile");
  }

  newProfileNameInput.value = "";
  syncPrefs(data.prefs);
  syncProfiles(data.profiles, data.prefs?.active_profile);
  addMessage("aiden", data.message || "Profile created.");
}

async function exportActiveProfile() {
  const response = await fetch("/api/profiles/export", { method: "POST" });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not export profile");
  }
  profileJsonInput.value = JSON.stringify(data.payload, null, 2);
  addMessage("aiden", `Profile export ready: ${data.path}`);
}

async function importProfile() {
  const raw = profileJsonInput.value.trim();
  if (!raw) {
    addMessage("aiden", "Paste a profile JSON payload first.");
    return;
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (_error) {
    throw new Error("Invalid JSON in profile import field");
  }
  const response = await fetch("/api/profiles/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      profile_name: parsed.profile_name,
      profile_data: parsed.profile,
    }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not import profile");
  }
  syncPrefs(data.prefs);
  syncProfiles(data.profiles, data.prefs?.active_profile);
  setTaskCache(data.tasks || []);
  renderMemoryNotes(data.memory_notes || []);
  addMessage("aiden", data.message || "Profile imported.");
}

async function switchProfile() {
  const name = profileSelect.value;
  if (!name) {
    addMessage("aiden", "Choose a profile first.");
    return;
  }

  const response = await fetch("/api/profiles/switch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not switch profile");
  }

  syncPrefs(data.prefs);
  syncProfiles(data.profiles, data.prefs?.active_profile);
  setTaskCache(data.tasks || []);
  renderMemoryNotes(data.memory_notes || []);
  addMessage("aiden", data.message || "Profile switched.");
}

async function deleteProfile() {
  const name = profileSelect.value;
  if (!name) {
    addMessage("aiden", "Choose a profile first.");
    return;
  }

  const response = await fetch("/api/profiles/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not delete profile");
  }

  syncPrefs(data.prefs);
  syncProfiles(data.profiles, data.prefs?.active_profile);
  setTaskCache(data.tasks || []);
  renderMemoryNotes(data.memory_notes || []);
  addMessage("aiden", data.message || "Profile deleted.");
}

async function addTask() {
  const text = taskInput.value.trim();
  if (!text) {
    return;
  }

  const response = await fetch("/api/tasks/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      due_date: taskDueDateInput.value,
      priority: taskPriorityInput.value,
    }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not add task");
  }

  taskInput.value = "";
  taskDueDateInput.value = "";
  taskPriorityInput.value = "medium";
  setTaskCache(data.tasks || []);
}

async function markTaskDone(taskId) {
  const response = await fetch("/api/tasks/done", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_id: taskId }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not mark task done");
  }
  setTaskCache(data.tasks || []);
}

async function editTask(taskId) {
  const response = await fetch("/api/tasks/edit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      task_id: taskId,
      text: taskInput.value,
      due_date: taskDueDateInput.value,
      priority: taskPriorityInput.value,
    }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not edit task");
  }
  setTaskCache(data.tasks || []);
}

async function postponeTask(taskId, days = 1) {
  const response = await fetch("/api/tasks/postpone", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_id: taskId, days }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not postpone task");
  }
  setTaskCache(data.tasks || []);
}

async function removeTask(taskId) {
  const response = await fetch("/api/tasks/remove", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_id: taskId }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not remove task");
  }
  setTaskCache(data.tasks || []);
}

async function clearTasks() {
  const response = await fetch("/api/tasks/clear", { method: "POST" });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not clear tasks");
  }
  setTaskCache(data.tasks || []);
}

async function addMemoryNote() {
  const note = memoryInput.value.trim();
  if (!note) {
    return;
  }

  const response = await fetch("/api/memory/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not save memory note");
  }
  memoryInput.value = "";
  renderMemoryNotes(data.memory_notes || []);
}

async function clearMemoryNotes() {
  const response = await fetch("/api/memory/clear", { method: "POST" });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not clear memory notes");
  }
  renderMemoryNotes(data.memory_notes || []);
}

async function searchMemoryNotes() {
  const query = memorySearchInput.value.trim();
  if (!query) {
    renderMemorySearchResults([]);
    return;
  }
  const response = await fetch("/api/memory/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not search memory");
  }
  renderMemorySearchResults(data.results || [], query);
}

addMessage("aiden", "Hello. I am Aiden - The Smart AI Companion. Ask me anything.");

resetBtn.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/reset", { method: "POST" });
    const data = await response.json();
    if (!response.ok) {
      addMessage("aiden", `Error: ${data.error || "Could not reset chat."}`);
      return;
    }
    chat.innerHTML = "";
    addMessage("aiden", data.message || "Conversation context reset.");
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

function exportChat() {
  const messages = [];
  const msgElements = chat.querySelectorAll(".msg");
  
  msgElements.forEach((el) => {
    const role = el.classList.contains("user") ? "user" : "aiden";
    const bubble = el.querySelector(".bubble");
    const time = el.querySelector(".msg-time");
    const text = bubble?.textContent || "";
    const timestamp = time?.title || new Date().toISOString();
    
    messages.push({
      role,
      text,
      timestamp,
      relative_time: time?.textContent || "now",
    });
  });

  const payload = {
    exported_at: new Date().toISOString(),
    message_count: messages.length,
    messages,
  };

  const json = JSON.stringify(payload, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const now = new Date();
  const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}_${String(now.getHours()).padStart(2, "0")}-${String(now.getMinutes()).padStart(2, "0")}`;
  a.download = `aiden_chat_${dateStr}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  addMessage("aiden", `Chat exported to aiden_chat_${dateStr}.json`);
}

exportBtn.addEventListener("click", async () => {
  try {
    exportChat();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

createProfileBtn.addEventListener("click", async () => {
  try {
    await createProfile();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

switchProfileBtn.addEventListener("click", async () => {
  try {
    await switchProfile();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

deleteProfileBtn.addEventListener("click", async () => {
  try {
    await deleteProfile();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

exportProfileBtn.addEventListener("click", async () => {
  try {
    await exportActiveProfile();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

importProfileBtn.addEventListener("click", async () => {
  try {
    await importProfile();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

addTaskBtn.addEventListener("click", async () => {
  try {
    await addTask();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

editTaskBtn.addEventListener("click", async () => {
  try {
    const taskId = Number(taskEditIdInput.value);
    if (!taskId) {
      addMessage("aiden", "Choose a task ID to edit.");
      return;
    }
    await editTask(taskId);
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

postponeTaskBtn.addEventListener("click", async () => {
  try {
    const taskId = Number(taskEditIdInput.value);
    if (!taskId) {
      addMessage("aiden", "Choose a task ID to postpone.");
      return;
    }
    await postponeTask(taskId, 1);
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

clearTasksBtn.addEventListener("click", async () => {
  try {
    await clearTasks();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

addMemoryBtn.addEventListener("click", async () => {
  try {
    await addMemoryNote();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

clearMemoryBtn.addEventListener("click", async () => {
  try {
    await clearMemoryNotes();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

memoryInput.addEventListener("keydown", async (event) => {
  if (event.key !== "Enter") {
    return;
  }
  event.preventDefault();
  try {
    await addMemoryNote();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

searchMemoryBtn.addEventListener("click", async () => {
  try {
    await searchMemoryNotes();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

copyEnvBtn?.addEventListener("click", async () => {
  try {
    await copyEnvSetup();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

runtimeInfoBtn?.addEventListener("click", () => {
  if (!runtimeInfoPanel) {
    return;
  }
  const isHidden = runtimeInfoPanel.classList.toggle("hidden");
  runtimeInfoBtn.setAttribute("aria-expanded", String(!isHidden));
});

copyRuntimeBtn?.addEventListener("click", async () => {
  try {
    await copyRuntimeJson();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

copyProfileBtn?.addEventListener("click", async () => {
  try {
    await copyProfileName();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

copyDebugBtn?.addEventListener("click", async () => {
  try {
    await copyDebugSnapshot();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

function setFilterActive(btn) {
  [filterAllBtn, filterPendingBtn, filterDoneBtn].forEach((b) => b?.classList.remove("active"));
  btn?.classList.add("active");
}

filterAllBtn?.addEventListener("click", () => {
  taskFilterMode = "all";
  setFilterActive(filterAllBtn);
  applyTaskView();
});

filterPendingBtn?.addEventListener("click", () => {
  taskFilterMode = "pending";
  setFilterActive(filterPendingBtn);
  applyTaskView();
});

filterDoneBtn?.addEventListener("click", () => {
  taskFilterMode = "done";
  setFilterActive(filterDoneBtn);
  applyTaskView();
});

taskSortSelect?.addEventListener("change", () => applyTaskView());

memorySearchInput.addEventListener("keydown", async (event) => {
  if (event.key !== "Enter") {
    return;
  }
  event.preventDefault();
  try {
    await searchMemoryNotes();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

taskInput.addEventListener("keydown", async (event) => {
  if (event.key !== "Enter") {
    return;
  }
  event.preventDefault();
  try {
    await addTask();
  } catch (error) {
    addMessage("aiden", `Error: ${error}`);
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const text = messageInput.value.trim();
  if (!text) {
    return;
  }

  addMessage("user", text);
  messageInput.value = "";
  setStreamingUiState(true);
  typingIndicator?.classList.remove("hidden");

  try {
    activeChatAbortController = new AbortController();
    const data = await streamChatReplyWithRetry(text, activeChatAbortController.signal);
    typingIndicator?.classList.add("hidden");
    if (!data) {
      return;
    }

    syncPrefs(data.prefs || {});
    syncRuntime(data.runtime || null);

    if (data.meta && data.meta.type === "exit") {
      addMessage("aiden", "Session closed command received. Refresh to continue.");
    }

    if (data.meta && data.meta.type === "profile") {
      await fetchState();
    }

    if (data.meta && data.meta.type === "task") {
      await fetchState();
    }
  } catch (error) {
    typingIndicator?.classList.add("hidden");
    if (error && error.name === "AbortError") {
      addMessage("aiden", "Streaming stopped.");
    } else {
      try {
        const fallback = await fetchChatFallback(text);
        addMessage("aiden", "Streaming unavailable, switched to standard response mode.");
        syncPrefs(fallback.prefs || {});
        syncRuntime(fallback.runtime || null);
        addMessage("aiden", fallback.answer || "I do not have a response right now.");

        if (fallback.meta && fallback.meta.type === "profile") {
          await fetchState();
        }
        if (fallback.meta && fallback.meta.type === "task") {
          await fetchState();
        }
      } catch (fallbackError) {
        addMessage("aiden", `Error: ${fallbackError}`);
      }
    }
  } finally {
    activeChatAbortController = null;
    setStreamingUiState(false);
    messageInput.focus();
  }
});

stopStreamingBtn?.addEventListener("click", () => {
  if (activeChatAbortController) {
    activeChatAbortController.abort();
  }
});

document.addEventListener("keydown", async (event) => {
  const ctrl = event.ctrlKey || event.metaKey;
  if (!ctrl) return;

  if (event.shiftKey && event.key === "D") {
    event.preventDefault();
    try { await copyDebugSnapshot(); } catch (e) { addMessage("aiden", `Error: ${e}`); }
    return;
  }

  if (event.shiftKey && event.key === "R") {
    event.preventDefault();
    try { await copyRuntimeJson(); } catch (e) { addMessage("aiden", `Error: ${e}`); }
    return;
  }

  if (!event.shiftKey && event.key === "/") {
    event.preventDefault();
    messageInput?.focus();
    return;
  }
});

settingsBtn?.addEventListener("click", () => {
  if (!settingsPanel) return;
  const isHidden = settingsPanel.classList.toggle("hidden");
  settingsBtn.setAttribute("aria-expanded", String(!isHidden));
  if (!isHidden) {
    const settings = loadSettings();
    darkModeToggle.checked = settings.darkMode;
    fontSizeSlider.value = settings.fontSize;
    fontSizeValue.textContent = settings.fontSize + "px";
    compactModeToggle.checked = settings.compactMode;
    soundToggle.checked = settings.soundEnabled;
  }
});

statsBtn?.addEventListener("click", () => {
  if (!statsPanel) return;
  const isHidden = statsPanel.classList.toggle("hidden");
  statsBtn.setAttribute("aria-expanded", String(!isHidden));
  if (!isHidden) {
    calculateStatistics();
  }
});

bookmarksBtn?.addEventListener("click", () => {
  if (!bookmarksPanel) return;
  const isHidden = bookmarksPanel.classList.toggle("hidden");
  bookmarksBtn.setAttribute("aria-expanded", String(!isHidden));
  if (!isHidden) {
    renderBookmarks();
  }
});

themeSelect?.addEventListener("change", (e) => {
  setTheme(e.target.value);
});

conversationTag?.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    addConversationTag(conversationTag.value);
    conversationTag.value = "";
  }
});

darkModeToggle?.addEventListener("change", () => {
  const settings = loadSettings();
  settings.darkMode = darkModeToggle.checked;
  saveSettings(settings);
});

fontSizeSlider?.addEventListener("input", () => {
  fontSizeValue.textContent = fontSizeSlider.value + "px";
  const settings = loadSettings();
  settings.fontSize = Number(fontSizeSlider.value);
  saveSettings(settings);
});

compactModeToggle?.addEventListener("change", () => {
  const settings = loadSettings();
  settings.compactMode = compactModeToggle.checked;
  saveSettings(settings);
});

soundToggle?.addEventListener("change", () => {
  const settings = loadSettings();
  settings.soundEnabled = soundToggle.checked;
  saveSettings(settings);
  if (settings.soundEnabled) {
    playNotificationSound();
  }
});

resetSettingsBtn?.addEventListener("click", () => {
  saveSettings(DEFAULT_SETTINGS);
  darkModeToggle.checked = DEFAULT_SETTINGS.darkMode;
  fontSizeSlider.value = DEFAULT_SETTINGS.fontSize;
  fontSizeValue.textContent = DEFAULT_SETTINGS.fontSize + "px";
  compactModeToggle.checked = DEFAULT_SETTINGS.compactMode;
  soundToggle.checked = DEFAULT_SETTINGS.soundEnabled;
  addMessage("aiden", "Settings reset to defaults.");
});

chatSearchInput?.addEventListener("input", (event) => {
  const query = event.target.value.trim();
  searchChatMessages(query);
});

chatSearchPrevBtn?.addEventListener("click", () => {
  if (chatSearchMatches.length === 0) return;
  let nextIndex = chatSearchCurrentIndex - 1;
  if (nextIndex < 0) {
    nextIndex = chatSearchMatches.length - 1;
  }
  goToChatSearchMatch(nextIndex);
});

chatSearchNextBtn?.addEventListener("click", () => {
  if (chatSearchMatches.length === 0) return;
  let nextIndex = chatSearchCurrentIndex + 1;
  if (nextIndex >= chatSearchMatches.length) {
    nextIndex = 0;
  }
  goToChatSearchMatch(nextIndex);
});

chatSearchClearBtn?.addEventListener("click", () => {
  chatSearchInput.value = "";
  clearChatSearch();
});

chatSearchInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    chatSearchNextBtn?.click();
  }
});

contextCopyText?.addEventListener("click", copyMessageText);
contextCopyFull?.addEventListener("click", copyMessageFull);
contextDelete?.addEventListener("click", deleteMessage);
contextPin?.addEventListener("click", togglePinnedMessage);

document.addEventListener("click", (event) => {
  if (!messageContextMenu.contains(event.target) && !chat.contains(event.target)) {
    hideMessageContextMenu();
  }
});

document.addEventListener("scroll", hideMessageContextMenu);

toggleConversationListBtn?.addEventListener("click", () => {
  const isHidden = conversationList.classList.toggle("hidden");
});

newConversationBtn?.addEventListener("click", () => {
  const name = prompt("Enter name for new conversation:", "Conversation " + (Object.keys(conversations).length + 1));
  if (name) {
    createNewConversation(name);
    conversationList.classList.add("hidden");
    addMessage("aiden", `Created new conversation: ${name}`);
  }
});

renameConversationBtn?.addEventListener("click", renameConversation);

deleteConversationBtn?.addEventListener("click", () => {
  if (currentConversationId) {
    deleteConversation(currentConversationId);
  }
});

const initialSettings = loadSettings();
applySettings(initialSettings);
if (initialSettings.soundEnabled) {
  soundToggle.checked = true;
}

loadConversations();
updateConversationUI();
if (currentConversationId) {
  switchConversation(currentConversationId);
}
calculateStatistics();

// Load theme and bookmarks
const savedTheme = localStorage.getItem("selectedTheme") || "dark";
setTheme(savedTheme);
if (bookmarksBtn) bookmarksBtn.textContent = `📌 Bookmarks (${bookmarkedMessages.length})`;
if (currentConversationId) {
  renderConversationTags();
}

fetchState().catch((error) => {
  addMessage("aiden", `Error: ${error}`);
});
