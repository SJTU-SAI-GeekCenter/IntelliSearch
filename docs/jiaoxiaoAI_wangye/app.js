// 状态与存储
const STORAGE_KEY = 'xj_ai_chats_v1';
const DEFAULT_BACKEND = '';

/** @type {{id:string,name:string,messages:Array<{role:'user'|'assistant'|'system',content:string}>}[]} */
let chats = loadChats();
let currentId = chats[0]?.id || createChat('未命名会话').id;

// 元素引用
const appEl = document.getElementById('app');
const historyListEl = document.getElementById('history-list');
const chatTitleEl = document.getElementById('chat-title');
const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('send');
const newChatBtn = document.getElementById('new-chat');
const renameBtn = document.getElementById('rename-chat');
const deleteBtn = document.getElementById('delete-chat');
const messagesEl = document.getElementById('messages');
const toastEl = document.getElementById('toast');
const brandEl = document.querySelector('.brand');

// 删除确认状态
let isDeleteConfirmMode = false;

// 初始化
renderHistory();
renderMessages();
autosize(promptEl);

// 侧边栏展开收起控制
brandEl.addEventListener('click', function() {
	appEl.classList.toggle('expanded');
});

// 事件
newChatBtn.addEventListener('click', () => {
	const c = createChat('新会话');
	selectChat(c.id);
});

renameBtn.addEventListener('click', () => {
	const chat = getCurrent();
	if (!chat) return;
	
	if (isDeleteConfirmMode) {
		// 如果是删除确认模式，点击"确定"执行删除
		doDeleteChat();
		// 恢复正常模式
		isDeleteConfirmMode = false;
		renameBtn.textContent = '命名';
		deleteBtn.textContent = '删除';
		renameBtn.title = '重命名会话';
		deleteBtn.title = '删除会话';
	} else {
		// 正常模式下执行重命名
		chatTitleEl.removeAttribute('readonly');
		chatTitleEl.focus();
		chatTitleEl.select();
	}
});

// 监听聊天标题输入框的编辑完成事件
chatTitleEl.addEventListener('blur', () => {
	finishEditingTitle();
});

chatTitleEl.addEventListener('keydown', (e) => {
	if (e.key === 'Enter') {
		e.preventDefault();
		finishEditingTitle();
	} else if (e.key === 'Escape') {
		// 按ESC键取消编辑，恢复原名称
		const chat = getCurrent();
		if (chat) {
			chatTitleEl.value = chat.name;
		}
		chatTitleEl.setAttribute('readonly', 'readonly');
	}
});

function finishEditingTitle() {
	const chat = getCurrent();
	if (!chat) return;
	const newName = chatTitleEl.value.trim() || '未命名会话';
	chat.name = newName;
	chatTitleEl.value = newName;
	chatTitleEl.setAttribute('readonly', 'readonly');
	save();
	renderHistory();
}

deleteBtn.addEventListener('click', () => {
	if (isDeleteConfirmMode) {
		// 如果已经是确认模式，点击"取消"恢复正常模式
		isDeleteConfirmMode = false;
		renameBtn.textContent = '命名';
		deleteBtn.textContent = '删除';
		renameBtn.title = '重命名会话';
		deleteBtn.title = '删除会话';
	} else {
		// 进入确认模式
		isDeleteConfirmMode = true;
		renameBtn.textContent = '确定';
		deleteBtn.textContent = '取消';
		renameBtn.title = '确认删除会话';
		deleteBtn.title = '取消删除';
	}
});

// 实际执行删除操作的函数
function doDeleteChat() {
	chats = chats.filter(c => c.id !== currentId);
	if (chats.length === 0) {
		const c = createChat('未命名会话');
		currentId = c.id;
	} else {
		currentId = chats[0].id;
	}
	save();
	renderHistory();
	renderMessages();
}

sendBtn.addEventListener('click', sendMessage);

promptEl.addEventListener('keydown', function (e) {
	if (e.key === 'Enter' && !e.shiftKey) {
		e.preventDefault();
		sendMessage();
	}
});

// 历史点击
historyListEl.addEventListener('click', function (e) {
	const item = e.target.closest('[data-id]');
	if (!item) return;
	selectChat(item.dataset.id);
});

