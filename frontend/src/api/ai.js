import request from '@/utils/request'

/**
 * 获取AI日程提醒
 * @returns {Promise} 返回AI日程提醒列表
 */
export function getScheduleReminders() {
  return request({
    url: '/api/ai/schedule-reminder/',
    method: 'get'
  })
}

/**
 * 调用AI聊天
 * @param {Object} data - 聊天数据
 * @returns {Promise} 返回AI回复
 */
export function aiChat(data) {
  return request({
    url: '/api/ai/chat/',
    method: 'post',
    data
  })
}

/**
 * 生成AI内容
 * @param {Object} data - 生成请求数据
 * @returns {Promise} 返回生成的内容
 */
export function generateContent(data) {
  return request({
    url: '/api/ai/generate/',
    method: 'post',
    data
  })
}

/**
 * 标记AI日程提醒为已读
 * @param {number} id - 提醒ID
 * @returns {Promise}
 */
export function markScheduleReminderAsRead(id) {
  return request({
    url: `/api/ai/recommendations/${id}/mark_as_read/`,
    method: 'post'
  })
}

/**
 * 文档增强AI对话
 * @param {Object} data - { message, chat_id, document_ids }
 * @returns {Promise}
 */
export function aiChatWithDocuments(data) {
  return request({
    url: '/api/ai/chat-with-documents/',
    method: 'post',
    data,
    responseType: 'text'
  })
}

/**
 * 流式文档增强AI对话
 * @param {Object} data - { message, chat_id, document_ids }
 * @param {Function} onChunk - 处理每个数据块的回调函数
 * @param {Function} onComplete - 处理完成时的回调函数
 * @param {Function} onError - 处理错误的回调函数
 * @returns {AbortController} 返回可用于取消请求的控制器
 */
export function aiChatWithDocumentsStream(data, onChunk, onComplete, onError) {
  // 创建AbortController，用于在需要时取消请求
  const controller = new AbortController();
  const signal = controller.signal;
  
  // 获取Token
  const token = localStorage.getItem('token');
  
  // 构建请求头
  const headers = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  // 使用fetch API发起请求
  fetch('http://localhost:8000/api/ai/chat-with-documents/', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(data),
    signal: signal
  })
  .then(async response => {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: '服务返回了错误状态，且响应体不是有效的JSON。' }));
      throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let lastChatId = null;

    const processStream = async () => {
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          if (buffer) {
            console.error("Stream finished but buffer is not empty:", buffer);
          }
          onComplete && onComplete(lastChatId);
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep the last partial line in buffer

        for (const line of lines) {
          if (line.startsWith("data:")) {
            const jsonStr = line.substring(5).trim();
            if (jsonStr === "[DONE]") {
              onComplete && onComplete(lastChatId);
              return;
            }
            try {
              const parsed = JSON.parse(jsonStr);
              onChunk && onChunk(parsed, parsed.chat_id);

              // 处理session_id类型的消息，提取chat_id
              if (parsed.type === 'session_id') {
                lastChatId = parsed.chat_id;
              } else if (parsed.chat_id) {
                lastChatId = parsed.chat_id;
              }
            } catch (error) {
              console.error("无法解析JSON流: ", jsonStr, error);
              onError && onError(new Error("无法解析服务器发送的数据"));
            }
          }
        }
      }
    };

    processStream().catch(err => {
      console.error("An error occurred while processing the stream:", err);
      onError && onError(err);
    });
  })
  .catch(error => {
    if (error.name !== 'AbortError') {
      console.error('Fetch request failed:', error);
      onError && onError(error);
    }
  });
  
  // 返回控制器，以便调用者可以取消请求
  return controller;
}

/**
 * 获取AI聊天会话列表
 */
export function getAIChatSessions() {
  return request({
    url: '/api/ai/chats/',
    method: 'get'
  })
}

/**
 * 获取AI聊天会话详情
 * @param {Number} id - 聊天会话ID
 */
export function getAIChatSession(id) {
  return request({
    url: `/api/ai/chats/${id}/`,
    method: 'get'
  })
}

/**
 * 删除AI聊天会话
 * @param {Number} id - 聊天会话ID
 */
export function deleteAIChatSession(id) {
  return request({
    url: `/api/ai/chats/${id}/`,
    method: 'delete'
  })
}

export function getChatHistory(chat_id) {
  return request({
    url: `/api/ai/chats/${chat_id}/messages/`,
    method: 'get'
  });
}

/**
 * 与文档进行非流式对话
 * @param {Object} data - { message, chat_id, document_ids, chatMode, search_method }
 */
export function chatWithDocuments(data) {
  return request({
    url: '/api/ai/chat-with-documents/',
    method: 'post',
    data,
  });
} 