/**
 * Main application entry point
 * @fileoverview Application initialization and coordination
 */

import {initializeAnimations} from './animations.js';
import {addMessage, clearAllHistory, createChat, deleteChat, getCurrentChat, initializeChat, renameChat, selectChat} from './chat.js';
import {appState} from './config.js';
import {getStorageUsage, loadSettings, saveSettings} from './storage.js';
import {appendMessageUI, initializeUI, renderHistory, renderMessages, setThinkingState, showToast, toggleSettingsPanel, updateAssistantMessage, updateChatTitle} from './ui.js';
import {isSupported} from './utils.js';
import {sendMessageToAPI, checkAPIConnection, getAvailableTools, setSessionId, getCurrentSessionId} from './api.js';

/**
 * Initialize the application
 */
async function initializeApp() {
  try {
    // Initialize core systems
    initializeChat();
    initializeSettings();
    initializeAnimations();
    initializeUI();

    // Setup event listeners
    setupEventListeners();

    // Initial render
    renderHistory();
    renderMessages();

    // Check API connection
    await checkAPIStatus();

    console.log('AI Chat Application initialized successfully');
  } catch (error) {
    console.error('Failed to initialize application:', error);
    showToast('Failed to initialize application', 5000);
  }
}

/**
 * Initialize application settings
 */
function initializeSettings() {
  const settings = loadSettings();
  appState.updateSettings(settings);
  applySettings();
}

/**
 * Apply settings to the UI
 */
function applySettings() {
  const {settings} = appState;

  // Apply font size
  if (settings.fontSize) {
    document.documentElement.style.setProperty(
        '--base-font-size', settings.fontSize + 'px');
    updateFontSizeControl(settings.fontSize);
  }

  // Apply other settings
  updateSettingsControls(settings);
}

/**
 * Update font size control elements
 * @param {number} fontSize - Font size value
 */
function updateFontSizeControl(fontSize) {
  const fontSizeSlider = document.getElementById('font-size-slider');
  const fontSizeValue = document.getElementById('font-size-value');

  if (fontSizeSlider) fontSizeSlider.value = fontSize;
  if (fontSizeValue) fontSizeValue.textContent = fontSize + 'px';
}

/**
 * Update settings controls
 * @param {Object} settings - Settings object
 */
function updateSettingsControls(settings) {
  // Response speed
  const responseSpeedSelect = document.getElementById('response-speed');
  if (responseSpeedSelect && settings.responseSpeed) {
    responseSpeedSelect.value = settings.responseSpeed;
  }

  // Typewriter effect
  const typewriterToggle = document.getElementById('typewriter-toggle');
  if (typewriterToggle && settings.typewriter !== undefined) {
    typewriterToggle.checked = settings.typewriter;
  }

  // Sound effects
  const soundToggle = document.getElementById('sound-toggle');
  if (soundToggle && settings.sound !== undefined) {
    soundToggle.checked = settings.sound;
  }

  // Auto-save
  const autoSaveToggle = document.getElementById('auto-save-toggle');
  if (autoSaveToggle && settings.autoSave !== undefined) {
    autoSaveToggle.checked = settings.autoSave;
  }
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
  setupChatEventListeners();
  setupSettingsEventListeners();
  setupActionEventListeners();
  setupKeyboardShortcuts();
}

/**
 * Setup chat-related event listeners
 */
function setupChatEventListeners() {
  // Send message button
  const sendBtn = document.getElementById('send');
  if (sendBtn) {
    sendBtn.addEventListener('click', sendMessage);
  }

  // Message input
  const promptEl = document.getElementById('prompt');
  if (promptEl) {
    promptEl.addEventListener('keydown', handlePromptKeydown);
  }

  // New chat button
  const newChatBtn = document.getElementById('new-chat');
  if (newChatBtn) {
    newChatBtn.addEventListener('click', handleNewChat);
  }

  // Rename chat button
  const renameBtn = document.getElementById('rename-chat');
  if (renameBtn) {
    renameBtn.addEventListener('click', handleRenameChat);
  }

  // Delete chat button
  const deleteBtn = document.getElementById('delete-chat');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', handleDeleteChat);
  }

  // History list clicks
  const historyList = document.getElementById('history-list');
  if (historyList) {
    historyList.addEventListener('click', handleHistoryClick);
  }
}

/**
 * Setup settings-related event listeners
 */
