// Enhanced Chat Features: File Upload, Edit/Delete, Search, Push Notifications

// ==================== Dark Mode ====================
function initDarkMode() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    themeToggle.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/toggle_theme', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            
            if (data.success) {
                document.body.classList.toggle('dark-mode');
                themeToggle.textContent = data.theme === 'dark' ? '☀️' : '🌙';
            }
        } catch (error) {
            console.error('Error toggling theme:', error);
        }
    });
}

// ==================== File Upload ====================
function initFileUpload() {
    const fileInput = document.getElementById('file-input');
    const fileButton = document.getElementById('file-button');
    const filePreview = document.getElementById('file-preview');
    
    if (!fileInput || !fileButton) return;

    fileButton.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // بررسی سایز فایل (16MB max)
        if (file.size > 16 * 1024 * 1024) {
            alert('حجم فایل نباید بیشتر از 16 مگابایت باشد');
            fileInput.value = '';
            return;
        }

        // نمایش پیش‌نمایش
        showFilePreview(file);
    });
}

function showFilePreview(file) {
    const filePreview = document.getElementById('file-preview');
    if (!filePreview) return;

    const fileName = document.createElement('div');
    fileName.className = 'file-preview-item';
    
    const fileIcon = getFileIcon(file.type);
    const fileSize = formatFileSize(file.size);
    
    fileName.innerHTML = `
        <span class="file-icon">${fileIcon}</span>
        <span class="file-name">${file.name}</span>
        <span class="file-size">${fileSize}</span>
        <button class="remove-file" onclick="removeFilePreview()">✕</button>
    `;
    
    filePreview.innerHTML = '';
    filePreview.appendChild(fileName);
    filePreview.style.display = 'block';
}

function removeFilePreview() {
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    
    if (fileInput) fileInput.value = '';
    if (filePreview) {
        filePreview.innerHTML = '';
        filePreview.style.display = 'none';
    }
}

function getFileIcon(fileType) {
    if (fileType.startsWith('image/')) return '🖼️';
    if (fileType.startsWith('video/')) return '🎥';
    if (fileType.startsWith('audio/')) return '🎵';
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('zip') || fileType.includes('rar')) return '📦';
    return '📎';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ==================== Message Edit/Delete ====================
function initMessageActions() {
    document.addEventListener('click', (e) => {
        // Edit message
        if (e.target.classList.contains('edit-message')) {
            const messageId = e.target.dataset.messageId;
            const messageContent = e.target.closest('.message').querySelector('.message-content');
            editMessage(messageId, messageContent);
        }
        
        // Delete message
        if (e.target.classList.contains('delete-message')) {
            const messageId = e.target.dataset.messageId;
            deleteMessage(messageId);
        }
    });
}

async function editMessage(messageId, messageElement) {
    const currentContent = messageElement.textContent;
    const newContent = prompt('ویرایش پیام:', currentContent);
    
    if (!newContent || newContent === currentContent) return;
    
    try {
        const response = await fetch('/api/edit_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message_id: messageId,
                content: newContent
            })
        });
        
        const data = await response.json();
        if (data.success) {
            messageElement.textContent = newContent;
            
            // اضافه کردن نشان ویرایش شده
            if (!messageElement.querySelector('.edited-badge')) {
                const editedBadge = document.createElement('span');
                editedBadge.className = 'edited-badge';
                editedBadge.textContent = ' (ویرایش شده)';
                messageElement.appendChild(editedBadge);
            }
            
            // ارسال event به سرور
            if (window.socket) {
                window.socket.emit('edit_message', {
                    message_id: messageId,
                    content: newContent,
                    other_user_id: window.otherUserId
                });
            }
        }
    } catch (error) {
        console.error('Error editing message:', error);
        alert('خطا در ویرایش پیام');
    }
}

