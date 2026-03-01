from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UIPreference, AISetting
from .serializers import UIPreferenceSerializer, AISettingSerializer


class UIPreferenceAPIView(APIView):
    """界面偏好设置API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取当前用户的界面偏好设置"""
        try:
            preference, created = UIPreference.objects.get_or_create(user=request.user)
            serializer = UIPreferenceSerializer(preference)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'获取设置失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """更新当前用户的界面偏好设置"""
        try:
            preference, created = UIPreference.objects.get_or_create(user=request.user)
            serializer = UIPreferenceSerializer(preference, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'message': '设置更新成功'
                })
            else:
                return Response({
                    'success': False,
                    'message': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'保存设置失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AISettingAPIView(APIView):
    """个性化AI设置API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取当前用户的个性化AI设置"""
        try:
            setting, created = AISetting.objects.get_or_create(user=request.user)
            serializer = AISettingSerializer(setting)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'获取AI设置失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """更新当前用户的个性化AI设置"""
        try:
            setting, created = AISetting.objects.get_or_create(user=request.user)
            serializer = AISettingSerializer(setting, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'message': '个性化AI设置更新成功'
                })
            else:
                return Response({
                    'success': False,
                    'message': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'保存AI设置失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 