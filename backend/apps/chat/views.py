"""Views for the chat app."""

import os
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import ChatSession, ChatParticipant, ChatMessage, ChatMessageRead
from .serializers import (
    ChatSessionSerializer, 
    ChatSessionDetailSerializer,
    ChatSessionCreateSerializer,
    ChatMessageSerializer,
    ChatMessageCreateSerializer,
    ChatMessageReadSerializer,
    ChatParticipantSerializer
)
from rest_framework.exceptions import PermissionDenied, ValidationError
import logging
from .calendar_detection import detect_calendar_event, format_calendar_data
from rest_framework.views import APIView
from django.db.models import Count
from apps.users.models import User
from .ai_utils import summarize_text_with_langchain
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.knowledge.models import KnowledgeBase
from apps.knowledge.serializers import KnowledgeBaseSerializer

logger = logging.getLogger(__name__)

class ChatSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing chat sessions."""
    
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return chat sessions for the current user."""
        return ChatSession.objects.filter(
            participants__user=self.request.user
        ).distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'retrieve':
            return ChatSessionDetailSerializer
        elif self.action == 'create':
            return ChatSessionCreateSerializer
        return ChatSessionSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new chat session with standardized response format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # Use the standard serializer for the response
        response_serializer = ChatSessionSerializer(instance, context={'request': request})
        
        return Response({
            'success': True,
            'code': 201,
            'message': '聊天会话创建成功',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """Mark all messages as read when retrieving a chat."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Mark messages as read
        participant = get_object_or_404(
            ChatParticipant, 
            chat=instance, 
            user=request.user
        )
        participant.last_read = timezone.now()
        participant.save()
        
        # Create read receipts for unread messages
        unread_messages = instance.messages.exclude(
            sender=request.user
        ).exclude(
            read_receipts__user=request.user
        )
        
        for message in unread_messages:
            ChatMessageRead.objects.get_or_create(
                message=message,
                user=request.user
            )
        
        return Response({
            'success': True,
            'code': 200,
            'message': '获取聊天会话详情成功',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to a chat session."""
        chat = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': '必须提供用户ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the requester is an admin
        try:
            participant = ChatParticipant.objects.get(
                chat=chat,
                user=request.user
            )
            if not participant.is_admin and not chat.is_group:
                return Response(
                    {'error': '只有群聊管理员可以添加成员'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except ChatParticipant.DoesNotExist:
            return Response(
                {'error': '您不是此聊天的成员'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user already in chat
        if ChatParticipant.objects.filter(chat=chat, user_id=user_id).exists():
            return Response(
                {'error': '用户已经在聊天中'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add the user
        from apps.users.models import User
        try:
            user = User.objects.get(id=user_id)
            ChatParticipant.objects.create(
                chat=chat,
                user=user
            )
            return Response({'success': f'已添加用户 {user.username}'})
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a participant from a chat session."""
        chat = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': '必须提供用户ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the requester is an admin
        try:
            participant = ChatParticipant.objects.get(
                chat=chat,
                user=request.user
            )
            if not participant.is_admin and not chat.is_group:
                return Response(
                    {'error': '只有群聊管理员可以移除成员'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except ChatParticipant.DoesNotExist:
            return Response(
                {'error': '您不是此聊天的成员'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Cannot remove self if you're the only admin
        if int(user_id) == request.user.id:
            admin_count = chat.participants.filter(is_admin=True).count()
            if admin_count <= 1:
                return Response(
                    {'error': '您是唯一的管理员，无法退出群聊'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Remove the user
        try:
            participant = ChatParticipant.objects.get(chat=chat, user_id=user_id)
            username = participant.user.username
            participant.delete()
            return Response({'success': f'已移除用户 {username}'})
        except ChatParticipant.DoesNotExist:
            return Response(
                {'error': '用户不在此聊天中'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='summarize')
    def summarize(self, request, pk=None):
        """
        Summarize chat messages within a given time range.
        """
        chat_session = self.get_object()

        # Check if the user is a participant
        if not chat_session.participants.filter(user=request.user).exists():
            raise PermissionDenied("You are not a participant of this chat session.")

        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')

        if not start_date_str or not end_date_str:
            return Response(
                {'error': '必须提供开始和结束日期'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create aware datetime objects from the ISO strings (which are in UTC)
            aware_start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            aware_end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))

            # Convert the UTC datetimes to the server's local timezone
            local_start_date = timezone.localtime(aware_start_date)
            local_end_date = timezone.localtime(aware_end_date)

            # Since USE_TZ is False, the database stores naive local times.
            # We must query with naive datetime objects that represent the server's local time.
            start_date = local_start_date.replace(tzinfo=None)
            end_date = local_end_date.replace(tzinfo=None)

        except ValueError:
            return Response(
                {'error': '日期格式无效，请使用ISO 8601格式'},
                status=status.HTTP_400_BAD_REQUEST
            )

        messages = ChatMessage.objects.filter(
            chat=chat_session,
            created_at__range=(start_date, end_date)
        ).order_by('created_at')

        if not messages.exists():
            return Response(
                {'summary': '在选定时间范围内没有消息可供总结。'},
                status=status.HTTP_200_OK
            )

        # Format messages for summarization
        formatted_messages = "\n".join(
            [f"{msg.sender.username}: {msg.content}" for msg in messages]
        )

        try:
            summary = summarize_text_with_langchain(formatted_messages)
            return Response({'summary': summary}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.error(f"Error during summarization: {e}")
            return Response(
                {'error': '生成摘要时出错'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing chat messages."""
    
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """Return messages for chats the current user is part of."""
        return ChatMessage.objects.filter(
            chat__participants__user=self.request.user
        ).distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return ChatMessageCreateSerializer
        return ChatMessageSerializer
    
    def create(self, request, *args, **kwargs):
        """创建新消息"""
        try:
            print("接收到的消息数据:", request.data)
            print("接收到的文件数据:", request.FILES)
            
            serializer = ChatMessageCreateSerializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                chat_id = serializer.validated_data.get('chat')
                user = request.user
                
                if not ChatParticipant.objects.filter(chat=chat_id, user=user).exists():
                    return Response(
                        {'error': '您不是该聊天的参与者'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                if serializer.validated_data.get('message_type') == 'knowledge':
                    knowledge_id = serializer.validated_data.get('knowledge_id')
                    if not knowledge_id:
                        return Response(
                            {'error': '未提供知识库ID'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    try:
                        knowledge = KnowledgeBase.objects.get(id=knowledge_id)
                        serializer.validated_data['knowledge_detail'] = KnowledgeBaseSerializer(knowledge, context={'request': request}).data
                    except KnowledgeBase.DoesNotExist:
                        return Response(
                            {'error': '知识库文件不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )
                
                # 确保chat_files目录存在
                if serializer.validated_data.get('message_type') in ['file', 'image'] and 'file' in request.FILES:
                    import os
                    from django.conf import settings
                    upload_dir = os.path.join(settings.MEDIA_ROOT, 'chat_files')
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir)
                
                message = serializer.save(sender=request.user)
                
                response_serializer = ChatMessageSerializer(message, context={'request': request})
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
            else:
                print("序列化器验证失败:", serializer.errors)
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            import traceback
            print(f"发送消息时发生错误: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'发送消息失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        """Create a new message and check that the user is in the chat."""
        chat = serializer.validated_data['chat']
        
        if not ChatParticipant.objects.filter(chat=chat, user=self.request.user).exists():
            raise PermissionDenied("您不是此聊天的成员")
        
        serializer.save(sender=self.request.user)
        
        chat.updated_at = timezone.now()
        chat.save()
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a file attached to a message."""
        message = self.get_object()
        
        # Check if message has a file
        if not message.file:
            return Response(
                {'error': '此消息没有附件'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has access to the message
        if not ChatParticipant.objects.filter(
            chat=message.chat, 
            user=request.user
        ).exists():
            return Response(
                {'error': '您没有权限访问此文件'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Return the file
        file_path = message.file.path
        filename = os.path.basename(file_path)
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class FindOrCreateChatView(APIView):
    """
    Finds an existing one-on-one chat with a user or creates a new one.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if str(request.user.id) == str(user_id):
             return Response({'error': 'Cannot create a chat with yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'The specified user does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        # Find an existing one-on-one chat.
        # First, find chat IDs common to both the current user and the other user.
        user_chat_ids = set(ChatParticipant.objects.filter(user=request.user).values_list('chat_id', flat=True))
        other_user_chat_ids = set(ChatParticipant.objects.filter(user=other_user).values_list('chat_id', flat=True))
        common_chat_ids = user_chat_ids.intersection(other_user_chat_ids)

        chat_session = None
        if common_chat_ids:
            # Among the common chats, find one that is specifically a two-person, non-group chat.
            chat_session = ChatSession.objects.annotate(
                participant_count=Count('participants')
            ).filter(
                id__in=common_chat_ids,
                is_group=False,
                participant_count=2
            ).first()

        if chat_session:
            return Response({'chat_id': chat_session.id}, status=status.HTTP_200_OK)
        else:
            # If no such chat exists, create a new one atomically.
            with transaction.atomic():
                new_chat = ChatSession.objects.create(
                    title=f"{request.user.username}, {other_user.username}",
                    is_group=False
                )
                ChatParticipant.objects.create(chat=new_chat, user=request.user)
                ChatParticipant.objects.create(chat=new_chat, user=other_user)
            
            return Response({'chat_id': new_chat.id}, status=status.HTTP_201_CREATED)


class AnalyzeForCalendarView(APIView):
    """
    Analyzes text content for a calendar event.
    This is a standalone view to avoid URL conflicts with the message viewset.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        content = request.data.get('content')
        if not content:
            return Response({'error': 'Content is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event_info = detect_calendar_event(content)
            calendar_data = format_calendar_data(event_info)

            if not calendar_data:
                from datetime import datetime, timedelta
                now = datetime.now()
                one_hour_later = now + timedelta(hours=1)
                
                calendar_data = {
                    'title': '新日程',
                    'start': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'end': one_hour_later.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'blue',
                    'location': '',
                    'reminder': '30min',
                    'description': content[:500] if content else '',
                    'participants': [request.user.id]
                }
            else:
                # 确保所有必要的字段都存在
                calendar_data['participants'] = [request.user.id]
                
                # 确保location字段存在，但不要自动填充默认值
                if 'location' not in calendar_data:
                    calendar_data['location'] = ''
                
                # 确保reminder字段存在
                if 'reminder' not in calendar_data or not calendar_data['reminder']:
                    calendar_data['reminder'] = '30min'
            
            # 记录返回的数据，用于调试
            print("AI分析返回的日程数据:", calendar_data)
            
            return Response({'data': calendar_data})
        except Exception as e:
            logger.exception(f"Error during calendar analysis: {str(e)}")
            return Response({
                'error': f'Analyzing for calendar event failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatMessageReadViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for chat message read receipts."""
    
    serializer_class = ChatMessageReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return read receipts for messages the current user has read."""
        return ChatMessageRead.objects.filter(
            user=self.request.user
        ) 