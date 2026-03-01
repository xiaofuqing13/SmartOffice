import { createRouter, createWebHistory } from 'vue-router'

// 路由懒加载处理，添加错误处理
const lazyLoad = (componentPath) => {
  return () => {
    return new Promise((resolve) => {
      try {
        const component = import(`../views/${componentPath}.vue`);
        resolve(component);
      } catch (error) {
        // 避免使用console.error，改为兼容ESLint的写法
        // eslint-disable-next-line no-console
        console.error(`路由加载失败: ${componentPath}`, error);
        // 返回一个简单的错误页面组件
        resolve({
          template: `<div class="error-page">
            <div style="text-align: center; padding: 100px 20px;">
              <h2 style="color: #f56c6c;">页面加载失败</h2>
              <p>抱歉，无法加载请求的页面: ${componentPath}</p>
              <button @click="$router.push('/')" 
                style="padding: 10px 20px; background: #409eff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                返回首页
              </button>
            </div>
          </div>`
        });
      }
    });
  };
};

// 路由懒加载 - 只保留已实现的组件
const Login = lazyLoad('auth/Login')
const Register = lazyLoad('auth/Register')
const AdminLogin = lazyLoad('admin/Login')
const AdminLayout = lazyLoad('admin/Layout')
const AdminDashboard = lazyLoad('admin/Dashboard')
const UserManagement = lazyLoad('admin/UserManagement')
const CompanyManagement = lazyLoad('admin/CompanyManagement')
const DepartmentManagement = lazyLoad('admin/DepartmentManagement')
const SmartDocManagement = lazyLoad('admin/SmartDocManagement')
const ContractManagement = lazyLoad('admin/ContractManagement')
const ContractTemplateManagement = lazyLoad('admin/ContractTemplateManagement')
const ContractTemplateEdit = lazyLoad('admin/ContractTemplateEdit')
const KnowledgeManagement = lazyLoad('admin/KnowledgeManagement')
const Layout = lazyLoad('layout/Index')
const Dashboard = lazyLoad('dashboard/Index')
const Calendar = lazyLoad('calendar/Index')
const Knowledge = lazyLoad('knowledge/Index')
const Chat = lazyLoad('chat/Index')
const Contract = lazyLoad('contract/Index')
const ContractDetail = lazyLoad('contract/Detail')
const Contact = lazyLoad('contact/Index')
const Project = lazyLoad('project/Index')
const ProjectDetail = lazyLoad('project/ProjectDetail')
const Company = lazyLoad('company/Index')
const Profile = lazyLoad('profile/Index')
const SmartDoc = lazyLoad('smartdoc/Index')
const SmartDocDetail = lazyLoad('smartdoc/Detail')

