<template>
  <div class="contact-container">
    <div class="contact-wrapper">
      <!-- 左侧部门导航 -->
      <div class="contact-sidebar">
        <el-card class="contacts-nav-card" v-loading="loading.departments" shadow="hover">
          <div class="search-box">
            <el-input 
              v-model="searchQuery" 
              placeholder="搜索联系人..."
              clearable
              prefix-icon="Search"
            ></el-input>
          </div>
          <div class="contacts-nav">
            <div 
              v-for="(dept, index) in departments" 
              :key="dept.id" 
              class="dept-item" 
              :class="{'active': selectedDept === index}"
              @click="selectedDept = index"
            >
              <el-icon><component :is="getDeptIcon(dept.icon)" /></el-icon>
              <span>{{ dept.name }}</span>
              <el-badge :value="dept.count || 0" type="info" class="dept-badge" />
            </div>
          </div>
        </el-card>
      </div>

      <!-- 中间联系人列表 -->
      <div class="contact-list">
        <el-card class="contacts-list-card" v-loading="loading.contacts" shadow="hover">
          <template #header>
            <div class="card-header-flex">
              <span class="header-title">{{ searchQuery ? '搜索结果' : departments[selectedDept]?.name }}</span>
              <span class="contact-count">{{ contacts.length }}人</span>
            </div>
          </template>
          <div class="contacts-list">
            <div v-if="searchQuery" class="search-info">
              <el-icon><InfoFilled /></el-icon>
              <span>搜索范围：全公司联系人</span>
            </div>
            <div v-else-if="selectedDept === 0" class="search-info">
              <el-icon><InfoFilled /></el-icon>
              <span>显示全部公司联系人</span>
            </div>
            <div 
              v-for="(contact, index) in contacts" 
              :key="contact.id" 
              class="contact-item" 
              :class="{'active': selectedContact === index}"
              @click="selectedContact = index"
            >
              <div class="contact-avatar" v-if="contact.avatar_url" style="background-color: transparent;">
                <img :src="contact.avatar_url" alt="头像" class="avatar-img" />
              </div>
              <div class="contact-avatar" v-else :style="getAvatarStyle(contact)">{{ getInitials(contact.name) }}</div>
              <div class="contact-info">
                <div class="contact-name">{{ contact.name }}</div>
                <div class="contact-position">{{ contact.position }} · {{ contact.department_name || '未分配部门' }}</div>
              </div>
            </div>
            <el-empty v-if="contacts.length === 0" description="暂无联系人数据"></el-empty>
          </div>
        </el-card>
      </div>

      <!-- 右侧联系人详情 -->
      <div class="contact-detail">
        <el-card v-if="selectedContact !== null && contacts[selectedContact]" class="contact-detail-card" shadow="hover">
          <div class="contact-header">
            <div class="detail-avatar" v-if="contacts[selectedContact].avatar_url" style="background-color: transparent;">
              <img :src="contacts[selectedContact].avatar_url" alt="头像" class="avatar-img" />
            </div>
            <div class="detail-avatar" v-else :style="getAvatarStyle(contacts[selectedContact])">
              {{ getInitials(contacts[selectedContact].name) }}
            </div>
            <div class="detail-info">
              <div class="detail-name">{{ contacts[selectedContact].name }}</div>
              <div class="detail-position">{{ contacts[selectedContact].position }}</div>
              <div class="detail-department">{{ contacts[selectedContact].department_name || '未分配部门' }}</div>
              <div class="contact-actions">
                <el-button type="primary" size="small" @click="startChat(contacts[selectedContact])">
                  <el-icon><ChatDotRound /></el-icon> 发送消息
                </el-button>
              </div>
            </div>
          </div>

          <el-divider />

          <div class="contact-sections">
            <div class="contact-section">
              <div class="section-title">
                <el-icon><Promotion /></el-icon> 联系方式
              </div>
              <div class="contact-grid">
                <div class="contact-item-box">
                  <div class="contact-item-icon"><el-icon><Iphone /></el-icon></div>
                  <div class="contact-item-content">
                    <div class="contact-item-label">手机号码</div>
                    <div class="contact-item-value">{{ contacts[selectedContact].mobile || '暂无' }}</div>
                  </div>
                </div>
                <div class="contact-item-box">
                  <div class="contact-item-icon"><el-icon><Message /></el-icon></div>
                  <div class="contact-item-content">
                    <div class="contact-item-label">电子邮箱</div>
                    <div class="contact-item-value">{{ contacts[selectedContact].email || '暂无' }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="contact-section">
              <div class="section-title">
                <el-icon><User /></el-icon> 个人信息
              </div>
              <div class="contact-grid">
                <div class="contact-item-box">
                  <div class="contact-item-icon"><el-icon><Ticket /></el-icon></div>
                  <div class="contact-item-content">
                    <div class="contact-item-label">员工编号</div>
                    <div class="contact-item-value">{{ contacts[selectedContact].employee_id || '暂无' }}</div>
                  </div>
                </div>
                <div class="contact-item-box">
                  <div class="contact-item-icon"><el-icon><UserFilled /></el-icon></div>
                  <div class="contact-item-content">
                    <div class="contact-item-label">直系领导</div>
                    <div class="contact-item-value">{{ contacts[selectedContact].manager || '暂无' }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 个人简介部分 -->
            <div class="contact-section">
              <div class="section-title">
                <el-icon><Document /></el-icon> 个人简介
              </div>
              <div class="bio-content">
                {{ contacts[selectedContact].bio || '暂无个人简介' }}
              </div>
            </div>

            <div class="contact-section" v-if="contacts[selectedContact].skills && contacts[selectedContact].skills.length > 0">
              <div class="section-title">
                <el-icon><Medal /></el-icon> 技能专长
              </div>
              <div class="skills-tags">
                <el-tag 
                  v-for="(skill, index) in contacts[selectedContact].skills" 
                  :key="index"
                  class="skill-tag"
                  effect="light"
                  round
                >
                  {{ skill }}
                </el-tag>
              </div>
            </div>

            <div class="contact-section" v-if="contacts[selectedContact].projects && contacts[selectedContact].projects.length > 0">
              <div class="section-title">
                <el-icon><SetUp /></el-icon> 管理项目
              </div>
              <el-table 
                :data="contacts[selectedContact].projects || []" 
                style="width: 100%"
                :border="false"
                size="small"
                stripe
              >
                <el-table-column prop="name" label="项目名称"></el-table-column>
                <el-table-column prop="role" label="担任角色"></el-table-column>
                <el-table-column prop="status" label="状态">
                  <template #default="scope">
                    <el-tag 
                      :type="scope.row.status === '进行中' ? 'primary' : scope.row.status === '已完成' ? 'success' : 'info'"
                      size="small"
                    >
                      {{ scope.row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-card>
        
        <el-empty v-else description="请选择一个联系人" :image-size="200"></el-empty>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { useRequest } from '@/hooks/useRequest'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { 
  Search, 
  InfoFilled, 
  ChatDotRound, 
  Iphone,
  User, 
  UserFilled, 
  Location, 
  Calendar, 
  Present, 
  Ticket, 
  Medal, 
  SetUp,
  Promotion,
  OfficeBuilding,
  Briefcase,
  House,
  PieChart,
  Money,
  Headset,
  Connection,
  More,
  Message,
  Document
} from '@element-plus/icons-vue'

export default {
  name: 'Contact',
  components: {
    Search, 
    InfoFilled, 
    ChatDotRound, 
    Iphone,
    User, 
    UserFilled, 
    Location, 
    Calendar, 
    Present, 
    Ticket, 
    Medal, 
    SetUp,
    Promotion,
    OfficeBuilding,
    Briefcase,
    House,
    PieChart,
    Money,
    Headset,
    Connection,
    More,
    Message,
    Document
  },
  setup() {
    // 状态定义
    const searchQuery = ref('')
    const selectedDept = ref(0)
    const selectedContact = ref(0)
    const departments = ref([
      { id: 0, name: '全部部门', icon: 'bi bi-building', count: 0 }
    ])
    const contacts = ref([])
    const loading = ref({
      departments: false,
      contacts: false
    })
    const currentUser = ref(null)
    const companyId = ref(null)
    
    // 路由
    const router = useRouter()

    // API请求
    const { request } = useRequest()

    // 获取部门图标
    const getDeptIcon = (iconClass) => {
      const iconMap = {
        'bi bi-building': 'House',
        'bi bi-people-fill': 'User',
        'bi bi-person-workspace': 'UserFilled',
        'bi bi-people': 'OfficeBuilding',
        'bi bi-cash-coin': 'Money',
        'bi bi-graph-up': 'PieChart',
        'bi bi-code-slash': 'Connection',
        'bi bi-box': 'Briefcase',
        'bi bi-headset': 'Headset',
        'bi bi-three-dots': 'More'
      }
      
      return iconMap[iconClass] || 'House'
    }
    
    // 生成头像样式
    const getAvatarStyle = (contact) => {
      if (!contact) return {}
      
      // 根据用户名生成一个固定的颜色
      const colors = [
        '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', 
        '#909399', '#3B71CA', '#14A44D', '#DC4C64',
        '#54B4D3', '#9FA6B2', '#3E4551', '#6610F2'
      ]
      
      let hash = 0
      if (contact.name) {
        for (let i = 0; i < contact.name.length; i++) {
          hash = contact.name.charCodeAt(i) + ((hash << 5) - hash)
        }
      }
      
      const colorIndex = Math.abs(hash) % colors.length
      return { backgroundColor: colors[colorIndex] }
    }

    // 获取当前用户信息
    const fetchCurrentUser = async () => {
      try {
        const res = await request('/api/auth/users/me/')
        console.log('获取用户信息响应:', res)
        
        // 检查不同的响应格式
        if (res && res.success && res.data) {
          // 标准格式：{success: true, data: {...}}
          currentUser.value = res.data
          companyId.value = res.data.company
          console.log('从标准格式中获取到公司ID:', companyId.value)
        } else if (res && res.code === 200 && res.data) {
          // 另一种格式：{code: 200, data: {...}}
          currentUser.value = res.data
          companyId.value = res.data.company
          console.log('从code=200格式中获取到公司ID:', companyId.value)
        } else if (res && typeof res === 'object') {
          // 直接返回数据对象的格式
          currentUser.value = res
          companyId.value = res.company
          console.log('从直接返回对象中获取到公司ID:', companyId.value)
        } else {
          console.error('无法解析用户信息响应:', res)
          ElMessage.warning('用户信息格式异常')
        }
          
          if (!companyId.value) {
          console.error('当前用户没有关联公司信息:', currentUser.value)
            ElMessage.warning('您的账号未关联任何公司，请联系管理员')
          }
          
        return currentUser.value
      } catch (error) {
        console.error('获取用户信息失败:', error)
        ElMessage.error('获取用户信息失败：' + (error.message || '未知错误'))
      }
      return null
    }

    // 获取部门列表
    const fetchDepartments = async () => {
      loading.value.departments = true
      try {
        if (!companyId.value) {
          console.error('未找到当前用户所属公司ID，无法加载部门列表')
          ElMessage.warning('无法加载部门列表：未找到您所属的公司')
          loading.value.departments = false
          return
        }
        
        console.log('开始获取公司部门，公司ID:', companyId.value)
        const res = await request(`/api/auth/companies/${companyId.value}/company_details/`)
        console.log('获取公司部门响应:', res)
        
        if (res && res.success && res.data) {
          // 计算所有联系人总数
          const totalContactsCount = await getTotalContactsCount()
          console.log('联系人总数:', totalContactsCount)
          
          // 添加全部部门选项
          const allDepts = [
            { 
              id: 0, 
              name: '全部联系人', 
              icon: 'bi bi-people-fill', 
              count: totalContactsCount
            }
          ]
          
          // 为每个部门添加图标
          const deptIcons = {
            '管理层': 'bi bi-person-workspace',
            '人事部': 'bi bi-people',
            '财务部': 'bi bi-cash-coin',
            '市场部': 'bi bi-graph-up',
            '技术部': 'bi bi-code-slash',
            '产品部': 'bi bi-box',
            '客服部': 'bi bi-headset',
            '其他': 'bi bi-three-dots'  // 添加"其他"部门的图标
          }
          
          // 确保每个部门都有count属性
          const formattedDepts = res.data.departments.map(dept => ({
            id: dept.id,
            name: dept.name,
            icon: deptIcons[dept.name] || 'bi bi-building',
            count: dept.count || 0  // 确保count属性存在，如果为null或undefined则设为0
          }))
          
          // 统计没有部门的用户数量
          const noDeptCount = await getContactsWithNoDept()
          
          // 添加"其他"部门选项 (如果有无部门用户)
          if (noDeptCount > 0) {
            formattedDepts.push({
              id: 'no-dept', // 特殊ID用于标识没有部门的用户
              name: '其他',
              icon: deptIcons['其他'],
              count: noDeptCount
            })
          }
          
          departments.value = [...allDepts, ...formattedDepts]
          console.log('部门列表加载完成:', departments.value)
        } else {
          console.error('获取部门列表响应格式错误:', res)
          ElMessage.error('获取部门列表失败：响应格式错误')
        }
      } catch (error) {
        console.error('获取部门列表失败:', error)
        ElMessage.error('获取部门列表失败：' + (error.message || '未知错误'))
      } finally {
        loading.value.departments = false
      }
    }

    // 获取公司所有联系人总数
    const getTotalContactsCount = async () => {
      try {
        if (!companyId.value) {
          console.error('未找到当前用户所属公司ID，无法获取联系人总数')
          return 0
        }
        
        console.log('开始获取联系人总数，公司ID:', companyId.value)
        const res = await request('/api/auth/contacts/', { params: { company: companyId.value } })
        console.log('获取联系人总数响应:', res)
        
        if (res && res.success && Array.isArray(res.data)) {
          return res.data.length
        }
        return 0
      } catch (error) {
        console.error('获取联系人总数失败:', error)
        return 0
      }
    }

    // 获取没有部门的用户数量
    const getContactsWithNoDept = async () => {
      try {
        if (!companyId.value) {
          console.error('未找到当前用户所属公司ID，无法获取联系人')
          return 0
        }
        
        console.log('开始获取无部门联系人，公司ID:', companyId.value)
        const res = await request('/api/auth/contacts/', { params: { company: companyId.value } })
        console.log('获取联系人总数响应:', res)
        
        if (res && res.success && Array.isArray(res.data)) {
          // 筛选没有部门的联系人
          const contactsWithNoDept = res.data.filter(contact => 
            !contact.department || contact.department === null || contact.department === '' || 
            !contact.department_name || contact.department_name === null || contact.department_name === ''
          )
          return contactsWithNoDept.length
        }
        return 0
      } catch (error) {
        console.error('获取无部门联系人数量失败:', error)
        return 0
      }
    }

    // 获取联系人列表
    const fetchContacts = async () => {
      loading.value.contacts = true
      try {
        if (!companyId.value) {
          console.error('未找到当前用户所属公司ID，无法获取联系人列表')
          ElMessage.warning('未找到当前用户所属公司，无法获取联系人')
          loading.value.contacts = false
          return
        }
        
        console.log('开始获取联系人列表，公司ID:', companyId.value)
        let url = '/api/auth/contacts/'
        const params = {
          company: companyId.value // 始终添加当前用户公司ID筛选
        }
        
        // 如果有搜索关键词，添加搜索参数
        if (searchQuery.value) {
          params.search = searchQuery.value
        } else if (selectedDept.value !== 0) {
          // 只有在没有搜索关键词且选择了特定部门时，才添加部门过滤
          const selectedDeptInfo = departments.value[selectedDept.value]
          
          if (selectedDeptInfo) {
            if (selectedDeptInfo.id === 'no-dept') {
              // 如果选择了"其他"部门，不需要添加部门参数，稍后会在结果中筛选
              console.log('已选择"其他"部门，将筛选没有部门的联系人')
            } else {
              // 正常部门，添加部门ID参数
              params.department = selectedDeptInfo.id
            }
          } else {
            console.error('选择的部门索引无效:', selectedDept.value)
          }
        }
        
        console.log('请求联系人列表参数:', params)
        const res = await request(url, { params })
        console.log('获取联系人列表响应:', res)
        
        if (res && res.success && Array.isArray(res.data)) {
          // 处理返回的联系人数据，添加avatar_url
          res.data.forEach(contact => {
            // 检查联系人自身是否有avatar字段
            if (contact.avatar) {
              // 处理头像路径，将avatar转换为完整URL
              const avatar = contact.avatar;
              if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
                contact.avatar_url = avatar;
              } else if (avatar.startsWith('/')) {
                contact.avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}${avatar}`;
              } else {
                contact.avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}/${avatar}`;
              }
            } 
            // 检查联系人是否关联了用户，用户可能有头像
            else if (contact.user && typeof contact.user === 'object' && contact.user.avatar) {
              const avatar = contact.user.avatar;
              if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
                contact.avatar_url = avatar;
              } else if (avatar.startsWith('/')) {
                contact.avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}${avatar}`;
              } else {
                contact.avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}/${avatar}`;
              }
            }
            // 如果用户ID是数字，可能需要额外获取用户信息
            else if (contact.user && typeof contact.user === 'number') {
              // 这里需要异步获取用户信息，但为简单起见，先设置一个标记
              contact.need_fetch_avatar = true;
            }

            // 添加调试日志
            console.log(`联系人 ${contact.name} 的头像信息:`, { 
              avatar: contact.avatar, 
              avatar_url: contact.avatar_url,
              user: contact.user
            });
          });

          // 如果选择了"其他"部门，筛选没有部门的联系人
          if (selectedDept.value !== 0 && 
              departments.value[selectedDept.value] && 
              departments.value[selectedDept.value].id === 'no-dept') {
            
            contacts.value = res.data.filter(contact => 
              !contact.department || contact.department === null || contact.department === '' ||
              !contact.department_name || contact.department_name === null || contact.department_name === ''
            )
            console.log('筛选出的无部门联系人:', contacts.value)
          } else {
            // 正常显示所有联系人或特定部门的联系人
            contacts.value = res.data
          }
          
          // 加载那些需要获取额外用户信息的联系人头像
          contacts.value.forEach(async (contact, index) => {
            if (contact.need_fetch_avatar) {
              await fetchUserAvatar(contact, index);
            }
          });
          
          // 打印第一个联系人数据以查看结构
          if (contacts.value && contacts.value.length > 0) {
            console.log('联系人数据结构示例:', contacts.value[0])
          } else {
            console.log('未找到任何联系人')
          }
          // 默认选中第一个联系人
          selectedContact.value = contacts.value.length > 0 ? 0 : null
        } else {
          console.error('获取联系人列表响应格式错误:', res)
          ElMessage.error('获取联系人列表失败：响应格式错误')
        }
      } catch (error) {
        console.error('获取联系人列表失败:', error)
        ElMessage.error('获取联系人列表失败：' + (error.message || '未知错误'))
      } finally {
        loading.value.contacts = false
      }
    }

    // 监听部门选择变化
    watch(selectedDept, () => {
      fetchContacts()
    })

    // 监听搜索关键词变化，使用防抖
    let searchTimeout = null
    watch(searchQuery, () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }
      searchTimeout = setTimeout(() => {
        fetchContacts()
      }, 300)
    })

    // 初始化数据
    onMounted(async () => {
      try {
      // 先获取当前用户信息
        console.log('开始初始化联系人页面...')
        const userData = await fetchCurrentUser()
        
        if (!userData) {
          console.error('未能获取到用户信息，中断初始化流程')
          return
        }
        
        if (!companyId.value) {
          console.error('未找到用户所属公司ID，中断初始化流程')
          return
        }
      
      // 再加载部门列表
        console.log('开始加载部门列表...')
      await fetchDepartments()
      
      // 最后加载联系人列表
        console.log('开始加载联系人列表...')
      await fetchContacts()
        
        console.log('联系人页面初始化完成')
      } catch (error) {
        console.error('联系人页面初始化失败:', error)
        ElMessage.error('页面加载失败：' + (error.message || '未知错误'))
      }
    })

    // 工具方法
    const getInitials = (name) => {
      if (!name) return ''
      return name.substring(0, 1)
    }

    // 跳转到聊天页面
    const startChat = async (contact) => {
      try {
        console.log('联系人信息:', contact)
        
        // 获取认证token
        const token = localStorage.getItem('token')
        if (!token) {
          ElMessage.error('未登录或登录已过期')
          return
        }
        
        // 先获取当前用户信息
        const currentUserResponse = await axios.get('/api/auth/users/me/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!currentUserResponse.data || !currentUserResponse.data.data) {
          ElMessage.error('获取当前用户信息失败')
          return
        }
        
        const currentUserId = currentUserResponse.data.data.id
        console.log('当前用户ID:', currentUserId)
        
        // 直接使用联系人的ID创建聊天会话
        // 因为联系人现在就是用户，所以ID直接用联系人的ID
        const userId = parseInt(contact.id)
        if (isNaN(userId) || userId <= 0) {
          console.log('无效的用户ID:', contact.id)
          ElMessage.error('无效的联系人用户ID')
          return
        }
        
        // 检查联系人用户ID是否与当前用户ID相同
        if (userId === currentUserId) {
          console.log('无法与自己聊天')
          ElMessage.error('无法与自己聊天')
          return
        }
        
        // 首先获取现有的聊天会话列表
        try {
          console.log('正在检查是否已有与该联系人的聊天会话...')
          const sessionsResponse = await axios.get('/api/chat/sessions/', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          console.log('获取到的会话列表:', sessionsResponse.data)
          
          // 解析会话数据
          let sessions = []
          if (sessionsResponse.data && sessionsResponse.data.results) {
            // 分页格式
            sessions = sessionsResponse.data.results
          } else if (sessionsResponse.data && Array.isArray(sessionsResponse.data)) {
            // 直接数组格式
            sessions = sessionsResponse.data
          } else if (sessionsResponse.data && sessionsResponse.data.data && Array.isArray(sessionsResponse.data.data)) {
            // 嵌套data格式
            sessions = sessionsResponse.data.data
          }
          
          // 查找是否有与当前联系人的单聊会话
          // 单聊会话的特点是不是群组，且只有两个参与者
          const existingSession = sessions.find(session => {
            // 跳过群聊
            if (session.is_group) return false
            
            // 确保有参与者数据且为数组
            if (!session.participants || !Array.isArray(session.participants)) return false
            
            // 确保参与者数量为2（当前用户+目标联系人）
            if (session.participants.length !== 2) return false
            
            // 查找是否有目标联系人在参与者中
            const hasTargetUser = session.participants.some(participant => {
              return participant.user && participant.user.id === userId
            })
            
            return hasTargetUser
          })
          
          if (existingSession) {
            // 找到现有会话，直接跳转
            console.log('找到现有会话:', existingSession)
            router.push({
              path: '/chat',
              query: { id: existingSession.id }
            })
            return
          } else {
            console.log('未找到与该联系人的现有会话，将创建新会话')
          }
          
          // 创建聊天会话
          const chatData = {
            participant_ids: [userId], // 使用整数类型
            is_group: false,
            title: contact.name ? `与${contact.name}的聊天` : '新聊天'
          }
          
          console.log('发送创建聊天会话请求:', chatData)
          console.log('participant_ids值:', chatData.participant_ids)
          console.log('participant_ids[0]类型:', typeof chatData.participant_ids[0])
          
          // 使用API函数替代直接axios调用
          const chatResponse = await axios.post('/api/chat/sessions/', chatData, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })
          
          console.log('聊天会话创建响应:', chatResponse.data)
          
          // 处理响应数据
          let sessionId = null
          if (chatResponse.data && chatResponse.data.id) {
            // 直接从响应获取ID
            sessionId = chatResponse.data.id
          } else if (chatResponse.data && chatResponse.data.data && chatResponse.data.data.id) {
            // 从data字段获取ID
            sessionId = chatResponse.data.data.id
          }
          
          if (sessionId) {
            console.log('获取到的会话ID:', sessionId)
            
            // 跳转到聊天页面，使用chat作为key
            router.push({
              path: '/chat',
              query: { id: sessionId }
            })
          } else {
            console.error('无法获取会话ID:', chatResponse.data)
            ElMessage.error('创建聊天会话成功，但无法获取会话ID')
          }
        } catch (error) {
          console.error('创建聊天会话失败:', error)
          if (error.response) {
            console.error('错误详情:', error.response.data)
            console.error('错误状态码:', error.response.status)
            
            // 显示具体的错误信息
            let errorMessage = '创建聊天会话失败'
            if (error.response.data) {
              if (typeof error.response.data === 'string') {
                errorMessage = error.response.data
              } else if (error.response.data.detail) {
                errorMessage = error.response.data.detail
              } else if (error.response.data.message) {
                errorMessage = error.response.data.message
              } else if (
                error.response.data.participant_ids && 
                Array.isArray(error.response.data.participant_ids) && 
                error.response.data.participant_ids.length > 0
              ) {
                errorMessage = error.response.data.participant_ids[0]
              } else {
                errorMessage = '创建聊天会话失败: ' + JSON.stringify(error.response.data)
              }
            }
            ElMessage.error(errorMessage)
          } else {
            ElMessage.error('创建聊天会话失败：网络错误')
          }
          throw error
        }
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error('操作失败：' + (error.message || '未知错误'))
      }
    }

    // 添加获取用户头像的辅助函数
    const fetchUserAvatar = async (contact, index) => {
      if (!contact.user || typeof contact.user !== 'number') return;
      
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        console.log(`为联系人 ${contact.name} 获取用户头像...`);
        const response = await axios.get(`/api/auth/users/${contact.user}/`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        let userData = null;
        if (response.data && response.data.success && response.data.data) {
          userData = response.data.data;
        } else if (response.data) {
          userData = response.data;
        }
        
        if (userData && userData.avatar) {
          const avatar = userData.avatar;
          if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
            contact.avatar_url = avatar;
          } else if (avatar.startsWith('/')) {
            contact.avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}${avatar}`;
          } else {
            contact.avatar_url = `${process.env.VUE_APP_BASE_API || 'http://localhost:8000'}/${avatar}`;
          }
          console.log(`成功获取联系人 ${contact.name} 的头像:`, contact.avatar_url);
          
          // 这里需要通过Vue的响应式系统更新联系人数据
          if (index !== undefined && index >= 0 && index < contacts.value.length) {
            contacts.value[index] = { ...contact };
          }
        }
      } catch (error) {
        console.error(`获取联系人 ${contact.name} 的用户头像失败:`, error);
      }
    };

    return {
      searchQuery,
      selectedDept,
      selectedContact,
      departments,
      contacts,
      loading,
      getInitials,
      startChat,
      getDeptIcon,
      getAvatarStyle
    }
  }
}
</script>

<style lang="scss" scoped>
.contact-container {
  padding: 20px;
}

.contact-wrapper {
  display: flex;
  gap: 20px;
  height: calc(100vh - 140px);
}

.contact-sidebar {
  width: 240px;
  flex-shrink: 0;
}

.contact-list {
  width: 320px;
  flex-shrink: 0;
}

.contact-detail {
  flex: 1;
  min-width: 0;
}

.contacts-nav-card,
.contacts-list-card,
.contact-detail-card {
  height: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.1);
  }
}

.search-box {
  margin-bottom: 15px;
}

.contacts-nav {
  max-height: calc(100vh - 240px);
  overflow-y: auto;
  padding-right: 5px;
  
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background-color: rgba(144, 147, 153, 0.3);
    border-radius: 2px;
  }
}

.dept-item {
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  transition: all 0.3s ease;
  
  .el-icon {
    font-size: 16px;
    margin-right: 10px;
    color: var(--el-text-color-secondary);
  }
  
  &:hover {
    background-color: var(--el-fill-color-light);
  }
  
  &.active {
    background-color: var(--el-color-primary-light-9);
    color: var(--el-color-primary);
    
    .el-icon {
      color: var(--el-color-primary);
    }
  }
  
  span {
    flex: 1;
    font-size: 14px;
  }
}

.dept-badge {
  margin-left: 5px;
}

.dept-badge :deep(.el-badge__content) {
  background-color: #909399 !important;
  color: white !important;
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 16px;
  font-weight: 500;
}

.contact-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  background-color: var(--el-fill-color-light);
  padding: 2px 8px;
  border-radius: 10px;
}

.search-info {
  background-color: var(--el-fill-color-light);
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  
  .el-icon {
    margin-right: 6px;
    color: var(--el-color-info);
  }
}

.contacts-list {
  max-height: calc(100vh - 240px);
  overflow-y: auto;
  padding-right: 5px;
  
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background-color: rgba(144, 147, 153, 0.3);
    border-radius: 2px;
  }
}

.contact-item {
  display: flex;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background-color: var(--el-fill-color-light);
  }
  
  &.active {
    background-color: var(--el-color-primary-light-9);
  }
}

.contact-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-right: 12px;
  font-size: 16px;
}

.contact-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.contact-name {
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.contact-position {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.contact-header {
  display: flex;
  margin-bottom: 24px;
}

.detail-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 24px;
  margin-right: 20px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.detail-info {
  flex: 1;
  min-width: 0;
}

.detail-name {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 6px;
}

.detail-position, .detail-department {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.contact-actions {
  margin-top: 12px;
  display: flex;
  gap: 10px;
}

.contact-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.contact-section {
  margin-bottom: 0;
}

.section-title {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  
  .el-icon {
    margin-right: 8px;
    color: var(--el-color-primary);
    font-size: 18px;
  }
}

.contact-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -10px;
}

.contact-item-box {
  width: 50%;
  padding: 0 10px;
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
}

.contact-item-icon {
  color: var(--el-color-info);
  margin-right: 10px;
  font-size: 16px;
}

.contact-item-content {
  flex: 1;
  min-width: 0;
}

.contact-item-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.contact-item-value {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-tag {
  margin: 0;
}

.bio-content {
  padding: 12px 15px;
  background-color: var(--hover-color);
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  margin-top: 5px;
  white-space: pre-line;
}

// 响应式布局
@media (max-width: 1200px) {
  .contact-wrapper {
    flex-wrap: wrap;
    height: auto;
  }
  
  .contact-sidebar {
    width: 100%;
    margin-bottom: 20px;
  }
  
  .contacts-nav {
    max-height: 200px;
  }
  
  .contact-list {
    width: 40%;
  }
  
  .contact-detail {
    width: 60%;
  }
  
  .contact-item-box {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .contact-wrapper {
    flex-direction: column;
  }
  
  .contact-list,
  .contact-detail {
    width: 100%;
    margin-bottom: 20px;
  }
  
  .contacts-list,
  .contacts-nav {
    max-height: 300px;
  }
}

.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

:deep(.el-tag) {
  background: var(--bg-color-tertiary) !important;
  color: var(--text-color) !important;
  border-color: var(--border-color) !important;
}
:deep(.el-tag.el-tag--info) {
  background: var(--bg-color-tertiary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-color) !important;
}
:deep(.el-tag.el-tag--success) {
  background: var(--success-color) !important;
  border-color: var(--success-color) !important;
  color: #fff !important;
}
:deep(.el-tag.el-tag--primary) {
  background: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: #fff !important;
}
:deep(.el-tag.el-tag--warning) {
  background: var(--warning-color) !important;
  border-color: var(--warning-color) !important;
  color: #fff !important;
}
:deep(.el-tag.el-tag--danger) {
  background: var(--danger-color) !important;
  border-color: var(--danger-color) !important;
  color: #fff !important;
}
:deep(.el-badge__content) {
  background: var(--danger-color) !important;
  color: #fff !important;
}
.contact-item:hover,
.dept-item:hover,
.search-info,
.contact-count {
  background-color: var(--hover-color) !important;
}
:deep(.el-table__row:hover > td.el-table__cell) {
  background-color: var(--hover-color) !important;
}

.contacts-nav-card {
  background: var(--bg-color-secondary) !important;
  border-color: var(--border-color) !important;
}
:deep(.el-card.contacts-nav-card) {
  background: var(--bg-color-secondary) !important;
  border-color: var(--border-color) !important;
}
.dept-item.active {
  background: var(--bg-color-tertiary) !important;
  color: var(--primary-color) !important;
}
.dept-item {
  background: transparent !important;
}

:deep(.el-badge__content.is-fixed) {
  position: static !important;
  transform: none !important;
}
</style> 