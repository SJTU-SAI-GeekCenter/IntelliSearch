/**
 * Chat management functionality
 * @fileoverview Chat operations, message handling, and conversation logic
 */

import {appState} from './config.js';
import {loadChats, saveChats} from './storage.js';
import {escapeHtml, generateRandomId, renderMarkdown} from './utils.js';

/**
 * Create a new chat session
 * @param {string} name - Name for the new chat
 * @returns {Object} New chat object
 */
export function createChat(name = 'New Chat') {
  const chat = {
    id: generateRandomId(),
    name: name.trim() || 'Untitled Chat',
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };

  appState.chats.unshift(chat);
  saveChats();
  return chat;
}

/**
 * Select and switch to a specific chat
 * @param {string} chatId - ID of chat to select
 */
export function selectChat(chatId) {
  const chat = appState.chats.find(c => c.id === chatId);
  if (chat) {
    appState.currentChatId = chatId;
    chat.updatedAt = new Date().toISOString();
    saveChats();
    return true;
  }
  return false;
}

/**
 * Get the currently active chat
 * @returns {Object|null} Current chat object or null
 */
export function getCurrentChat() {
  return appState.chats.find(chat => chat.id === appState.currentChatId) ||
      null;
}

/**
 * Add a message to the current chat
 * @param {string} role - Message role ('user' | 'assistant' | 'system')
 * @param {string} content - Message content
 * @returns {Object|null} The message object or null if no current chat
 */
export function addMessage(role, content) {
  const chat = getCurrentChat();
  if (!chat) return null;

  const message = {
    role,
    content: content.trim(),
    timestamp: new Date().toISOString(),
    id: generateRandomId()
  };

  chat.messages.push(message);
  chat.updatedAt = new Date().toISOString();
  saveChats();

  return message;
}

/**
 * Update an existing message
 * @param {string} messageId - ID of message to update
 * @param {string} content - New content for the message
 * @returns {boolean} Success status
 */
export function updateMessage(messageId, content) {
  const chat = getCurrentChat();
  if (!chat) return false;

  const message = chat.messages.find(m => m.id === messageId);
  if (message) {
    message.content = content.trim();
    message.edited = true;
    message.updatedAt = new Date().toISOString();
    chat.updatedAt = new Date().toISOString();
    saveChats();
    return true;
  }

  return false;
}

/**
 * Delete a message from the current chat
 * @param {string} messageId - ID of message to delete
 * @returns {boolean} Success status
 */
export function deleteMessage(messageId) {
  const chat = getCurrentChat();
  if (!chat) return false;

  const messageIndex = chat.messages.findIndex(m => m.id === messageId);
  if (messageIndex !== -1) {
    chat.messages.splice(messageIndex, 1);
    chat.updatedAt = new Date().toISOString();
    saveChats();
    return true;
  }

  return false;
}

/**
 * Rename a chat
 * @param {string} chatId - ID of chat to rename
 * @param {string} newName - New name for the chat
 * @returns {boolean} Success status
 */
export function renameChat(chatId, newName) {
  const chat = appState.chats.find(c => c.id === chatId);
  if (chat) {
    chat.name = newName.trim() || 'Untitled Chat';
    chat.updatedAt = new Date().toISOString();
    saveChats();
    return true;
  }
  return false;
}

/**
 * Delete a chat completely
 * @param {string} chatId - ID of chat to delete
 * @returns {boolean} Success status
 */
export function deleteChat(chatId) {
  const chatIndex = appState.chats.findIndex(c => c.id === chatId);
  if (chatIndex !== -1) {
    appState.chats.splice(chatIndex, 1);

    // If deleting current chat, switch to another one
    if (appState.currentChatId === chatId) {
      if (appState.chats.length > 0) {
        appState.currentChatId = appState.chats[0].id;
      } else {
        // Create a new chat if all were deleted
        const newChat = createChat('New Chat');
        appState.currentChatId = newChat.id;
      }
    }

    saveChats();
    return true;
  }

  return false;
}

/**
 * Clear all chat history
 */
export function clearAllHistory() {
  appState.chats = [];
  const newChat = createChat('New Chat');
  appState.currentChatId = newChat.id;
  saveChats();
}

/**
 * Get chat statistics
 * @returns {Object} Chat statistics
 */
export function getChatStats() {
  const totalMessages =
      appState.chats.reduce((sum, chat) => sum + chat.messages.length, 0);
  const totalWords = appState.chats.reduce((sum, chat) => {
    return sum + chat.messages.reduce((wordSum, message) => {
      return wordSum + (message.content.split(/\s+/).length || 0);
    }, 0);
  }, 0);

  return {
    chatCount: appState.chats.length,
    totalMessages,
    totalWords,
    averageMessagesPerChat: appState.chats.length > 0 ?
        Math.round(totalMessages / appState.chats.length) :
        0,
    lastActivity: appState.chats.length > 0 ?
        Math.max(
            ...appState.chats.map(chat => new Date(chat.updatedAt).getTime())) :
        null
  };
}

/**
 * Search messages across all chats
 * @param {string} query - Search query
 * @returns {Array} Array of matching message objects with chat context
 */
export function searchMessages(query) {
  const results = [];
  const searchTerm = query.toLowerCase().trim();

  if (!searchTerm) return results;

  appState.chats.forEach(chat => {
    chat.messages.forEach((message, index) => {
      if (message.content.toLowerCase().includes(searchTerm)) {
        results.push({
          ...message,
          chatId: chat.id,
          chatName: chat.name,
          messageIndex: index,
          snippet: getMessageSnippet(message.content, searchTerm)
        });
      }
    });
  });

  return results;
}

/**
 * Get a snippet of message content around the search term
 * @param {string} content - Full message content
 * @param {string} searchTerm - Term to highlight
 * @param {number} contextLength - Length of context around term
 * @returns {string} Snippet with highlighted term
 */
function getMessageSnippet(content, searchTerm, contextLength = 50) {
  const index = content.toLowerCase().indexOf(searchTerm.toLowerCase());
  if (index === -1) return content.substring(0, 100);

  const start = Math.max(0, index - contextLength);
  const end =
      Math.min(content.length, index + searchTerm.length + contextLength);

  let snippet = content.substring(start, end);
  if (start > 0) snippet = '...' + snippet;
  if (end < content.length) snippet = snippet + '...';

  // Highlight the search term
  const regex = new RegExp(`(${searchTerm})`, 'gi');
  snippet = snippet.replace(regex, '<mark>$1</mark>');

  return snippet;
}

/**
 * Initialize chat system by loading saved data
 */
export function initializeChat() {
  appState.chats = loadChats();

  if (appState.chats.length === 0) {
    const newChat = createChat('Untitled Chat');
    appState.currentChatId = newChat.id;
  } else {
    appState.currentChatId = appState.chats[0].id;
  }
}