const routes = [
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: AdminLogin,
    meta: { title: '管理员登录', requiresAuth: false }
  },
  {
    path: '/admin',
    component: AdminLayout,
    redirect: '/admin/dashboard',
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: AdminDashboard,
        meta: { title: '仪表盘' }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: UserManagement,
        meta: { title: '用户管理' }
      },
      {
        path: 'companies',
        name: 'CompanyManagement',
        component: CompanyManagement,
        meta: { title: '公司管理' }
      },
      {
        path: 'departments',
        name: 'DepartmentManagement',
        component: DepartmentManagement,
        meta: { title: '部门管理' }
      },
      {
        path: 'smart-docs',
        name: 'SmartDocManagement',
        component: SmartDocManagement,
        meta: { title: '智能文档管理' }
      },
      {
        path: 'contracts',
        name: 'AdminContractManagement',
        component: ContractManagement,
        meta: { title: '合同管理' }
      },
      {
        path: 'contract-templates',
        name: 'AdminContractTemplateManagement',
        component: ContractTemplateManagement,
        meta: { title: '合同模板管理' }
      },
      {
        path: 'contract-templates/new',
        name: 'AdminContractTemplateNew',
        component: ContractTemplateEdit,
        meta: { title: '新建合同模板' }
      },
      {
        path: 'contract-templates/edit/:id',
        name: 'AdminContractTemplateEdit',
        component: ContractTemplateEdit,
        meta: { title: '编辑合同模板' },
        props: true
      },
      {
        path: 'knowledge',
        name: 'KnowledgeManagement',
        component: KnowledgeManagement,
        meta: { title: '知识库管理' }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { title: '注册', requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '工作中心', icon: 'bi-grid-1x2' }
      },
      {
        path: 'calendar',
        name: 'Calendar',
        component: Calendar,
        meta: { title: '日程安排', icon: 'bi-calendar-week' }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: Knowledge,
        meta: { title: '企业知识库', icon: 'bi-book' }
      },
      {
        path: 'chat',
        name: 'Chat',
        component: Chat,
        meta: { title: '即时沟通', icon: 'bi-chat-dots' }
      },
      {
        path: 'smartdoc',
        name: 'SmartDoc',
        component: SmartDoc,
        meta: { title: '文档处理', icon: 'bi-file-earmark-text' },
      },
      {
        path: 'smartdoc/:id',
        name: 'SmartDocDetail',
        component: SmartDocDetail,
        meta: { title: '文档详情', icon: 'bi-file-earmark-text' },
        hidden: true,
        props: true,
        beforeEnter: (to, from, next) => {
          // 验证ID是否有效
          const id = to.params.id
          if (!id || isNaN(id)) {
            next({ name: 'SmartDoc' })
          } else {
            next()
          }
        }
      },
      {
        path: 'contract',
        name: 'Contract',
        component: Contract,
        meta: { title: '智能合同', icon: 'bi-file-earmark-ruled' }
      },
      {
        path: 'contract/:id',
        name: 'ContractDetail',
        component: ContractDetail,
        meta: { title: '合同详情', icon: 'bi-file-earmark-ruled' },
        hidden: true,
        beforeEnter: (to, from, next) => {
          // 验证ID是否为有效数字
          const id = to.params.id
          if (!id || id === 'contract' || isNaN(id)) {
            next({ name: 'Contract' })
          } else {
            next()
          }
        }
      },
      {
        path: 'contact',
        name: 'Contact',
        component: Contact,
        meta: { title: '企业通讯录', icon: 'bi-person-lines-fill' }
      },
      {
        path: 'project',
        name: 'Project',
        component: Project,
        meta: { title: '项目协作', icon: 'bi-kanban' }
      },
      {
        path: 'project/:id',
        name: 'ProjectDetail',
        component: ProjectDetail,
        meta: { title: '项目详情', icon: 'bi-kanban' },
        hidden: true,
        props: true,
        beforeEnter: (to, from, next) => {
          // 验证ID是否有效
          const id = to.params.id
          if (!id || isNaN(id)) {
            next({ name: 'Project' })
          } else {
            next()
          }
        }
      },
      {
        path: 'company',
        name: 'Company',
        component: Company,
        meta: { title: '企业信息', icon: 'bi-building' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: Profile,
        meta: { title: '个人中心', icon: 'bi-person' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫，处理页面标题和身份验证
router.beforeEach((to, from, next) => {
  // 设置标题
  document.title = to.meta.title ? `${to.meta.title} - 智能办公系统` : '智能办公系统'
  
  // 检查用户是否已登录
  const isAuthenticated = localStorage.getItem('token') !== null
  const user = JSON.parse(localStorage.getItem('user'));
  
  // 检查管理员路由
  if (to.matched.some(record => record.meta.requiresAdmin)) {
    if (!isAuthenticated || !user?.isAdmin) {
      // 如果需要管理员权限但用户未登录或不是管理员，重定向到管理员登录页
      next({ name: 'AdminLogin' });
      return;
    }
  }
  
  // 处理需要验证的路由
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!isAuthenticated) {
      next({ name: 'Login' });
      return;
    }
  }
  
  // 处理可能的smartdoc路径错误
  if (from.path.startsWith('/smartdoc/')) {
    const pathSegments = to.path.split('/');
    if (pathSegments.length > 2 && pathSegments[1] === 'smartdoc' && isNaN(pathSegments[2])) {
      // 修正错误路径
      const correctPath = '/' + pathSegments.slice(2).join('/');
      next({ path: correctPath, replace: true });
      return;
    }
  }
    
  // 正常导航
    next();
})

export default router 