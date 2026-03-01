"""Views for the users app."""

from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import uuid
import datetime
from django.db.models import Q

from .authentication import generate_jwt_token
from .models import User, PasswordResetToken, Company, Department, Contact
from .serializers import (
    UserSerializer, 
    UserDetailSerializer, 
    UserCreateSerializer,
    LoginSerializer, 
    PasswordResetRequestSerializer,
    PasswordResetSerializer,
    PasswordChangeSerializer,
    CompanySerializer,
    DepartmentSerializer,
    ContactSerializer,
    UserSimpleSerializer
)


class RegisterView(APIView):
    """API view for registering a new user."""
    
    authentication_classes = []  # 显式指定不需要认证
    permission_classes = [AllowAny]  # 显式指定允许所有用户访问
    
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Handle POST requests for creating a new user."""
        print("接收到注册请求:", request.data)  # 调试日志
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            return Response({
                'success': True,
                'message': '注册成功',
                'data': {
                    'userId': str(user.id),
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': '用户名或邮箱已被注册',
            'code': 40001
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """API view for user login."""
    
    authentication_classes = []  # 显式指定不需要认证
    permission_classes = [AllowAny]  # 显式指定允许所有用户访问
    
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Handle POST requests for user login."""
        print("接收到登录请求:", request.data)  # 调试日志
        username = request.data.get('username')
        password = request.data.get('password')
        remember = request.data.get('remember', 'false').lower() == 'true'
        
        if '@' in username:
            # 用户使用邮箱登录
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(email=user_obj.email, password=password)
            except User.DoesNotExist:
                user = None
        else:
            # 用户使用用户名登录
            try:
                user_obj = User.objects.get(username=username)
                user = authenticate(email=user_obj.email, password=password)
            except User.DoesNotExist:
                user = None
        
        if user:
            # 更新最后登录时间
            user.last_login = timezone.now()
            user.save()
            
            # 生成JWT令牌，如果remember为True，设置更长的过期时间
            token_expiry = 30 if remember else 1  # 30天或1天
            token = generate_jwt_token(user.id, days=token_expiry)
            
            return Response({
                'success': True,
                'message': '登录成功',
                'data': {
                    'userId': str(user.id),
                    'username': user.username,
                    'token': token,
                    'tokenType': 'Bearer',
                    'expiresIn': token_expiry * 24 * 3600  # 转换为秒
                }
            })
        else:
            return Response({
                'success': False,
                'message': '用户名或密码错误',
                'code': 40101
            }, status=status.HTTP_401_UNAUTHORIZED)


class AdminLoginView(APIView):
    """API view for admin login."""
    
    authentication_classes = []
    permission_classes = [AllowAny]
    
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Handle POST requests for admin login."""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(email=user_obj.email, password=password)
            except User.DoesNotExist:
                user = None
        else:
            try:
                user_obj = User.objects.get(username=username)
                user = authenticate(email=user_obj.email, password=password)
            except User.DoesNotExist:
                user = None
        
        if user and user.is_staff:
            user.last_login = timezone.now()
            user.save()
            
            token = generate_jwt_token(user.id, days=1)
            
            return Response({
                'success': True,
                'message': '登录成功',
                'data': {
                    'userId': str(user.id),
                    'username': user.username,
                    'token': token,
                    'tokenType': 'Bearer',
                    'expiresIn': 1 * 24 * 3600
                }
            })
        elif user and not user.is_staff:
            return Response({
                'success': False,
                'message': '该用户不是管理员',
                'code': 40301
            }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                'success': False,
                'message': '用户名或密码错误',
                'code': 40101
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """API view for user logout."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle POST requests for user logout."""
        logout(request)
        return Response({
            'success': True,
            'message': '登出成功'
        })


