/**
 * Управление обсуждениями в localStorage для незарегистрированных пользователей
 */
class LocalStorageManager {
    constructor() {
        this.storageKey = 'ai_discussions';
    }

    /**
     * Получить все обсуждения из localStorage
     * @returns {Array} Массив обсуждений
     */
    getAllDiscussions() {
        const data = localStorage.getItem(this.storageKey);
        return data ? JSON.parse(data) : [];
    }

    /**
     * Получить обсуждение по ID
     * @param {string} id ID обсуждения
     * @returns {Object|null} Объект обсуждения или null, если не найдено
     */
    getDiscussionById(id) {
        const discussions = this.getAllDiscussions();
        return discussions.find(d => d.id.toString() === id.toString()) || null;
    }

    /**
     * Сохранить обсуждение в localStorage
     * @param {Object} discussion Объект обсуждения
     */
    saveDiscussion(discussion) {
        const discussions = this.getAllDiscussions();
        const existingIndex = discussions.findIndex(d => d.id.toString() === discussion.id.toString());
        
        if (existingIndex >= 0) {
            // Обновляем существующее обсуждение
            discussions[existingIndex] = {...discussions[existingIndex], ...discussion};
        } else {
            // Добавляем новое обсуждение
            discussions.push(discussion);
        }
        
        localStorage.setItem(this.storageKey, JSON.stringify(discussions));
    }

    /**
     * Удалить обсуждение из localStorage
     * @param {string} id ID обсуждения
     * @returns {boolean} True, если обсуждение было удалено
     */
    deleteDiscussion(id) {
        const discussions = this.getAllDiscussions();
        const initialLength = discussions.length;
        const filteredDiscussions = discussions.filter(d => d.id.toString() !== id.toString());
        
        localStorage.setItem(this.storageKey, JSON.stringify(filteredDiscussions));
        return filteredDiscussions.length < initialLength;
    }

    /**
     * Добавить сообщение к обсуждению
     * @param {string} discussionId ID обсуждения
     * @param {Object} message Объект сообщения
     * @returns {boolean} True, если сообщение было добавлено
     */
    addMessage(discussionId, message) {
        const discussion = this.getDiscussionById(discussionId);
        if (!discussion) return false;
        
        if (!discussion.messages) {
            discussion.messages = [];
        }
        
        discussion.messages.push(message);
        this.saveDiscussion(discussion);
        return true;
    }

    /**
     * Обновить статус обсуждения
     * @param {string} discussionId ID обсуждения
     * @param {Object} updates Объект с обновлениями
     * @returns {boolean} True, если обсуждение было обновлено
     */
    updateDiscussion(discussionId, updates) {
        const discussion = this.getDiscussionById(discussionId);
        if (!discussion) return false;
        
        const updatedDiscussion = {...discussion, ...updates};
        this.saveDiscussion(updatedDiscussion);
        return true;
    }

    /**
     * Перенести все обсуждения на сервер
     * @param {string} apiEndpoint Endpoint API для переноса
     * @param {string} token Токен аутентификации
     * @returns {Promise} Promise с результатом операции
     */
    async migrateDiscussionsToServer(apiEndpoint, token) {
        const discussions = this.getAllDiscussions();
        if (discussions.length === 0) {
            return { status: 'success', message: 'Нет обсуждений для переноса' };
        }
        
        try {
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ discussions })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Очищаем localStorage после успешного переноса
                localStorage.removeItem(this.storageKey);
            }
            
            return result;
        } catch (error) {
            console.error('Error migrating discussions:', error);
            return { 
                status: 'error', 
                message: 'Ошибка при переносе обсуждений: ' + error.message 
            };
        }
    }

    /**
     * Очистить все обсуждения
     */
    clearAllDiscussions() {
        localStorage.removeItem(this.storageKey);
    }
}

// Экспортируем экземпляр для использования в других скриптах
const localStorageManager = new LocalStorageManager(); 