function setupSettingsEventListeners() {
  // Settings button
  const settingsBtn = document.getElementById('settings-btn');
  if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
      toggleSettingsPanel(true);
      updateStorageInfo();
    });
  }

  // Close settings button
  const closeSettingsBtn = document.getElementById('close-settings');
  if (closeSettingsBtn) {
    closeSettingsBtn.addEventListener('click', () => {
      toggleSettingsPanel(false);
    });
  }

  // Settings overlay click
  const settingsPanel = document.getElementById('settings-panel');
  if (settingsPanel) {
    settingsPanel.addEventListener('click', (e) => {
      if (e.target === settingsPanel) {
        toggleSettingsPanel(false);
      }
    });
  }

  // Font size slider
  const fontSizeSlider = document.getElementById('font-size-slider');
  const fontSizeValue = document.getElementById('font-size-value');
  if (fontSizeSlider && fontSizeValue) {
    fontSizeSlider.addEventListener('input', (e) => {
      const value = e.target.value;
      fontSizeValue.textContent = value + 'px';
      document.documentElement.style.setProperty(
          '--base-font-size', value + 'px');
    });
  }

  // Save settings button
  const saveSettingsBtn = document.getElementById('save-settings');
  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('click', handleSaveSettings);
  }

  // Reset settings button
  const resetSettingsBtn = document.getElementById('reset-settings');
  if (resetSettingsBtn) {
    resetSettingsBtn.addEventListener('click', handleResetSettings);
  }
}

/**
 * Setup action button event listeners
 */
function setupActionEventListeners() {
  // Home button
  const homeBtn = document.getElementById('home-btn');
  if (homeBtn) {
    homeBtn.addEventListener('click', () => {
      window.location.href = 'introduction.html';
    });
  }

  // Export chat button
  const exportChatBtn = document.getElementById('export-chat');
  if (exportChatBtn) {
    exportChatBtn.addEventListener('click', handleExportChat);
  }

  // Clear history button
  const clearHistoryBtn = document.getElementById('clear-history');
  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener('click', handleClearHistory);
  }

  // Share chat button
  const shareChatBtn = document.getElementById('share-chat');
  if (shareChatBtn) {
    shareChatBtn.addEventListener('click', handleShareChat);
  }

  // Voice chat button
  const voiceChatBtn = document.getElementById('voice-chat');
  if (voiceChatBtn) {
    voiceChatBtn.addEventListener('click', handleVoiceChat);
  }
}

/**
 * Setup keyboard shortcuts
 */
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to send message
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }

    // Escape to close settings
    if (e.key === 'Escape') {
      toggleSettingsPanel(false);
    }
  });
}

/**
 * Handle prompt input keyboard events
 * @param {KeyboardEvent} e - Keyboard event
 */
function handlePromptKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

/**
 * Handle new chat creation
 */
function handleNewChat() {
  const newChat = createChat('New Chat');
  selectChat(newChat.id);
  renderHistory();
  renderMessages();
  showToast('New chat created');
}

/**
 * Handle chat renaming
 */
function handleRenameChat() {
  const chat = getCurrentChat();
  if (!chat) return;

  const newName = prompt('Enter new chat name:', chat.name);
  if (newName && newName.trim() && newName !== chat.name) {
    renameChat(chat.id, newName.trim());
    renderHistory();
    updateChatTitle(newName.trim());
    showToast('Chat renamed');
  }
}

/**
 * Handle chat deletion
 */
function handleDeleteChat() {
  const chat = getCurrentChat();
  if (!chat) return;

  if (confirm(`Are you sure you want to delete "${
          chat.name}"? This action cannot be undone.`)) {
    deleteChat(chat.id);
    renderHistory();
    renderMessages();
    showToast('Chat deleted');
  }
}

/**
 * Handle history list clicks
 * @param {Event} e - Click event
 */
function handleHistoryClick(e) {
  const item = e.target.closest('[data-id]');
  if (item) {
    selectChat(item.dataset.id);
    renderHistory();
    renderMessages();
  }
}

/**
 * Send a message
 */
async function sendMessage() {
  const promptEl = document.getElementById('prompt');
  const content = promptEl?.value.trim();

  if (!content) return;

  const chat = getCurrentChat();
  if (!chat) return;

  // Add user message
  addMessage('user', content);
  appendMessageUI('user', content);

  // Clear input
  if (promptEl) {
    promptEl.value = '';
  }

  // Create AI response placeholder
  const aiBubble = appendMessageUI('assistant', '');
  setThinkingState(aiBubble, true);

  try {
    // 设置会话ID（使用聊天ID作为会话ID）
    setSessionId(chat.id);

    // 调用真实API
    let assistantContent = '';
    let toolCalls = [];

    await sendMessageToAPI(
      content,
      // 流式响应处理
      (chunk) => {
        assistantContent += chunk;
        updateAssistantMessage(aiBubble, assistantContent, false);
      },
      // 完成回调
      (result) => {
        assistantContent = result.content;
        toolCalls = result.toolCalls;

        setThinkingState(aiBubble, false);
        updateAssistantMessage(aiBubble, assistantContent, true);
        addMessage('assistant', assistantContent);

        // 如果有工具调用，添加工具信息到消息
        if (toolCalls.length > 0) {
          const message = addMessage('assistant', assistantContent);
          if (message) {
            message.toolCalls = toolCalls;
          }
        }
      },
      // 错误回调
      (error) => {
        throw error;
      }
    );

  } catch (error) {
    console.error('Error sending message:', error);
    setThinkingState(aiBubble, false);

    // 检查是否为连接错误
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      updateAssistantMessage(aiBubble, '无法连接到后端服务。请确保后端服务正在运行（http://localhost:8000）。', false);
      showToast('无法连接到后端服务', 5000);
    } else {
      updateAssistantMessage(aiBubble, 'Error: ' + error.message, false);
      showToast('Failed to send message: ' + error.message, 5000);
    }
  }
}

