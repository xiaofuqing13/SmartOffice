from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import Http404
from rest_framework.views import APIView

from .models import CalendarEvent
from .serializers import CalendarEventSerializer, CalendarEventCreateSerializer
from apps.ai.models import AIRecommendation
from apps.ai.services import check_and_generate_reminders


class CalendarEventViewSet(viewsets.ModelViewSet):
    """日历事件视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = CalendarEventSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'location', 'description']
    ordering_fields = ['start', 'end', 'created_at', 'updated_at']
    ordering = ['start']
    
    def get_queryset(self):
        """获取当前用户可见的日历事件"""
        user = self.request.user
        return CalendarEvent.objects.filter(participants=user).order_by('start')
    
    def get_serializer_class(self):
        """根据不同的操作选择不同的序列化器"""
        if self.action in ['create', 'update', 'partial_update']:
            return CalendarEventCreateSerializer
        return CalendarEventSerializer
    
    def list(self, request, *args, **kwargs):
        """获取所有日程事件"""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # 直接返回结果数组，不包含分页信息
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """获取单个日程事件详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """获取指定月份的事件"""
        try:
            year = int(request.query_params.get('year', None) or timezone.now().year)
            month = int(request.query_params.get('month', None) or timezone.now().month)
            if not (1 <= month <= 12):
                month = timezone.now().month
            if year < 1970 or year > 2100:
                year = timezone.now().year
        except (ValueError, TypeError):
            year = timezone.now().year
            month = timezone.now().month
        # 获取指定月份的开始和结束日期（去掉tzinfo）
        start_date = datetime(year, month, 1)
        # 计算下个月的第一天
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        # 结束日期是下个月的第一天减一秒
        end_date = next_month - timedelta(seconds=1)
        # 获取该月份的事件
        events = self.get_queryset().filter(
            start__gte=start_date,
            start__lte=end_date
        )
        serializer = self.get_serializer(events, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """获取指定周的事件"""
        try:
            date_str = request.query_params.get('date')
            if date_str:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date = timezone.now().date()
            # 获取所选日期所在周的周一
            start_date = date - timedelta(days=date.weekday())
            # 获取所选日期所在周的周日
            end_date = start_date + timedelta(days=6)
            # 转换为datetime（去掉tzinfo）
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            # 获取该周的事件
            events = self.get_queryset().filter(
                start__gte=start_datetime,
                start__lte=end_datetime
            )
            serializer = self.get_serializer(events, many=True)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except (ValueError, TypeError):
            return Response(
                {'success': False, 'error': '无效的日期参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def daily(self, request):
        """获取指定日期的事件"""
        try:
            date_str = request.query_params.get('date')
            if date_str:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date = timezone.now().date()
            # 转换为datetime（去掉tzinfo）
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())
            # 获取该日期的事件
            events = self.get_queryset().filter(
                start__gte=start_datetime,
                start__lte=end_datetime
            )
            serializer = self.get_serializer(events, many=True)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except (ValueError, TypeError):
            return Response(
                {'success': False, 'error': '无效的日期参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def create(self, request, *args, **kwargs):
        """创建日历事件"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # 获取创建的事件并使用详细序列化器返回
        instance = serializer.instance
        # 自动把创建者加入参与人
        instance.participants.add(request.user)
        
        # 对新创建的事件立即进行一次提醒检查
        try:
            check_and_generate_reminders(request.user, event_instance=instance)
        except Exception as e:
            print(f"[CalendarCreate] 提醒检查失败: {str(e)}")
            
        response_serializer = CalendarEventSerializer(instance)
        
        return Response({
            'success': True,
            'message': '日历事件创建成功',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """更新日历事件"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # 保存更新前的状态
        old_start = instance.start
        old_reminder = instance.reminder
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # 检查时间和提醒设置是否有变化
        if old_start != instance.start or old_reminder != instance.reminder:
            # 如果有变化，删除旧的AI提醒记录
            AIRecommendation.objects.filter(type='calendar', reference_id=instance.id).delete()
            print(f"[CalendarUpdate] 日程 '{instance.title}' (ID: {instance.id}) 的时间和提醒已变更，旧提醒已删除。")
            
            # 对更新后的事件立即进行一次提醒检查
            try:
                check_and_generate_reminders(request.user, event_instance=instance)
            except Exception as e:
                print(f"[CalendarUpdate] 提醒检查失败: {str(e)}")
        
        # 确保当前用户在参与人列表中
        if request.user not in instance.participants.all():
            instance.participants.add(request.user)
        
        # 使用详细序列化器返回
        response_serializer = CalendarEventSerializer(instance)
        
        return Response({
            'success': True,
            'message': '日历事件更新成功',
            'data': response_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """删除日历事件"""
        instance = self.get_object()
        self.perform_destroy(instance)
        # 删除关联的AI提醒
        AIRecommendation.objects.filter(type='calendar', reference_id=instance.id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 