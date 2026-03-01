"""Views for the AI app."""

from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
import threading
import json
import logging

from .models import AIChat, AIChatMessage, AIRecommendation, Document, DocumentChunk
from .serializers import (
    AIChatSerializer, 
    AIChatListSerializer,
    AIChatCreateSerializer,
    AIChatMessageSerializer,
    AIMessageCreateSerializer,
    AIRecommendationSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    ContentGenerationRequestSerializer,
    ContentGenerationResponseSerializer,
    DocumentUploadSerializer,
    DocumentSerializer,
    DocumentChunkSerializer,
    DocumentSearchRequestSerializer,
    DocumentSearchResponseSerializer,
    ChatWithDocumentsRequestSerializer
)
from .services import LangChainAssistant, DocumentProcessor, run_graphrag_query_stream, check_and_generate_reminders
from apps.calendar.models import CalendarEvent
from django.utils import timezone
from datetime import timedelta, datetime
from apps.knowledge.views import GraphRAGQueryView

logger = logging.getLogger(__name__)


class AIChatViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing AIChat instances."""
    
    serializer_class = AIChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        """Return chats for the current user."""
        return AIChat.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'list':
            return AIChatListSerializer
        if self.action == 'create':
            return AIChatCreateSerializer
        return AIChatSerializer
    
    def perform_create(self, serializer):
        """Create a new chat."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Return messages for a specific chat."""
        chat = self.get_object()
        messages = chat.messages.all()
        serializer = AIChatMessageSerializer(messages, many=True)
        return Response(serializer.data)


class AIChatMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing AIChatMessage instances."""
    
    serializer_class = AIChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return messages for chats owned by the current user."""
        return AIChatMessage.objects.filter(chat__user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return AIMessageCreateSerializer
        return AIChatMessageSerializer
    
    def perform_create(self, serializer):
        """Create a new message and check that the user owns the chat."""
        chat = serializer.validated_data['chat']
        if chat.user != self.request.user:
            return Response(
                {'detail': 'You do not have permission to add messages to this chat.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()


class AIRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing AIRecommendation instances."""
    
    serializer_class = AIRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return recommendations for the current user."""
        return AIRecommendation.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a recommendation as read."""
        recommendation = self.get_object()
        recommendation.is_read = True
        recommendation.save()
        return Response({'status': 'recommendation marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all recommendations as read."""
        recommendations = self.get_queryset().filter(is_read=False)
        recommendations.update(is_read=True)
        return Response({'status': 'all recommendations marked as read'})


class ChatAPIView(APIView):
    """API view for chatting with the AI assistant."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Handle POST requests for AI chat."""
        serializer = ChatRequestSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data['message']
            chat_id = serializer.validated_data.get('chat_id')
            
            # 获取或创建聊天
            if chat_id:
                try:
                    chat = AIChat.objects.get(id=chat_id, user=request.user)
                except AIChat.DoesNotExist:
                    return Response(
                        {'detail': 'Chat not found.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # For new chats, create a placeholder title.
                # The real title will be generated by the serializer if it's empty.
                chat = AIChat.objects.create(user=request.user, title="")
            
            # 保存用户消息
            user_message = AIChatMessage.objects.create(
                chat=chat,
                role=AIChatMessage.MessageRole.USER,
                content=message
            )
            
            # 获取聊天历史
            messages = []
            for msg in chat.messages.all().order_by('created_at'):
                messages.append({
                    'role': msg.role,
                    'content': msg.content
                })
            
            # 用LangChainAssistant拼接历史
            prompt = '\n'.join([f"{m['role']}: {m['content']}" for m in messages])
            ai_assistant = LangChainAssistant()
            ai_response = ai_assistant.chat(prompt)
            
            # 保存AI回复
            assistant_message = AIChatMessage.objects.create(
                chat=chat,
                role=AIChatMessage.MessageRole.ASSISTANT,
                content=ai_response
            )
            
            # 更新聊天时间
            chat.save()  # 更新updated_at时间戳
            
            # 返回响应
            response_serializer = ChatResponseSerializer({
                'message': ai_response,
                'chat_id': chat.id
            })
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContentGenerationAPIView(APIView):
    """API view for generating content with AI."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Handle POST requests for content generation."""
        serializer = ContentGenerationRequestSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data['prompt']
            context = serializer.validated_data.get('context', '')
            content_type = serializer.validated_data.get('content_type', 'text')
            
            # 用LangChainAssistant生成内容
            ai_assistant = LangChainAssistant()
            full_prompt = f"类型:{content_type}\n上下文:{context}\n用户要求:{prompt}"
            generated_content = ai_assistant.chat(full_prompt)
            
            # 返回响应
            response_serializer = ContentGenerationResponseSerializer({
                'content': generated_content
            })
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 


class ScheduleReminderAPIView(APIView):
    """AI主动日程提醒API，基于LangChain分析日程并生成提醒。"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            reminders = check_and_generate_reminders(request.user)
            # 返回前只保留未读提醒
            if not reminders:
                return Response({'success': True, 'data': []})

            unread_reminders = [r for r in reminders if not AIRecommendation.objects.get(id=r['recommendation_id']).is_read]
            print(f"[AI提醒] 返回未读提醒数量: {len(unread_reminders)}")
            return Response({'success': True, 'data': unread_reminders})
        except Exception as e:
            print(f"[AI提醒] API处理过程出现错误: {str(e)}")
            import traceback
            traceback.print_exc()
            # 返回错误但不中断服务
            return Response({
                'success': False,
                'error': '获取日程提醒时出错',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentViewSet(viewsets.ModelViewSet):
    """文档管理视图集."""
    
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """返回当前用户的文档."""
        return Document.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """返回适当的序列化器类."""
        if self.action == 'upload':
            return DocumentUploadSerializer
        return DocumentSerializer
    
    def perform_create(self, serializer):
        """创建新文档（异步处理，前端会轮询状态）."""
        # 默认情况下，DRF的ModelViewSet会处理创建
        # 但我们通过'upload' action自定义了该过程
        pass

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """处理文档上传并触发后台处理."""
        serializer = DocumentUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # 序列化器现在会处理创建和字段填充，所以save()不需要额外参数
            document = serializer.save()
            
            # 使用DocumentProcessor在后台线程中处理文档
            processor = DocumentProcessor()
            thread = threading.Thread(target=processor.process_document, args=(document.id,))
            thread.daemon = True
            thread.start()
            
            # 返回文档信息和接受状态
            response_serializer = DocumentSerializer(document)
            return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        """获取文档的分块内容."""
        document = self.get_object()
        chunks = document.chunks.all()
        serializer = DocumentChunkSerializer(chunks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """重新处理文档."""
        document = self.get_object()
        
        # 启动后台线程进行处理
        processor = DocumentProcessor()
        thread = threading.Thread(target=processor.process_document, args=(document.id,))
        thread.daemon = True
        thread.start()
        
        document.status = 'processing'
        document.save()

        return Response(
            {'status': 'reprocessing_started', 'message': '文档正在后台重新处理...'},
            status=status.HTTP_202_ACCEPTED
        )


class DocumentSearchAPIView(APIView):
    """文档搜索API."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """处理文档搜索请求."""
        serializer = DocumentSearchRequestSerializer(data=request.data)
        if serializer.is_valid():
            query = serializer.validated_data['query']
            limit = serializer.validated_data.get('limit', 5)
            document_id = serializer.validated_data.get('document_id')
            
            # 使用文档处理器搜索
            processor = DocumentProcessor()
            
            # 如果指定了文档ID，只在该文档中搜索
            if document_id:
                try:
                    document = Document.objects.get(id=document_id, user=request.user)
                    # 这里应该优化为仅在特定文档中搜索，但当前简单实现使用过滤
                    all_results = processor.search_relevant_chunks(query, limit=limit*2)  # 多获取一些结果，后面过滤
                    results = [r for r in all_results if r['document_id'] == document_id][:limit]
                except Document.DoesNotExist:
                    return Response(
                        {'error': '文档不存在或无权访问'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # 搜索用户的所有文档
                results = processor.search_relevant_chunks(query, limit=limit)
            
            # 返回响应
            response_serializer = DocumentSearchResponseSerializer({
                'results': results
            })
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatWithDocumentsAPIView(APIView):
    """
    支持文档上下文的聊天API.
    该视图根据'chatMode'参数，在GraphRAG和LangChain之间进行分发。
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChatWithDocumentsRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        chat_mode = validated_data.get('chatMode', 'agent')
        
        # 根据chatMode分发到不同的处理器
        if chat_mode == 'knowledge_base':
            # 直接代理到GraphRAG查询视图
            graphrag_view = GraphRAGQueryView()
            return graphrag_view.post(request)

        # 默认或'agent'模式使用LangChain
        elif chat_mode == 'agent':
            message_content = validated_data.get('message')
            document_ids = validated_data.get('document_ids')
            chat_id = validated_data.get('chat_id')
            ai_settings = validated_data.get('ai_settings')  # 获取AI设置

            try:
                # 获取或创建聊天会话
                if chat_id:
                    chat = AIChat.objects.get(id=chat_id, user=request.user)
                else:
                    chat = AIChat.objects.create(user=request.user, title=message_content[:50] or "新对话")
                
                # 保存用户消息
                AIChatMessage.objects.create(
                    chat=chat, role='user', content=message_content,
                    metadata={'document_ids': document_ids} if document_ids else {}
                )
                
                # 准备消息历史
                history = []
                for msg in chat.messages.all().order_by('created_at'):
                    history.append({'role': msg.role, 'content': msg.content})

                # 定义事件流函数
                def event_stream():
                    ai_assistant = LangChainAssistant(user=request.user)
                    # 将document_ids和ai_settings传递给服务
                    stream_generator = ai_assistant.chat_with_tools_stream(history, document_ids=document_ids, ai_settings=ai_settings)
                    
                    assistant_response = ""
                    for chunk in stream_generator:
                        try:
                            # 尝试解析JSON
                            data = json.loads(chunk)
                            assistant_response += data.get("content", "")
                        except json.JSONDecodeError:
                            # 如果不是JSON，直接累加
                            assistant_response += chunk
                        
                        yield f"data: {chunk}\n\n"

                    # 流结束后保存AI的完整回复
                    if assistant_response:
                        AIChatMessage.objects.create(
                            chat=chat, role='assistant', content=assistant_response
                        )
                    
                    # 返回新会话ID（如果创建了）
                    yield f"data: {json.dumps({'type': 'session_id', 'chat_id': str(chat.id)})}\n\n"

                # 返回流式响应
                response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
                response['X-Accel-Buffering'] = 'no' # For Nginx
                response['Cache-Control'] = 'no-cache'
                return response

            except AIChat.DoesNotExist:
                return Response({"error": "Chat not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"处理文档聊天时出错: {e}", exc_info=True)
                return Response({"error": f"An unexpected error occurred: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            return Response({"error": f"Invalid chat mode: {chat_mode}"}, status=status.HTTP_400_BAD_REQUEST)