/**
 * 检查API连接状态并在应用启动时显示状态
 */
async function checkAPIStatus() {
  const isConnected = await checkAPIConnection();
  if (isConnected) {
    showToast('后端服务连接成功', 3000);

    // 获取可用工具
    const tools = await getAvailableTools();
    if (tools.length > 0) {
      console.log(`发现 ${tools.length} 个可用工具`);
    }
  } else {
    showToast('无法连接到后端服务，请确保后端服务正在运行', 5000);
  }
}

/**
 * Handle settings saving
 */
function handleSaveSettings() {
  const fontSizeSlider = document.getElementById('font-size-slider');
  const responseSpeedSelect = document.getElementById('response-speed');
  const typewriterToggle = document.getElementById('typewriter-toggle');
  const soundToggle = document.getElementById('sound-toggle');
  const autoSaveToggle = document.getElementById('auto-save-toggle');

  const newSettings = {
    fontSize: parseInt(fontSizeSlider?.value || 14),
    responseSpeed: responseSpeedSelect?.value || 'normal',
    typewriter: typewriterToggle?.checked ?? true,
    sound: soundToggle?.checked ?? false,
    autoSave: autoSaveToggle?.checked ?? true
  };

  appState.updateSettings(newSettings);
  saveSettings();
  showToast('Settings saved');
}

/**
 * Handle settings reset
 */
function handleResetSettings() {
  if (confirm('Are you sure you want to reset all settings to defaults?')) {
    localStorage.removeItem(appState.config.STORAGE_KEYS.SETTINGS);
    initializeSettings();
    showToast('Settings reset to defaults');
  }
}

/**
 * Handle chat export
 */
function handleExportChat() {
  const chat = getCurrentChat();
  if (!chat) {
    showToast('No chat to export');
    return;
  }

  const exportData = {
    title: chat.name,
    messages: chat.messages,
    exportDate: new Date().toISOString(),
    totalMessages: chat.messages.length,
    version: '1.0'
  };

  const blob = new Blob(
      [JSON.stringify(exportData, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${chat.name}_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  showToast('Chat exported successfully');
}

/**
 * Handle history clearing
 */
function handleClearHistory() {
  if (confirm(
          'Are you sure you want to clear all chat history? This action cannot be undone.')) {
    clearAllHistory();
    renderHistory();
    renderMessages();
    showToast('All chat history cleared');
  }
}

/**
 * Handle chat sharing
 */
async function handleShareChat() {
  const chat = getCurrentChat();
  if (!chat) {
    showToast('No chat to share');
    return;
  }

  const shareUrl =
      `${window.location.origin}${window.location.pathname}#chat=${chat.id}`;

  if (isSupported('webShare')) {
    try {
      await navigator.share({
        title: chat.name,
        text: `Check out my conversation with AI: ${chat.name}`,
        url: shareUrl
      });
    } catch (error) {
      // User cancelled or share failed, fallback to clipboard
      copyShareUrl(shareUrl);
    }
  } else {
    copyShareUrl(shareUrl);
  }
}

/**
 * Copy share URL to clipboard
 * @param {string} url - URL to copy
 */
async function copyShareUrl(url) {
  try {
    await navigator.clipboard.writeText(url);
    showToast('Share link copied to clipboard');
  } catch (error) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = url;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    showToast('Share link copied to clipboard');
  }
}

/**
 * Handle voice chat
 */
function handleVoiceChat() {
  if (!isSupported('webSpeech')) {
    showToast('Voice input is not supported in your browser');
    return;
  }

  showToast('Voice chat feature coming soon!');
}

/**
 * Update storage information display
 */
function updateStorageInfo() {
  const storageInfo = document.getElementById('storage-info');
  if (storageInfo) {
    storageInfo.textContent = getStorageUsage();
  }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Export main functions for potential external use
window.ChatApp = {
  sendMessage,
  handleNewChat,
  handleExportChat,
  handleShareChat,
  showToast
};