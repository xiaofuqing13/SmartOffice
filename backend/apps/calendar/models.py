from django.db import models
from django.utils import timezone

class CalendarEvent(models.Model):
    """日历事件模型"""
    
    EVENT_TYPE_CHOICES = (
        ('blue', '会议'),
        ('orange', '出差'),
        ('green', '假期'),
        ('red', '截止日期'),
        ('purple', '其他'),
    )
    
    REMINDER_CHOICES = (
        ('none', '不提醒'),
        ('10min', '10分钟前'),
        ('30min', '30分钟前'),
        ('1hour', '1小时前'),
        ('1day', '1天前'),
    )
    
    title = models.CharField('标题', max_length=100)
    start = models.DateTimeField('开始时间')
    end = models.DateTimeField('结束时间')
    location = models.CharField('地点', max_length=100, blank=True, null=True)
    description = models.TextField('描述', blank=True, null=True)
    type = models.CharField('事件类型', max_length=20, choices=EVENT_TYPE_CHOICES, default='blue')
    reminder = models.CharField('提醒时间', max_length=20, choices=REMINDER_CHOICES, default='30min')
    creator = models.ForeignKey('users.User', verbose_name='创建者', on_delete=models.CASCADE, related_name='created_events')
    participants = models.ManyToManyField('users.User', verbose_name='参与者', related_name='events', blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '日历事件'
        verbose_name_plural = '日历事件列表'
        ordering = ['start']
    
    def __str__(self):
        return self.title 