import request from '@/utils/request'

/**
 * 获取聊天会话列表
 */
export function getChatSessions() {
  return request({
    url: '/api/chat/sessions/',
    method: 'get'
  })
}

/**
 * 获取聊天会话详情
 * @param {Number} id - 聊天会话ID
 */
export function getChatSession(id) {
  return request({
    url: `/api/chat/sessions/${id}/`,
    method: 'get'
  })
}

/**
 * 创建新的聊天会话
 * @param {Object} data - 聊天会话数据
 */
export function createChatSession(data) {
  return request({
    url: '/api/chat/sessions/',
    method: 'post',
    data
  })
}

/**
 * 发送文本消息
 * @param {Object} data - 消息数据
 */
export function sendTextMessage(data) {
  return request({
    url: '/api/chat/messages/',
    method: 'post',
    data: {
      ...data,
      message_type: 'text'
    }
  })
}

/**
 * 发送文件消息
 * @param {Number} chatId - 聊天ID
 * @param {String} content - 消息内容
 * @param {File} file - 文件对象
 */
export function sendFileMessage(chatId, content, file) {
  const formData = new FormData();
  formData.append('chat', chatId);
  formData.append('message_type', 'file');
  formData.append('content', content);
  formData.append('file', file);
  
  return request({
    url: '/api/chat/messages/',
    method: 'post',
    data: formData
  })
}

/**
 * 发送图片消息
 * @param {Number} chatId - 聊天ID
 * @param {String} content - 消息内容
 * @param {File} image - 图片文件
 */
export function sendImageMessage(chatId, content, image) {
  const formData = new FormData();
  formData.append('chat', chatId);
  formData.append('message_type', 'image');
  formData.append('content', content);
  formData.append('file', image);
  
  return request({
    url: '/api/chat/messages/',
    method: 'post',
    data: formData
  })
}

/**
 * 发送知识库消息
 * @param {Object} data - 消息数据，包含chat和knowledge_id
 */
export function sendKnowledgeMessage(data) {
  return request({
    url: '/api/chat/messages/',
    method: 'post',
    data: {
      ...data,
      message_type: 'knowledge',
      content: '分享了一个知识库文件'
    }
  })
}

/**
 * 下载消息中的文件
 * @param {Number} messageId - 消息ID
 */
export function downloadMessageFile(messageId) {
  return request({
    url: `/api/chat/messages/${messageId}/download/`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 发送文档消息 - 分享智能文档到聊天
 * @param {Object} data - 包含chat(聊天ID)、document_id(文档ID)、format(文档格式，如pdf/word)、title(文档标题)的对象
 */
export function sendDocumentMessage(data) {
  // 创建FormData对象
  const formData = new FormData();
  
  // 添加必要的字段
  formData.append('chat', data.chat);
  formData.append('message_type', 'file');
  formData.append('document_id', data.document_id);
  formData.append('format', data.format);
  formData.append('title', data.title);
  formData.append('content', `分享了一个${data.format === 'pdf' ? 'PDF' : 'Word'}文档`);
  
  return request({
    url: '/api/chat/messages/',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 向聊天添加参与者
 * @param {Number} chatId - 聊天会话ID
 * @param {Number} userId - 用户ID
 */
export function addChatParticipant(chatId, userId) {
  return request({
    url: `/api/chat/sessions/${chatId}/add_participant/`,
    method: 'post',
    data: {
      user_id: userId
    }
  })
}

/**
 * 从聊天中移除参与者
 * @param {Number} chatId - 聊天会话ID
 * @param {Number} userId - 用户ID
 */
export function removeChatParticipant(chatId, userId) {
  return request({
    url: `/api/chat/sessions/${chatId}/remove_participant/`,
    method: 'post',
    data: {
      user_id: userId
    }
  })
}

/**
 * 从聊天消息添加日历事件
 * @param {Number} messageId - 消息ID
 * @param {Object} data - 可选的更新日程数据
 * @param {Boolean} preview - 是否仅预览不创建事件
 */
export function addCalendarEvent(messageId, data, preview = false) {
  let url = `/api/chat/messages/${messageId}/add_calendar_event/`
  if (preview) {
    url += '?preview=true'
  }
  
  return request({
    url: url,
    method: 'post',
    data
  })
}

// 获取知识库列表
export function getKnowledgeList(params) {
  return request({
    url: '/api/knowledge/files/',
    method: 'get',
    params
  })
}

// 查看文件内容 
export function deleteMessage(id) {
  return request({
    url: `/chat/messages/${id}/`,
    method: 'delete'
  })
}

// 新增：查找或创建一对一聊天
export function findOrCreateChat(userId) {
  return request({
    url: '/api/chat/find-or-create/',
    method: 'post',
    data: { user_id: userId }
  })
}

/**
 * 根据用户ID列表查找或创建聊天会话
 * @param {Array<Number>} userIds - 用户ID数组
 * @returns {Promise}
 */
export async function findOrCreateChatWithUsers(userIds) {
  if (!userIds || userIds.length === 0) {
    throw new Error('No user IDs provided');
  }

  if (userIds.length === 1) {
    // 处理单人聊天
    return findOrCreateChat(userIds[0]);
  } else {
    // 处理多人聊天
    return createChatSession({ participants: userIds });
  }
}

/**
 * 清空所有聊天会话
 * @returns {Promise}
 */
export function clearAllChatSessions() {
  return request({
    url: '/api/chat/sessions/clear_all/',
    method: 'post'
  });
}

/**
 * 上传文件到会话中
 * @param {FormData} formData 包含文件和会话ID的表单数据
 * @returns {Promise}
 */
export function uploadFile(formData) {
  return request({
    url: '/api/chat/messages/',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

export function getChatMessages(chatId, page = 1, pageSize = 20) {
  return request({
    url: `/api/chat/messages/`,
    method: 'get',
    params: {
      chat: chatId,
      page,
      page_size: pageSize
    }
  });
}

// Summarize chat messages
export function summarizeChat(sessionId, startDate, endDate) {
  return request({
    url: `/api/chat/sessions/${sessionId}/summarize/`,
    method: 'post',
    data: {
      start_date: startDate,
      end_date: endDate
    }
  });
}

export function createChatMessage(data) {
  const formData = new FormData();
  for (const key in data) {
    if (data[key] !== null && data[key] !== undefined) {
      if (key === 'file' && data[key] instanceof File) {
        formData.append(key, data[key], data[key].name);
      } else {
        formData.append(key, data[key]);
      }
    }
  }

  return request({
    url: '/api/chat/messages/',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

/**
 * Analyzes text content to extract calendar event information.
 * @param {String} content - The text content to analyze.
 */
export function analyzeForCalendar(content) {
  return request({
    url: '/api/chat/analyze-for-calendar/',
    method: 'post',
    data: { content }
  });
}

/**
 * Creates a new calendar event.
 * @param {Object} eventData - The event data to create.
 */
export function createCalendarEvent(eventData) {
  return request({
    url: '/api/calendar/events/',
    method: 'post',
    data: eventData
  });
} 