// 核心函数
async function sendMessage() {
	const content = promptEl.value.trim();
	if (!content) return;
	// 移除后端地址检查，允许消息发送

	const chat = getCurrent();
	if (!chat) return;
	// 追加用户消息
	const userMsg = { role: 'user', content: content };
	chat.messages.push(userMsg);
	save();
	appendMessageUI('user', content);

	// 准备 AI 占位消息
	const aiContainer = appendMessageUI('assistant', '');
	aiContainer.classList.add('typing');
	setThinking(aiContainer, true);

	promptEl.value = '';
	autosize(promptEl);

	// 模拟AI响应
	try {
		// 模拟思考延迟
		await new Promise(resolve => setTimeout(resolve, 1000));
		
		// 简单的模拟响应
		let response = "感谢您的消息！由于后端服务未配置，这是一条模拟回复。\n\n您的问题很有趣，我会尽力提供帮助。如果您需要更详细的回答，请确保后端服务正常运行。";
		
		setThinking(aiContainer, false);
		aiContainer.classList.remove('typing');
		updateAssistantUI(aiContainer, response);
		pushAssistantMessage(response);
	} catch (err) {
		setThinking(aiContainer, false);
		aiContainer.classList.remove('typing');
		updateAssistantUI(aiContainer, '发生错误：' + err.message);
		toast('消息处理失败');
	}
}

function pushAssistantMessage(text) {
	const chat = getCurrent();
	if (!chat) return;
	chat.messages.push({ role: 'assistant', content: text });
	save();
}

// UI 渲染
function renderHistory() {
	historyListEl.innerHTML = '';
	for (var i = 0; i < chats.length; i++) {
		const c = chats[i];
		const el = document.createElement('div');
		el.className = 'history-item' + (c.id === currentId ? ' active' : '');
		el.dataset.id = c.id;
		el.innerHTML = '<span class="name">' + escapeHtml(c.name) + '</span>';
		historyListEl.appendChild(el);
	}
}

function renderMessages() {
	const chat = getCurrent();
	if (!chat) return;
	chatTitleEl.value = chat.name;
	messagesEl.innerHTML = '';
	for (var i = 0; i < chat.messages.length; i++) {
		const m = chat.messages[i];
		appendMessageUI(m.role, m.content);
	}
	messagesEl.scrollTop = messagesEl.scrollHeight;
}

function appendMessageUI(role, content) {
	const row = document.createElement('div');
	row.className = 'msg ' + role;
	row.innerHTML = `
		<div class="msg-content">
			<div class="avatar ${role === 'assistant' ? 'ai' : 'user'}">${role === 'assistant' ? 'AI' : '👤'}</div>
			<div class="bubble">${renderMarkdown(content || '')}</div>
		</div>
	`;
	messagesEl.appendChild(row);
	messagesEl.scrollTop = messagesEl.scrollHeight;
	return row.querySelector('.bubble');
}

function updateAssistantUI(bubbleEl, text) {
	if (bubbleEl) {
		bubbleEl.innerHTML = renderMarkdown(text);
		messagesEl.scrollTop = messagesEl.scrollHeight;
	}
}

function setThinking(bubbleEl, on) {
	if (bubbleEl) {
		if (on) {
			bubbleEl.innerHTML = '<span class="thinking">正在思考中…</span>';
		} else {
			bubbleEl.innerHTML = '';
		}
	}
}

// 会话管理
function createChat(name) {
	const c = { id: cryptoRandomId(), name: name, messages: [] };
	chats.unshift(c);
	save();
	return c;
}

function selectChat(id) {
	currentId = id;
	renderHistory();
	renderMessages();
}

function getCurrent() { return chats.find(function (c) { return c.id === currentId; }); }

// 存储
function save() { localStorage.setItem(STORAGE_KEY, JSON.stringify(chats)); }
function loadChats() {
	try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch (e) { return []; }
}

// 工具函数
function cryptoRandomId() {
	if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
	return 'id_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function joinUrl(base, path) {
	if (!base) return path;
	return base.replace(/\/$/, '') + path;
}

function toast(text, ms) {
	ms = ms || 2200;
	toastEl.textContent = text;
	toastEl.classList.add('show');
	setTimeout(function () { toastEl.classList.remove('show'); }, ms);
}

function autosize(textarea) {
	var resize = function () {
		textarea.style.height = 'auto';
		textarea.style.height = Math.min(240, textarea.scrollHeight) + 'px';
	};
	textarea.addEventListener('input', resize);
	resize();
}

// 极简 markdown 渲染（只处理换行、代码块、行内代码）
function renderMarkdown(text) {
	if (!text) return '';
	// 代码块 ``` ```
	text = text.replace(/```([\s\S]*?)```/g, function (_, code) {
		return '<pre><code>' + escapeHtml(code) + '</code></pre>';
	});
	// 行内代码
	text = text.replace(/`([^`]+)`/g, function (_, code) { return '<code>' + escapeHtml(code) + '</code>'; });
	// 段落
	var parts = text.split(/\n{2,}/).map(function (p) { return '<p>' + p.replace(/\n/g, '<br/>') + '</p>'; });
	return parts.join('');
}

function escapeHtml(s) {
	return s
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/\"/g, '&quot;')
		.replace(/'/g, '&#39;');
}