async function deleteMessage(messageId) {
    if (!confirm('آیا مطمئن هستید که می‌خواهید این پیام را حذف کنید؟')) return;
    
    try {
        const response = await fetch('/api/delete_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message_id: messageId
            })
        });
        
        const data = await response.json();
        if (data.success) {
            const messageElement = document.querySelector(`[data-message-id="${messageId}"]`).closest('.message');
            if (messageElement) {
                messageElement.style.opacity = '0.5';
                messageElement.querySelector('.message-content').textContent = 'این پیام حذف شد';
                messageElement.querySelectorAll('.message-actions').forEach(el => el.remove());
            }
            
            // ارسال event به سرور
            if (window.socket) {
                window.socket.emit('delete_message', {
                    message_id: messageId,
                    other_user_id: window.otherUserId
                });
            }
        }
    } catch (error) {
        console.error('Error deleting message:', error);
        alert('خطا در حذف پیام');
    }
}

// ==================== Search Messages ====================
function initSearchMessages() {
    const searchInput = document.getElementById('search-messages');
    const searchResults = document.getElementById('search-results');
    
    if (!searchInput) return;
    
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            searchResults.innerHTML = '';
            searchResults.style.display = 'none';
            return;
        }
        
        searchTimeout = setTimeout(() => {
            searchMessages(query);
        }, 500);
    });
}

async function searchMessages(query) {
    try {
        const response = await fetch('/api/search_messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        displaySearchResults(data.results);
    } catch (error) {
        console.error('Error searching messages:', error);
    }
}

function displaySearchResults(results) {
    const searchResults = document.getElementById('search-results');
    if (!searchResults) return;
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="no-results">نتیجه‌ای یافت نشد</div>';
        searchResults.style.display = 'block';
        return;
    }
    
    const html = results.map(result => `
        <div class="search-result-item">
            <a href="${result.chat_link}">
                <div class="result-users">${result.sender_name} → ${result.receiver_name}</div>
                <div class="result-content">${result.content}</div>
                <div class="result-time">${result.timestamp}</div>
            </a>
        </div>
    `).join('');
    
    searchResults.innerHTML = html;
    searchResults.style.display = 'block';
}

// ==================== Push Notifications ====================
async function initPushNotifications() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.log('Push notifications not supported');
        return;
    }
    
    try {
        // ثبت Service Worker
        const registration = await navigator.serviceWorker.register('/static/js/service-worker.js');
        console.log('Service Worker registered');
        
        // درخواست مجوز
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            console.log('Notification permission denied');
            return;
        }
        
        // اشتراک در Push
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(window.VAPID_PUBLIC_KEY)
        });
        
        // ارسال اشتراک به سرور
        await fetch('/api/subscribe_push', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(subscription.toJSON())
        });
        
        console.log('Push subscription successful');
    } catch (error) {
        console.error('Error setting up push notifications:', error);
    }
}

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// ==================== SocketIO Listeners ====================
function initSocketIOListeners() {
    if (!window.socket) return;
    
    // دریافت پیام ویرایش شده
    window.socket.on('message_edited', (data) => {
        const messageElement = document.querySelector(`[data-message-id="${data.message_id}"]`);
        if (messageElement) {
            const contentElement = messageElement.closest('.message').querySelector('.message-content');
            contentElement.textContent = data.new_content;
            
            if (!contentElement.querySelector('.edited-badge')) {
                const editedBadge = document.createElement('span');
                editedBadge.className = 'edited-badge';
                editedBadge.textContent = ' (ویرایش شده)';
                contentElement.appendChild(editedBadge);
            }
        }
    });
    
    // دریافت پیام حذف شده
    window.socket.on('message_deleted', (data) => {
        const messageElement = document.querySelector(`[data-message-id="${data.message_id}"]`);
        if (messageElement) {
            const messageDiv = messageElement.closest('.message');
            messageDiv.style.opacity = '0.5';
            messageDiv.querySelector('.message-content').textContent = 'این پیام حذف شد';
            messageDiv.querySelectorAll('.message-actions').forEach(el => el.remove());
        }
    });
}

// ==================== Initialize All ====================
document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initFileUpload();
    initMessageActions();
    initSearchMessages();
    initPushNotifications();
    initSocketIOListeners();
});