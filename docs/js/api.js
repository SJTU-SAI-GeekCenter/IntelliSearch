/**
 * API service for backend communication
 * @fileoverview Backend API integration and tool calling effects
 */

import {CONFIG} from './config.js';
import {showToast} from './ui.js';

// 全局状态
let currentSessionId = null;
let isConnecting = false;

/**
 * 生成新的会话ID
 */
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * 获取或创建当前会话ID
 */
function getCurrentSessionId() {
    if (!currentSessionId) {
        currentSessionId = generateSessionId();
    }
    return currentSessionId;
}

/**
 * 显示工具调用特效
 */
function showToolCallingEffect(toolName) {
    // 创建工具调用指示器
    let indicator = document.getElementById('tool-calling-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'tool-calling-indicator';
        indicator.innerHTML = `
            <div class="tool-calling-content">
                <div class="tool-spinner"></div>
                <div class="tool-info">
                    <div class="tool-title">正在调用工具</div>
                    <div class="tool-name" id="tool-name-display">${toolName}</div>
                </div>
            </div>
        `;

        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            #tool-calling-indicator {
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%);
                border: 2px solid #10b981;
                border-radius: 12px;
                padding: 16px;
                box-shadow: 0 0 30px rgba(16, 185, 129, 0.3), 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                z-index: 1000;
                animation: slideInRight 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                min-width: 280px;
                position: relative;
                overflow: hidden;
            }

            #tool-calling-indicator::before {
                content: '';
                position: absolute;
                top: -2px;
                left: -2px;
                right: -2px;
                bottom: -2px;
                background: linear-gradient(45deg, #10b981, #4a69ee, #10b981);
                border-radius: 12px;
                opacity: 0.8;
                z-index: -1;
                animation: borderGlow 3s linear infinite;
            }

            .tool-calling-content {
                display: flex;
                align-items: center;
                gap: 16px;
            }

            .tool-spinner {
                width: 32px;
                height: 32px;
                position: relative;
                border: 3px solid rgba(16, 185, 129, 0.2);
                border-radius: 50%;
            }

            .tool-spinner::before {
                content: '';
                position: absolute;
                top: -3px;
                left: -3px;
                right: -3px;
                bottom: -3px;
                border: 3px solid transparent;
                border-top: 3px solid #10b981;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            .tool-spinner::after {
                content: '🔧';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 16px;
                animation: pulse 2s ease-in-out infinite;
            }

            .tool-info {
                flex: 1;
            }

            .tool-title {
                font-size: 14px;
                font-weight: 600;
                color: #111827;
                margin-bottom: 4px;
            }

            .tool-name {
                font-size: 12px;
                color: #10b981;
                font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(74, 105, 238, 0.1));
                padding: 4px 8px;
                border-radius: 4px;
                border: 1px solid rgba(16, 185, 129, 0.3);
                font-weight: 500;
                letter-spacing: 0.5px;
            }

            @keyframes borderGlow {
                0%, 100% {
                    opacity: 0.8;
                    transform: rotate(0deg);
                }
                50% {
                    opacity: 1;
                    transform: rotate(180deg);
                }
            }

            @keyframes pulse {
                0%, 100% {
                    transform: translate(-50%, -50%) scale(1);
                    opacity: 1;
                }
                50% {
                    transform: translate(-50%, -50%) scale(1.2);
                    opacity: 0.8;
                }
            }

            @keyframes spin {
                0% {
                    transform: rotate(0deg);
                }
                100% {
                    transform: rotate(360deg);
                }
            }

            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }

    document.getElementById('tool-name-display').textContent = toolName;
    document.body.appendChild(indicator);
}

/**
 * 隐藏工具调用特效
 */
function hideToolCallingEffect() {
    const indicator = document.getElementById('tool-calling-indicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * 显示工具成功特效
 */
function showToolSuccessEffect() {
    const effect = document.createElement('div');
    effect.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        pointer-events: none;
        z-index: 10000;
    `;

    const checkmark = document.createElement('div');
    checkmark.style.cssText = `
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #10b981, #34d399);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        color: white;
        animation: successPop 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    `;
    checkmark.textContent = '✓';

    // 添加动画
    const style = document.createElement('style');
    style.textContent = `
        @keyframes successPop {
            0% {
                transform: scale(0) rotate(0deg);
                opacity: 0;
            }
            50% {
                transform: scale(1.2) rotate(180deg);
                opacity: 1;
            }
            70% {
                transform: scale(0.9) rotate(270deg);
                opacity: 1;
            }
            100% {
                transform: scale(1) rotate(360deg);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);

    effect.appendChild(checkmark);
    document.body.appendChild(effect);

    // 1秒后移除
    setTimeout(() => {
        effect.remove();
        style.remove();
    }, 1000);
}

/**
 * 发送消息到后端API
 * @param {string} message - 用户消息
 * @param {Function} onChunk - 流式响应处理函数
 * @param {Function} onComplete - 完成回调函数
 * @param {Function} onError - 错误回调函数
 */
export async function sendMessageToAPI(message, onChunk, onComplete, onError) {
    if (isConnecting) {
        showToast('正在连接中，请稍候...', 3000);
        return;
    }

    isConnecting = true;

    try {
        const response = await fetch(`${CONFIG.BACKEND_URL}/api/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: getCurrentSessionId(),
                use_tools: true
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantContent = '';
        let toolCalls = [];

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);

                        if (data === '[DONE]') {
                            break;
                        }

                        try {
                            const event = JSON.parse(data);

                            switch (event.type) {
                                case 'content':
                                    assistantContent += event.content;
                                    if (onChunk) {
                                        onChunk(event.content);
                                    }
                                    break;

                                case 'tool_call_start':
                                    showToolCallingEffect(event.tool_call.name);
                                    toolCalls.push({
                                        id: event.tool_call.id,
                                        name: event.tool_call.name,
                                        arguments: ''
                                    });
                                    break;

                                case 'tool_call_delta':
                                    if (toolCalls.length > 0) {
                                        toolCalls[toolCalls.length - 1].arguments += event.tool_call.arguments;
                                    }
                                    break;

                                case 'tool_result':
                                    console.log('Tool result:', event.tool_result);
                                    break;

                                case 'error':
                                    throw new Error(event.error);
                            }
                        } catch (parseError) {
                            console.error('Failed to parse SSE data:', parseError, 'Data:', data);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }

        hideToolCallingEffect();
        if (toolCalls.length > 0) {
            showToolSuccessEffect();
        }

        if (onComplete) {
            onComplete({
                content: assistantContent,
                toolCalls: toolCalls
            });
        }

    } catch (error) {
        console.error('API Error:', error);
        hideToolCallingEffect();

        if (onError) {
            onError(error);
        } else {
            showToast(`API 错误: ${error.message}`, 5000);
        }
    } finally {
        isConnecting = false;
    }
}

/**
 * 检查API连接状态
 */
export async function checkAPIConnection() {
    try {
        const response = await fetch(`${CONFIG.BACKEND_URL}/health`);
        return response.ok;
    } catch (error) {
        return false;
    }
}

/**
 * 获取可用工具列表
 */
export async function getAvailableTools() {
    try {
        const response = await fetch(`${CONFIG.BACKEND_URL}/api/tools`);
        if (response.ok) {
            const data = await response.json();
            return data.tools || [];
        }
    } catch (error) {
        console.error('Failed to fetch tools:', error);
    }
    return [];
}

/**
 * 设置会话ID
 */
export function setSessionId(sessionId) {
    currentSessionId = sessionId;
}

/**
 * 获取当前会话ID
 */
export { getCurrentSessionId };