class PasswordResetRequestView(APIView):
    """API view for requesting a password reset."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle POST requests for requesting a password reset."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # 生成重置令牌
                token = str(uuid.uuid4())
                expires_at = timezone.now() + datetime.timedelta(hours=24)
                
                # 保存令牌
                PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )
                
                # 在实际环境中，这里应该发送邮件，包含重置链接
                # 例如：f"{settings.FRONTEND_URL}/reset-password?token={token}"
                
                return Response({
                    'success': True,
                    'message': '密码重置邮件已发送，请检查您的邮箱'
                })
            except User.DoesNotExist:
                # 即使用户不存在也返回成功，避免暴露用户信息
                return Response({
                    'success': True,
                    'message': '密码重置邮件已发送，请检查您的邮箱'
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """API view for resetting a password."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle POST requests for resetting a password."""
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['newPassword']
            
            try:
                # 查找有效的令牌
                reset_token = PasswordResetToken.objects.get(
                    token=token,
                    expires_at__gt=timezone.now(),
                    used=False
                )
                
                # 更新用户密码
                user = reset_token.user
                user.set_password(new_password)
                user.save()
                
                # 标记令牌为已使用
                reset_token.used = True
                reset_token.save()
                
                return Response({
                    'success': True,
                    'message': '密码重置成功'
                })
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'success': False,
                    'message': '无效或已过期的重置令牌',
                    'code': 40102
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing User instances."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['retrieve', 'me', 'update', 'partial_update']:
            return UserDetailSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Returns the authenticated user's details.
        """
        serializer = self.get_serializer(request.user)
        return Response({
            'success': True,
            'code': 200,
            'message': '获取用户信息成功',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change the authenticated user's password.
        """
        user = request.user
        serializer = PasswordChangeSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            old_password = serializer.validated_data['old_password']
            if not user.check_password(old_password):
                return Response({
                    'old_password': ['Incorrect password.']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({'message': 'Password updated successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def avatar(self, request, pk=None):
        """
        Upload avatar for a user.
        """
        user = self.get_object()
        
        # 检查权限：只允许用户上传自己的头像
        if request.user.id != user.id and not request.user.is_staff:
            return Response({
                'success': False,
                'message': '您无权更新其他用户的头像',
                'code': 40003
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 处理头像文件
        avatar_file = request.FILES.get('avatar')
        if not avatar_file:
            return Response({
                'success': False,
                'message': '未提供头像文件',
                'code': 40001
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 保存头像
        try:
            user.avatar = avatar_file
            user.save()
            serializer = self.get_serializer(user)
            return Response({
                'success': True,
                'message': '头像上传成功',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'头像上传失败: {str(e)}',
                'code': 50001
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing Company instances."""
    
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'simple_list', 'company_details']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def simple_list(self, request):
        """Return a simplified list of all companies (id and name only)."""
        companies = Company.objects.all()
        data = [{'id': company.id, 'name': company.name} for company in companies]
        return Response({
            'success': True,
            'data': data
        })
    
    @action(detail=True, methods=['get'])
    def company_details(self, request, pk=None):
        """Return company details including departments structure."""
        try:
            company = self.get_object()
            company_data = CompanySerializer(company).data
            
            # 获取公司所有部门
            departments = Department.objects.filter(company=company)
            departments_data = DepartmentSerializer(departments, many=True).data
            
            # 计算每个部门的人数
            for dept in departments_data:
                dept['count'] = User.objects.filter(department_id=dept['id']).count()
            
            return Response({
                'success': True,
                'data': {
                    'company': company_data,
                    'departments': departments_data
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e),
                'code': 40001
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def current_user_company(self, request):
        """返回当前登录用户所属公司的详细信息"""
        try:
            user = request.user
            if not user.company:
                return Response({
                    'success': False,
                    'message': '当前用户没有关联任何公司',
                    'code': 40001
                }, status=status.HTTP_400_BAD_REQUEST)
                
            company = user.company
            company_data = CompanySerializer(company).data
            
            # 获取公司所有部门
            departments = Department.objects.filter(company=company)
            departments_data = DepartmentSerializer(departments, many=True).data
            
            # 计算每个部门的人数
            for dept in departments_data:
                dept['count'] = User.objects.filter(department_id=dept['id']).count()
            
            # 计算公司总员工数
            total_employee_count = User.objects.filter(company=company).count()
            
            return Response({
                'success': True,
                'data': {
                    'company': company_data,
                    'departments': departments_data,
                    'total_employee_count': total_employee_count
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e),
                'code': 40001
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        company = self.get_object()
        users = company.users.all()
        return Response(UserSimpleSerializer(users, many=True).data)


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing Department instances."""
    
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optionally restricts the returned departments to a given company."""
        queryset = Department.objects.all()
        company_id = self.request.query_params.get('company', None)
        if company_id is not None:
            queryset = queryset.filter(company_id=company_id)
        return queryset
    
    @action(detail=False, methods=['get'])
    def company_departments(self, request):
        """Return departments for a specific company."""
        company_id = request.query_params.get('company_id', None)
        if company_id:
            departments = Department.objects.filter(company_id=company_id)
            serializer = self.get_serializer(departments, many=True)
            return Response({
                'success': True,
                'data': serializer.data
            })
        return Response({
            'success': False,
            'message': '未提供公司ID',
            'code': 40001
        }, status=status.HTTP_400_BAD_REQUEST)


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing Contact instances."""
    
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """从User表获取联系人数据，而不是Contact表"""
        # 首先获取请求中的参数
        company_id = self.request.query_params.get('company', None)
        department_id = self.request.query_params.get('department', None)
        search_query = self.request.query_params.get('search', None)
        
        # 从User表中查询数据
        queryset = User.objects.all()
        
        # 筛选指定公司的用户
        if company_id:
            try:
                company_id = int(company_id)
                queryset = queryset.filter(company_id=company_id)
                print(f"按公司ID {company_id} 筛选用户，找到 {queryset.count()} 个用户")
            except ValueError:
                print(f"无效的公司ID: {company_id}")
                queryset = User.objects.none()  # 返回空查询集
        
        # 筛选指定部门的用户
        if department_id:
            try:
                department_id = int(department_id)
                queryset = queryset.filter(department_id=department_id)
                print(f"按部门ID {department_id} 筛选用户，找到 {queryset.count()} 个用户")
            except ValueError:
                print(f"无效的部门ID: {department_id}")
        
        # 搜索用户
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
            print(f"按关键词 '{search_query}' 搜索用户，找到 {queryset.count()} 个结果")
        
        # 将User对象转换为Contact对象
        # 这是为了与前端期望的响应格式保持一致
        contact_list = []
        for user in queryset:
            # 获取员工编号（在公司中的创建顺序）
            employee_id = None
            if user.company:
                employee_id = f"EMP{User.objects.filter(company=user.company, date_joined__lt=user.date_joined).count() + 1:04d}"
            
            # 获取直系领导（部门经理）
            manager_name = None
            if user.department and user.department.manager:
                manager_name = user.department.manager.name or user.department.manager.username
            
            # 创建一个虚拟的Contact对象
            contact = Contact(
                id=user.id,
                name=user.name or user.username,
                position=user.position,
                department=user.department,
                company=user.company,
                email=user.email,
                mobile=user.phone,
                employee_id=employee_id,
                manager=manager_name,
                user=user
            )
            # 手动设置bio属性，而不是在构造函数中传递
            if hasattr(user, 'bio') and user.bio:
                contact.bio = user.bio
            
            contact_list.append(contact)
        
        return contact_list
    
    def list(self, request, *args, **kwargs):
        """自定义列表响应格式"""
        contacts = self.get_queryset()
        
        # 由于get_queryset返回的是对象列表而不是QuerySet，需要手动序列化
        serializer = self.get_serializer(contacts, many=True)
        
        return Response({
            'success': True,
            'code': 200,
            'message': '获取联系人列表成功',
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """自定义详情响应格式"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'code': 200,
            'message': '获取联系人详情成功',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """禁用创建联系人功能"""
        return Response({
            'success': False,
            'code': 403,
            'message': '添加联系人功能已禁用',
            'data': None
        }, status=status.HTTP_403_FORBIDDEN)
    
    def update(self, request, *args, **kwargs):
        """自定义更新响应格式"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'code': 200,
            'message': '更新联系人成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """自定义删除响应格式"""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return Response({
            'success': True,
            'code': 200,
            'message': '删除联系人成功',
            'data': None
        })
    
    @action(detail=False, methods=['get'])
    def department_contacts(self, request):
        """返回特定部门的用户列表作为联系人"""
        department_id = request.query_params.get('department_id', None)
        if department_id:
            try:
                department_id = int(department_id)
                # 从User表中获取特定部门的用户
                users = User.objects.filter(department_id=department_id)
                
                # 将User对象转换为Contact对象
                contact_list = []
                for user in users:
                    # 获取员工编号（在公司中的创建顺序）
                    employee_id = None
                    if user.company:
                        employee_id = f"EMP{User.objects.filter(company=user.company, date_joined__lt=user.date_joined).count() + 1:04d}"
                    
                    # 获取直系领导（部门经理）
                    manager_name = None
                    if user.department and user.department.manager:
                        manager_name = user.department.manager.name or user.department.manager.username
                    
                    # 创建一个虚拟的Contact对象
                    contact = Contact(
                        id=user.id,
                        name=user.name or user.username,
                        position=user.position,
                        department=user.department,
                        company=user.company,
                        email=user.email,
                        mobile=user.phone,
                        employee_id=employee_id,
                        manager=manager_name,
                        user=user
                    )
                    # 手动设置bio属性，而不是在构造函数中传递
                    if hasattr(user, 'bio') and user.bio:
                        contact.bio = user.bio
                    
                    contact_list.append(contact)
                
                serializer = self.get_serializer(contact_list, many=True)
                
                # 添加调试日志
                print(f"通过department_contacts获取部门ID {department_id} 的用户:")
                print(f"找到 {users.count()} 个用户")
                
                return Response({
                    'success': True,
                    'code': 200,
                    'message': '获取部门联系人列表成功',
                    'data': serializer.data
                })
            except ValueError:
                # 处理无效的部门ID
                print(f"无效的部门ID: {department_id}")
                return Response({
                    'success': False,
                    'code': 400,
                    'message': '提供的部门ID无效',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'success': False,
            'code': 400,
            'message': '未提供部门ID',
            'data': None
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def company_contacts(self, request):
        """返回特定公司的用户列表作为联系人"""
        company_id = request.query_params.get('company_id', None)
        if company_id:
            try:
                company_id = int(company_id)
                # 从User表中获取特定公司的用户
                users = User.objects.filter(company_id=company_id)
                
                # 将User对象转换为Contact对象
                contact_list = []
                for user in users:
                    # 获取员工编号（在公司中的创建顺序）
                    employee_id = None
                    if user.company:
                        employee_id = f"EMP{User.objects.filter(company=user.company, date_joined__lt=user.date_joined).count() + 1:04d}"
                    
                    # 获取直系领导（部门经理）
                    manager_name = None
                    if user.department and user.department.manager:
                        manager_name = user.department.manager.name or user.department.manager.username
                    
                    # 创建一个虚拟的Contact对象
                    contact = Contact(
                        id=user.id,
                        name=user.name or user.username,
                        position=user.position,
                        department=user.department,
                        company=user.company,
                        email=user.email,
                        mobile=user.phone,
                        employee_id=employee_id,
                        manager=manager_name,
                        user=user
                    )
                    # 手动设置bio属性，而不是在构造函数中传递
                    if hasattr(user, 'bio') and user.bio:
                        contact.bio = user.bio
                    
                    contact_list.append(contact)
                
                serializer = self.get_serializer(contact_list, many=True)
                
                # 添加调试日志
                print(f"通过company_contacts获取公司ID {company_id} 的用户:")
                print(f"找到 {users.count()} 个用户")
                
                return Response({
                    'success': True,
                    'code': 200,
                    'message': '获取公司联系人列表成功',
                    'data': serializer.data
                })
            except ValueError:
                # 处理无效的公司ID
                print(f"无效的公司ID: {company_id}")
                return Response({
                    'success': False,
                    'code': 400,
                    'message': '提供的公司ID无效',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'success': False,
            'code': 400,
            'message': '未提供公司ID',
            'data': None
        }, status=status.HTTP_400_BAD_REQUEST) 