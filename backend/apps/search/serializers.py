from rest_framework import serializers

class GlobalSearchResultSerializer(serializers.Serializer):
    """
    全局搜索结果的统一序列化器
    """
    type = serializers.CharField()          # 结果类型 (e.g., 'project', 'task', 'document')
    id = serializers.IntegerField()         # 对象ID
    title = serializers.CharField()         # 结果标题
    summary = serializers.CharField()       # 结果摘要或片段
    url = serializers.CharField()           # 前端跳转URL
    meta = serializers.DictField()          # 其他元数据 (e.g., created_at, creator) 