<template>
  <div class="contract-detail-container">
    <!-- 将导航栏移到顶部 -->
    <div class="top-navigation-bar">
      <el-tabs v-model="activeTab" class="contract-detail-tabs">
        <el-tab-pane label="基本信息" name="basicInfo"></el-tab-pane>
        <el-tab-pane label="合同文本" name="contractText"></el-tab-pane>
        <el-tab-pane label="合同检查" name="contractCheck"></el-tab-pane>
        <el-tab-pane label="操作记录" name="history"></el-tab-pane>
      </el-tabs>
    </div>

    <div class="card" v-loading="isLoading">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span id="contractTitleHeader">{{ contractTitle }}</span>
        <div>
          <el-button type="default" size="small" class="me-2" @click="downloadContract">
            <el-icon><Download /></el-icon> 下载Word
          </el-button>
          <el-button 
            type="primary" 
            size="small" 
            @click="saveChanges" 
            :loading="isSaving"
          >
            <el-icon><DocumentAdd /></el-icon> 保存更改
          </el-button>
        </div>
      </div>
      <div class="card-body">
        <!-- 原来的导航栏已移除，现在根据activeTab值显示不同内容 -->
        <div v-if="activeTab === 'basicInfo'">
          <h5>基本信息</h5>
          <div class="row mb-3">
            <div class="col-md-6">
              <el-form label-position="top">
                <el-form-item label="合同名称">
                  <el-input v-model="contractDetails.title"></el-input>
                </el-form-item>
                <el-form-item label="合同编号">
                  <el-input v-model="contractDetails.number" disabled></el-input>
                </el-form-item>
                <el-form-item label="合同类型">
                  <el-select v-model="contractDetails.type" style="width: 100%;">
                    <el-option label="采购合同" value="采购合同"></el-option>
                    <el-option label="销售合同" value="销售合同"></el-option>
                    <el-option label="服务合同" value="服务合同"></el-option>
                    <el-option label="合作协议" value="合作协议"></el-option>
                    <el-option label="租赁合同" value="租赁合同"></el-option>
                    <el-option label="其他" value="其他"></el-option>
                  </el-select>
                </el-form-item>
                <el-form-item label="合同金额">
                  <el-input v-model="contractDetails.amount" prefix="¥"></el-input>
                </el-form-item>
              </el-form>
            </div>
            <div class="col-md-6">
              <el-form label-position="top">
                <el-form-item label="签约对方">
                  <el-input v-model="contractDetails.company"></el-input>
                </el-form-item>
                <el-form-item label="签约日期">
                  <el-date-picker 
                    v-model="contractDetails.signDate" 
                    type="date" 
                    value-format="YYYY-MM-DD"
                    style="width: 100%;">
                  </el-date-picker>
                </el-form-item>
                <el-form-item label="生效日期">
                  <el-date-picker 
                    v-model="contractDetails.startDate" 
                    type="date" 
                    value-format="YYYY-MM-DD"
                    style="width: 100%;">
                  </el-date-picker>
                </el-form-item>
                <el-form-item label="到期日期">
                  <el-date-picker 
                    v-model="contractDetails.expireDate" 
                    type="date" 
                    value-format="YYYY-MM-DD"
                    style="width: 100%;">
                  </el-date-picker>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'contractText'">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h5>合同文本编辑</h5>
            <div class="d-flex align-items-center">
              <div v-if="realTimePolishLoading" class="d-flex align-items-center">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span class="ms-1">AI分析中...</span>
              </div>
            </div>
          </div>
          
          <!-- 使用flex布局容器包裹AI润色区和编辑器区，添加ref以便于JS操作 -->
          <div class="contract-edit-wrapper">
            <!-- 删除badge容器 -->
            
            <div class="contract-edit-container" ref="contractEditContainer">
              <!-- AI润色分析左侧区域 -->
              <div class="ai-polish-sidebar" ref="aiPolishSidebar">
                <el-button 
                  type="primary" 
                  size="large" 
                  @click="manualAnalyzeText" 
                  :loading="realTimePolishLoading"
                  :disabled="realTimePolishLoading"
                  class="ai-polish-button"
                >
                  <div class="ai-polish-button-content">
                    <el-icon class="ai-polish-icon no-bg"><MagicStick /></el-icon>
                    <span>{{ realTimePolishLoading ? '正在分析中...' : 'AI智能润色' }}</span>
                  </div>
                </el-button>
                
                <div class="ai-polish-info">
                  <div class="time-estimate" v-if="!realTimePolishLoading">
                    <el-icon><Timer /></el-icon>
                    <span>预计用时: {{ estimatedTime }}</span>
                  </div>
                  <div class="shortcut-hint">
                    <el-icon><Position /></el-icon>
                    <span>快捷键: Ctrl+Shift+A</span>
                  </div>
                </div>
                
                <!-- 个性化定制选项区域 -->
                <div class="ai-polish-personalization">
                  <h6 class="personalization-title">个性化定制</h6>
                  
                  <div class="personalization-section">
                    <div class="section-header">
                      <el-icon><Setting /></el-icon>
                      <span>润色偏好</span>
                    </div>
                    
                    <div class="preference-option">
                      <span>语言风格</span>
                      <el-select v-model="polishPreferences.style" size="small" placeholder="选择风格">
                        <el-option label="正式严谨" value="formal"></el-option>
                        <el-option label="中性专业" value="neutral"></el-option>
                        <el-option label="简洁明了" value="concise"></el-option>
                      </el-select>
                    </div>
                    
                    <div class="preference-option">
                      <span>合同类型</span>
                      <el-select v-model="polishPreferences.contractType" size="small" placeholder="选择类型">
                        <el-option label="通用合同" value="general"></el-option>
                        <el-option label="买卖合同" value="sales"></el-option>
                        <el-option label="劳务合同" value="labor"></el-option>
                        <el-option label="租赁合同" value="lease"></el-option>
                        <el-option label="技术合同" value="technology"></el-option>
                      </el-select>
                    </div>
                  </div>
                  
                  <div class="personalization-section">
                    <div class="section-header">
                      <el-icon><DocumentChecked /></el-icon>
                      <span>优化重点</span>
                    </div>
                    
                    <div class="optimization-options">
                      <el-checkbox-group v-model="polishPreferences.focus">
                        <el-checkbox label="grammar">语法规范</el-checkbox>
                        <el-checkbox label="terminology">专业术语</el-checkbox>
                        <el-checkbox label="structure">句式结构</el-checkbox>
                        <el-checkbox label="consistency">用词一致性</el-checkbox>
                      </el-checkbox-group>
                    </div>
                  </div>
                  
                  <div class="personalization-section">
                    <div class="section-header">
                      <el-icon><Notebook /></el-icon>
                      <span>术语词典</span>
                    </div>
                    
                    <div class="terminology-manager">
                      <el-input
                        v-model="newTerminology.term"
                        size="small"
                        placeholder="添加专业术语"
                        class="terminology-input"
                      >
                        <template #append>
                          <el-button @click="addCustomTerminology">
                            <el-icon><Plus /></el-icon>
                          </el-button>
                        </template>
                      </el-input>
                      
                      <div class="terminology-list" v-if="customTerminologies.length > 0">
                        <el-tag
                          v-for="(term, index) in customTerminologies"
                          :key="index"
                          closable
                          @close="removeCustomTerminology(index)"
                          class="terminology-tag"
                        >
                          {{term}}
                        </el-tag>
                      </div>
                      <div v-else class="terminology-empty">
                        <span class="text-muted">添加常用术语以确保准确性</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="ai-polish-features">
                  <div class="feature-item">
                    <el-icon><Check /></el-icon>
                    <span>改善语法和表达</span>
                  </div>
                  <div class="feature-item">
                    <el-icon><Check /></el-icon>
                    <span>优化专业术语</span>
                  </div>
                  <div class="feature-item">
                    <el-icon><Check /></el-icon>
                    <span>增强阅读体验</span>
                  </div>
                  <div class="feature-item">
                    <el-icon><Check /></el-icon>
                    <span>保持个性化定制</span>
                  </div>
                </div>
              </div>
              
              <!-- 文本编辑器右侧区域 -->
              <div class="editor-main-area" ref="editorMainArea">
                <QuillEditor
                  v-model:content="contractDetails.content"
                  ref="quillEditor"
                  :toolbar="editorOption.modules.toolbar"
                  contentType="html"
                  class="contract-text-editor"
                  theme="snow"
                  @textChange="onContractContentChange"
                />
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'contractCheck'">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5>合同检查审核</h5>
          </div>

          <!-- 使用与合同文本部分相同的布局结构 -->
          <div class="contract-edit-wrapper">
            <div class="contract-edit-container" ref="contractCheckContainer">
              <!-- 左侧工具栏和个性化设置区域 -->
              <div class="ai-polish-sidebar check-sidebar" ref="checkSidebar">
                <el-button 
                  type="primary" 
                  size="large" 
                  @click="startContractCheck" 
                  :loading="isChecking"
                  :disabled="isChecking"
                  class="ai-polish-button"
                >
                  <div class="ai-polish-button-content">
                    <el-icon class="ai-polish-icon no-bg"><DocumentChecked /></el-icon>
                    <span>{{ isChecking ? '检查中...' : 'AI智能检查' }}</span>
                  </div>
                </el-button>
                
                <div class="ai-polish-info">
                  <div class="time-estimate" v-if="!isChecking">
                    <el-icon><Timer /></el-icon>
                    <span>预计用时: {{ estimatedTime }}</span>
                  </div>
                  <div class="shortcut-hint">
                    <el-icon><Position /></el-icon>
                    <span>快捷键: Ctrl+Shift+C</span>
                  </div>
                </div>
                
                <!-- 检查偏好设置区域 -->
                <div class="ai-polish-personalization">
                  <h6 class="personalization-title">检查偏好设置</h6>
                  
                  <div class="personalization-section">
                    <div class="section-header">
                      <el-icon><Setting /></el-icon>
                      <span>检查维度</span>
                    </div>
                    
                    <div class="check-options">
                      <el-checkbox v-model="checkPreferences.legalCompliance">法律合规性</el-checkbox>
                      <el-checkbox v-model="checkPreferences.completeness">条款完整性</el-checkbox>
                      <el-checkbox v-model="checkPreferences.riskAlert">风险提示</el-checkbox>
                    </div>
                  </div>
                  
                  <div class="personalization-section">
                    <div class="section-header">
                      <el-icon><Reading /></el-icon>
                      <span>合同类型参考</span>
                    </div>
                    
                    <div class="preference-option">
                      <span>合同类型</span>
                      <el-select v-model="checkPreferences.contractType" size="small" placeholder="选择类型">
                        <el-option label="通用合同" value="general"></el-option>
                        <el-option label="买卖合同" value="sales"></el-option>
                        <el-option label="劳务合同" value="labor"></el-option>
                        <el-option label="租赁合同" value="lease"></el-option>
                        <el-option label="技术合同" value="technology"></el-option>
                      </el-select>
                    </div>
                  </div>
                  
                  <div class="personalization-section">
                    <div class="section-header">
                      <el-icon><InfoFilled /></el-icon>
                      <span>关注程度</span>
                    </div>
                    
                    <div class="preference-option">
                      <span>检查深度</span>
                      <el-select v-model="checkPreferences.checkDepth" size="small" placeholder="选择深度">
                        <el-option label="标准检查" value="standard"></el-option>
                        <el-option label="深度检查" value="deep"></el-option>
                        <el-option label="快速检查" value="quick"></el-option>
                      </el-select>
                    </div>
                  </div>
                </div>
                
                <div class="ai-polish-features">
                  <div class="feature-item">
                    <el-icon><Check /></el-icon>
                    <span>法律合规审查</span>
                  </div>
                  <div class="feature-item">
                    <el-icon><Check /></el-icon>
                    <span>条款完整性检查</span>
                  </div>
                  <div class="feature-item">
                    <el-icon><Check /></el-icon>
                    <span>潜在风险分析</span>
                  </div>
                  <div class="feature-item">
                    <el-icon><Check /></el-icon>
                    <span>智能修改建议</span>
                  </div>
                </div>
              </div>
              
              <!-- 右侧检查结果区域 -->
              <div class="editor-main-area check-result-area" ref="checkResultArea">
                <!-- 使用Element UI的el-scrollbar组件 -->
                <el-scrollbar height="calc(100% - 10px)" always class="contract-check-scrollbar">
                  <div class="check-content-inner" style="padding: 15px 20px;">
                    <!-- 检查结果概览卡片 -->
                    <div class="check-result-card">
                      <div class="check-result-header">
                        <h6>检查结果概览</h6>
                        <el-tag v-if="checkResult.totalIssues > 0" type="danger" size="small">发现{{ checkResult.totalIssues }}个问题</el-tag>
                        <el-tag v-else type="success" size="small">未发现问题</el-tag>
                      </div>
                      
                      <div class="check-result-stats">
                        <div class="stat-item">
                          <div class="stat-value danger">{{ checkResult.criticalIssues }}</div>
                          <div class="stat-label">严重问题</div>
                        </div>
                        <div class="stat-item">
                          <div class="stat-value warning">{{ checkResult.warningIssues }}</div>
                          <div class="stat-label">警告</div>
                        </div>
                        <div class="stat-item">
                          <div class="stat-value info">{{ checkResult.suggestions }}</div>
                          <div class="stat-label">建议</div>
                        </div>
                        <div class="stat-item">
                          <div class="stat-value">{{ checkResult.totalIssues }}</div>
                          <div class="stat-label">问题总数</div>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 无问题时显示的明确提示 -->
                    <div v-if="aiCheckFinished && !isChecking && checkResult.totalIssues === 0" class="el-alert el-alert--success" style="margin: 8px 0 12px 0; padding: 12px 18px; border-radius: 4px;">
                      <div style="display: flex; align-items: center;">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" style="width: 20px; height: 20px; margin-right: 8px; color: #67c23a; flex-shrink:0;">
                          <path fill="currentColor" d="M512 64a448 448 0 1 1 0 896 448 448 0 0 1 0-896zm-55.808 536.384-99.52-99.584a38.4 38.4 0 1 0-54.336 54.336l126.72 126.72a38.272 38.272 0 0 0 54.336 0l262.4-262.464a38.4 38.4 0 1 0-54.272-54.336L456.192 600.384z"></path>
                        </svg>
                        <span style="font-size: 15px; font-weight: bold; color: #67c23a; margin-right: 6px;">合同检查完成</span>
                        <span style="font-size: 14px; color: #606266; font-weight: normal;">AI分析完成，未发现明显风险。合同文本质量良好，符合常规法律和业务要求。</span>
                      </div>
                    </div>
                    
                    <!-- 检查结果详情 -->
                    <div class="check-result-details">
                      <el-collapse v-model="activeCollapse" class="check-collapse">
                        <el-collapse-item title="法律合规性" name="legalCompliance">
                          <template #title>
                            <div class="collapse-header">
                              <el-icon class="text-danger"><WarningFilled /></el-icon>
                              <span>法律合规性</span>
                              <el-badge :value="checkResult.legalComplianceIssues.length" type="danger" class="ms-2" v-if="checkResult.legalComplianceIssues.length > 0"></el-badge>
                            </div>
                          </template>
                          
                          <div v-if="checkResult.legalComplianceIssues.length === 0" class="empty-result">
                            <el-empty description="未发现法律合规性问题" :image-size="80"></el-empty>
                          </div>
                          
                          <div v-for="(issue, index) in checkResult.legalComplianceIssues" :key="'legal-'+index" class="check-issue-card">
                            <div class="issue-header">
                              <el-icon class="text-danger fs-4"><WarningFilled /></el-icon>
                              <h6>{{ issue.title }}</h6>
                            </div>
                            <div class="issue-content">
                              <div class="issue-field">
                                <div class="field-label">当前条款：</div>
                                <div class="field-value">{{ issue.current }}</div>
                              </div>
                              <div class="issue-field">
                                <div class="field-label">问题：</div>
                                <div class="field-value text-danger">{{ issue.problem }}</div>
                              </div>
                            </div>
                            <div class="issue-actions">
                              <el-button size="small" type="primary" @click="viewRegulation(issue)">查看法规</el-button>
                              <el-button size="small" type="default">忽略</el-button>
                            </div>
                          </div>
                        </el-collapse-item>

                        <el-collapse-item title="条款完整性" name="clauseCompleteness">
                          <template #title>
                            <div class="collapse-header">
                              <el-icon class="text-warning"><Document /></el-icon>
                              <span>条款完整性</span>
                              <el-badge :value="checkResult.completenessIssues.length" type="warning" class="ms-2" v-if="checkResult.completenessIssues.length > 0"></el-badge>
                            </div>
                          </template>
                          
                          <div v-if="checkResult.completenessIssues.length === 0" class="empty-result">
                            <el-empty description="未发现条款完整性问题" :image-size="80"></el-empty>
                          </div>
                          
                          <div v-for="(issue, index) in checkResult.completenessIssues" :key="'comp-'+index" class="check-issue-card">
                            <div class="issue-header">
                              <el-icon class="text-warning fs-4"><Warning /></el-icon>
                              <h6>{{ issue.title }}</h6>
                            </div>
                            <div class="issue-content">
                              <div class="issue-field">
                                <div class="field-label">建议：</div>
                                <div class="field-value">{{ issue.suggestion }}</div>
                              </div>
                            </div>
                            <div class="issue-actions">
                              <el-button size="small" type="default">忽略</el-button>
                            </div>
                          </div>
                        </el-collapse-item>

                        <el-collapse-item title="风险提示" name="riskAlert">
                          <template #title>
                            <div class="collapse-header">
                              <el-icon class="text-info"><InfoFilled /></el-icon>
                              <span>风险提示</span>
                              <el-badge :value="checkResult.riskAlerts.length" type="info" class="ms-2" v-if="checkResult.riskAlerts.length > 0"></el-badge>
                            </div>
                          </template>
                          
                          <div v-if="checkResult.riskAlerts.length === 0" class="empty-result">
                            <el-empty description="未发现风险提示" :image-size="80"></el-empty>
                          </div>
                          
                          <div v-for="(issue, index) in checkResult.riskAlerts" :key="'risk-'+index" class="check-issue-card">
                            <div class="issue-header">
                              <el-icon class="text-info fs-4"><InfoFilled /></el-icon>
                              <h6>{{ issue.title }}</h6>
                            </div>
                            <div class="issue-content">
                              <div class="issue-field">
                                <div class="field-label">建议：</div>
                                <div class="field-value">{{ issue.suggestion }}</div>
                              </div>
                            </div>
                            <div class="issue-actions">
                              <el-button size="small" type="default">忽略</el-button>
                            </div>
                          </div>
                        </el-collapse-item>
                      </el-collapse>
                    </div>
                  </div>
                </el-scrollbar>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'history'">
          <h5>操作记录</h5>
          <el-timeline>
            <el-timeline-item
              v-for="(activity, index) in contractHistory"
              :key="index"
              :timestamp="activity.time"
            >
              {{ activity.content }}
            </el-timeline-item>
          </el-timeline>
          <el-empty 
            v-if="contractHistory.length === 0" 
            description="暂无操作记录"
          ></el-empty>
        </div>
        
        <hr>
        <div class="mt-3 text-end">
          <el-button @click="goBack">返回列表</el-button>
        </div>
      </div>
    </div>

    <!-- AI建议面板 (初始隐藏) -->
    <div 
      v-if="activeTab === 'contractText'"
      class="ai-suggestions-panel" 
      :class="{ 'show': showAiSuggestions, 'collapsed': isAiPanelCollapsed }"
      id="aiSuggestionsPanel"
    >
      <div class="panel-header">
        <h5><el-icon class="text-warning"><Reading /></el-icon> AI 润色建议</h5>
        <div class="panel-controls">
          <el-button type="link" @click="hideAiPanel">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
      
      <div v-if="realTimePolishLoading" class="text-center my-2">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span class="ms-1">正在分析内容...</span>
      </div>
      
      <div v-if="!realTimePolishLoading && aiSuggestions.syntax.length === 0 && aiSuggestions.terminology.length === 0" class="text-center my-3 text-muted">
        <el-icon><InfoFilled /></el-icon>
        <p>没有建议可显示</p>
        <p class="small">点击上方"AI润色分析"按钮可获取建议</p>
      </div>
      
      <el-collapse v-model="activeSuggestionCollapse">
        <el-collapse-item name="syntax">
          <template #title>
            <span><el-icon class="me-1"><Edit /></el-icon> 语法与格式 ({{ aiSuggestions.syntax.length }})</span>
          </template>
          
          <div v-if="aiSuggestions.syntax.length === 0" class="p-3 text-center text-muted">
            没有语法或格式问题
          </div>
          
          <div 
            v-for="(suggestion, index) in aiSuggestions.syntax" 
            :key="'syntax-'+index" 
            class="suggestion-item"
          >
            <div class="original-text">{{ suggestion.original }}</div>
            <div class="suggested-text">{{ suggestion.suggested }}</div>
            <p class="explanation">{{ suggestion.explanation }}</p>
            <div class="suggestion-actions text-end">
              <el-button size="small" @click="ignoreSuggestion('syntax', index)">忽略</el-button>
              <el-button size="small" type="success" @click="adoptSuggestion('syntax', index)">采纳</el-button>
            </div>
          </div>
        </el-collapse-item>

        <el-collapse-item name="terminology">
          <template #title>
            <span><el-icon class="me-1"><Reading /></el-icon> 专业术语 ({{ aiSuggestions.terminology.length }})</span>
          </template>
          
          <div v-if="aiSuggestions.terminology.length === 0" class="p-3 text-center text-muted">
            没有术语问题
          </div>
          
          <div 
            v-for="(suggestion, index) in aiSuggestions.terminology" 
            :key="'term-'+index" 
            class="suggestion-item"
          >
            <div class="original-text">{{ suggestion.original }}</div>
            <div class="suggested-text">{{ suggestion.suggested }}</div>
            <p class="explanation">{{ suggestion.explanation }}</p>
            <div class="suggestion-actions text-end">
              <el-button size="small" @click="ignoreSuggestion('terminology', index)">忽略</el-button>
              <el-button size="small" type="success" @click="adoptSuggestion('terminology', index)">采纳</el-button>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <div class="text-center mt-3" v-if="aiSuggestions.syntax.length > 0 || aiSuggestions.terminology.length > 0">
        <el-button type="primary" size="small" @click="applyAllSuggestions">应用所有采纳的建议</el-button>
      </div>
    </div>

    <!-- 永久可见的展开按钮，只在合同文本标签页且面板隐藏时显示 -->
    <div 
      v-if="activeTab === 'contractText' && !showAiSuggestions"
      class="panel-open-button"
      @click="showAiSuggestions = true"
    >
      <el-tooltip content="显示AI润色建议" placement="left">
        <el-button type="primary" size="small" circle>
          <el-icon><MagicStick /></el-icon>
        </el-button>
      </el-tooltip>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed, watch, onUnmounted, nextTick, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import {
  Download, DocumentAdd, MagicStick, Check, Warning, WarningFilled,
  Document, InfoFilled, Edit, Reading, Close, Loading,
  Timer, Position, Setting, DocumentChecked, Notebook, Plus
} from '@element-plus/icons-vue'
import { 
  getContractDetail, 
  updateContract, 
  checkContract,
  aiPolishContract 
} from '@/api/contract'
import request from '@/utils/request'
// 引入富文本编辑器
import { QuillEditor } from '@vueup/vue-quill'
// 引入富文本编辑器样式
import '@vueup/vue-quill/dist/vue-quill.snow.css'
// 引入lodash的debounce函数用于性能优化
import { debounce } from 'lodash-es'

// 延迟加载Quill模块确保只在客户端执行
let SuggestionBlot
let SuggestionModule

// 初始化Quill扩展 - 确保只在浏览器环境中执行
const initQuillExtensions = () => {
  if (typeof window === 'undefined') return
  
  // 确保Quill已经通过CDN加载
  if (!window.Quill) {
    console.error('Quill未加载，无法初始化扩展')
    return
  }
  
  // 创建自定义Quill内联格式 - 建议高亮
  const InlineSuggestionBlot = window.Quill.import('blots/inline')
  SuggestionBlot = class extends InlineSuggestionBlot {
    static create(value) {
      const node = super.create()
      node.setAttribute('data-suggestion-id', value.id)
      node.setAttribute('class', 'suggestion-highlight')
      node.setAttribute('data-original', value.original)
      node.setAttribute('data-suggested', value.suggested)
      
      // 添加提示和更明显的视觉样式
      node.title = '点击查看修改建议'
      node.style.position = 'relative'
      node.style.backgroundColor = 'rgba(255, 217, 102, 0.3)'
      node.style.borderBottom = '1px dashed #ffb300'
      node.style.padding = '0 2px'
      node.style.cursor = 'pointer'
      
      return node
    }
  
    static formats(node) {
      return {
        id: node.getAttribute('data-suggestion-id'),
        original: node.getAttribute('data-original'),
        suggested: node.getAttribute('data-suggested')
      }
    }
  }
  SuggestionBlot.blotName = 'suggestion'
  SuggestionBlot.tagName = 'span'
  window.Quill.register(SuggestionBlot)
  
  // 自定义Quill Module - 处理建议交互
  SuggestionModule = class {
    constructor(quill, options) {
      this.quill = quill
      this.options = options
      this.suggestions = options.suggestions || []
      this.container = document.createElement('div')
      this.container.className = 'ql-suggestion-tooltip'
      this.container.style.display = 'none'
      document.body.appendChild(this.container)
      
      this.quill.on('text-change', () => {
        this.update()
      })
      
      // 保存点击监听器的引用以便于清理
      this._clickListener = (e) => {
        if (e.target && e.target.classList.contains('suggestion-highlight')) {
          this.showTooltip(e.target)
        } else {
          this.hideTooltip()
        }
      }
      
      this.quill.root.addEventListener('click', this._clickListener)
      
      // 使用MutationObserver替代DOMNodeInserted监听
      this.observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
          if (mutation.type === 'childList' || mutation.type === 'characterData') {
            this.update()
          }
        }
      })
      
      // 配置observer监听子节点变化和内容变化
      this.observer.observe(this.quill.root, {
        childList: true,
        subtree: true,
        characterData: true
      })
    }
    
    update() {
      // 更新建议标记
    }
    
    showTooltip(element) {
      const rect = element.getBoundingClientRect()
      const id = element.getAttribute('data-suggestion-id')
      const original = element.getAttribute('data-original')
      const suggested = element.getAttribute('data-suggested')
      
      // 增强工具提示，确保前后对比清晰
      this.container.innerHTML = `
        <div class="suggestion-tooltip-content">
          <div class="suggestion-tooltip-header">AI文本优化建议</div>
          <div class="suggestion-tooltip-body">
            <div class="suggestion-label">原文本:</div>
            <div class="suggestion-original">${original}</div>
            <div class="suggestion-arrow"><span>→</span></div>
            <div class="suggestion-label">建议修改为:</div>
            <div class="suggestion-suggested">${suggested}</div>
            <div class="suggestion-diff">
              ${this._generateDiff(original, suggested)}
            </div>
          </div>
          <div class="suggestion-actions">
            <button class="btn-adopt" data-id="${id}">采纳</button>
            <button class="btn-ignore" data-id="${id}">忽略</button>
          </div>
        </div>
      `
      
      this.container.style.display = 'block'
      this.container.style.top = `${rect.bottom + window.scrollY + 5}px`
      this.container.style.left = `${rect.left + window.scrollX}px`
      
      // 使用现代事件绑定方法
      const adoptBtn = this.container.querySelector('.btn-adopt')
      const ignoreBtn = this.container.querySelector('.btn-ignore')
      
      // 移除旧的事件监听器（如果有）
      if (this._adoptListener) {
        adoptBtn.removeEventListener('click', this._adoptListener)
      }
      if (this._ignoreListener) {
        ignoreBtn.removeEventListener('click', this._ignoreListener)
      }
      
      // 添加新的事件监听器
      this._adoptListener = () => {
        this.options.onAdopt && this.options.onAdopt(id)
        this.hideTooltip()
      }
      
      this._ignoreListener = () => {
        this.options.onIgnore && this.options.onIgnore(id)
        this.hideTooltip()
      }
      
      adoptBtn.addEventListener('click', this._adoptListener)
      ignoreBtn.addEventListener('click', this._ignoreListener)
    }
    
    // 生成差异对比
    _generateDiff(original, suggested) {
      // 简单的差异标记
      try {
        if (!original || !suggested) return '';
        
        const words1 = original.split(/\s+/);
        const words2 = suggested.split(/\s+/);
        
        // 寻找第一个不同的词
        let firstDiff = 0;
        while (firstDiff < words1.length && firstDiff < words2.length && 
              words1[firstDiff] === words2[firstDiff]) {
          firstDiff++;
        }
        
        // 找最后一个不同的词（从后往前）
        let lastDiff1 = words1.length - 1;
        let lastDiff2 = words2.length - 1;
        while (lastDiff1 >= 0 && lastDiff2 >= 0 && 
              words1[lastDiff1] === words2[lastDiff2]) {
          lastDiff1--;
          lastDiff2--;
        }
        
        // 提取相同的前缀和后缀
        const prefix = words1.slice(0, firstDiff).join(' ');
        const suffix1 = words1.slice(lastDiff1 + 1).join(' ');
        
        // 提取不同的部分
        const diff1 = words1.slice(firstDiff, lastDiff1 + 1).join(' ');
        const diff2 = words2.slice(firstDiff, lastDiff2 + 1).join(' ');
        
        return `
          <div class="diff-explain">具体差异:</div>
          <div class="diff-content">
            ${prefix ? `<span class="diff-common">${prefix}</span> ` : ''}
            <span class="diff-removed">${diff1}</span> → 
            <span class="diff-added">${diff2}</span>
            ${suffix1 ? ` <span class="diff-common">${suffix1}</span>` : ''}
          </div>
        `;
      } catch (e) {
        console.error('生成差异对比失败:', e);
        return '';
      }
    }
    
    hideTooltip() {
      this.container.style.display = 'none'
    }
    
    applySuggestions(suggestions) {
      this.suggestions = suggestions
      
      // 先清除所有已有的建议标记
      this.clearAllSuggestionFormats()
      
      // 应用新的建议标记
      suggestions.forEach(suggestion => {
        // 在文档中查找建议的原始文本位置
        const content = this.quill.getText()
        let index = content.indexOf(suggestion.original)
        
        if (index !== -1) {
          // 添加建议格式
          this.quill.formatText(index, suggestion.original.length, {
            'suggestion': {
              id: suggestion.id,
              original: suggestion.original,
              suggested: suggestion.suggested
            }
          }, 'api');
        }
      });
    }
    
    clearAllSuggestionFormats() {
      const content = this.quill.getText()
      this.quill.formatText(0, content.length, { 'suggestion': false }, 'api')
    }
    
    // 在组件销毁时断开MutationObserver
    destroy() {
      // 清理观察器
      if (this.observer) {
        this.observer.disconnect()
        this.observer = null
      }
      
      // 清理事件监听器
      if (this.quill && this.quill.root) {
        this.quill.root.removeEventListener('click', this._clickListener)
      }
      
      // 清理按钮事件监听器
      if (this._adoptListener) {
        const adoptBtn = this.container.querySelector('.btn-adopt')
        if (adoptBtn) {
          adoptBtn.removeEventListener('click', this._adoptListener)
        }
      }
      
      if (this._ignoreListener) {
        const ignoreBtn = this.container.querySelector('.btn-ignore')
        if (ignoreBtn) {
          ignoreBtn.removeEventListener('click', this._ignoreListener)
        }
      }
      
      // 移除tooltip容器
      if (this.container && this.container.parentNode) {
        this.container.parentNode.removeChild(this.container)
        this.container = null
      }
    }
  }
  
  window.Quill.register('modules/suggestion', SuggestionModule)
}

export default {
  name: 'ContractDetail',
  components: {
    QuillEditor,
    Download, DocumentAdd, MagicStick, Check, Warning, WarningFilled,
    Document, InfoFilled, Edit, Reading, Close, Loading,
    Timer, Position, Setting, DocumentChecked, Notebook, Plus
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    // 确保contractId是数字类型，且只在合同详情页面有效
    const contractId = computed(() => {
      // 如果不在合同详情页面，直接返回null
      if (route.name !== 'ContractDetail') {
        return null;
      }
      const id = route.params.id;
      return !isNaN(Number(id)) ? Number(id) : null;
    })
    
    // 状态变量和响应式数据
    const activeTab = ref('basicInfo')
    const activeCollapse = ref(['legalCompliance', 'clauseCompleteness', 'riskAlert'])
    const activeSuggestionCollapse = ref(['syntax', 'terminology'])
    
    // 个性化润色偏好设置
    const polishPreferences = reactive({
      style: 'neutral',       // 语言风格：正式严谨、中性专业、简洁明了
      contractType: 'general', // 合同类型：通用、买卖、劳务等
      focus: ['grammar', 'terminology'], // 优化重点：语法、术语、句式、一致性
    })
    
    // 检查偏好设置
    const checkPreferences = reactive({
      legalCompliance: true,  // 法律合规性检查
      completeness: true,     // 条款完整性检查
      riskAlert: true,        // 风险提示检查
      contractType: 'general', // 合同类型参考：通用、买卖、劳务等
      checkDepth: 'standard'  // 检查深度：标准、深度、快速
    })
    
    // 自定义术语管理
    const customTerminologies = ref([])
    const newTerminology = reactive({
      term: ''
    })
    
    // 添加自定义术语
    const addCustomTerminology = () => {
      if (!newTerminology.term.trim()) return
      
      if (!customTerminologies.value.includes(newTerminology.term.trim())) {
        customTerminologies.value.push(newTerminology.term.trim())
        newTerminology.term = ''
        
        // 如果用户添加了术语，自动勾选"术语"优化重点
        if (!polishPreferences.focus.includes('terminology')) {
          polishPreferences.focus.push('terminology')
        }
        
        // 保存到本地存储
        localStorage.setItem('customTerminologies', JSON.stringify(customTerminologies.value))
        
        ElMessage.success('已添加术语')
      } else {
        ElMessage.warning('该术语已存在')
        newTerminology.term = ''
      }
    }
    
    // 移除自定义术语
    const removeCustomTerminology = (index) => {
      customTerminologies.value.splice(index, 1)
      
      // 保存到本地存储
      localStorage.setItem('customTerminologies', JSON.stringify(customTerminologies.value))
    }
    
    const isChecking = ref(false)
    const quillEditor = ref(null)
    const showAiSuggestions = ref(false)
    const isLoading = ref(false)
    const isSaving = ref(false)
    
    // 添加合同编辑区域的引用
    const contractEditContainer = ref(null)
    const aiPolishSidebar = ref(null)
    const editorMainArea = ref(null)
    
    // 添加合同检查区域的引用
    const contractCheckContainer = ref(null)
    const checkSidebar = ref(null)
    const checkResultArea = ref(null)
    
    // 实时AI润色相关状态，改为手动触发
    const isRealTimePolishing = ref(false) // 改为默认关闭
    const realTimePolishLoading = ref(false)
    const lastAnalyzedContent = ref('')
    const lastAnalysisTime = ref(0)
    
    // 内联建议设置
    const enableInlineSuggestions = ref(false) // 控制是否在编辑器中显示内联建议，默认关闭
    
    // 面板折叠状态
    const isAiPanelCollapsed = ref(false)
    
    // 切换面板折叠状态
    const toggleAiPanelCollapse = () => {
      isAiPanelCollapsed.value = !isAiPanelCollapsed.value
    }
    
    // 富文本编辑器配置
    const editorOption = {
      placeholder: '请输入合同内容',
      modules: {
        toolbar: [
          ['bold', 'italic', 'underline', 'strike'],
          ['blockquote', 'code-block'],
          [{ 'header': 1 }, { 'header': 2 }],
          [{ 'list': 'ordered' }, { 'list': 'bullet' }],
          [{ 'script': 'sub' }, { 'script': 'super' }],
          [{ 'indent': '-1' }, { 'indent': '+1' }],
          [{ 'direction': 'rtl' }],
          [{ 'size': ['small', false, 'large', 'huge'] }],
          [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
          [{ 'color': [] }, { 'background': [] }],
          [{ 'font': [] }],
          [{ 'align': [] }],
          ['clean']
        ],
        suggestion: {
          suggestions: [],
          onAdopt: (suggestionId) => {
            adoptInlineEditSuggestion(suggestionId)
          },
          onIgnore: (suggestionId) => {
            ignoreInlineEditSuggestion(suggestionId)
          }
        }
      }
    }
    
    // 合同详情数据
    const contractDetails = reactive({
      id: contractId.value,
      number: '',
      title: '',
      type: '',
      amount: '',
      company: '',
      signDate: '',
      startDate: '',
      expireDate: '',
      content: '',
      status: '',
      created_by: null,
      created_at: '',
      updated_at: '',
      attachments: [],
      actions: []
    })
    
    // 计算合同标题
    const contractTitle = computed(() => {
      return contractDetails.title ? `合同详情: ${contractDetails.number}` : '加载中...'
    })

    // 合同检查结果
    const checkResult = reactive({
      totalIssues: 0,
      criticalIssues: 0,
      warningIssues: 0,
      suggestions: 0,
      legalComplianceIssues: [],
      completenessIssues: [],
      riskAlerts: []
    })

    // AI建议
    const aiSuggestions = reactive({
      syntax: [],
      terminology: []
    })

    // 操作历史 - 从合同actions中获取
    const contractHistory = computed(() => {
      return contractDetails.actions?.map(action => ({
        time: action.created_at,
        content: `${action.user?.username || '系统'} ${action.description}`
      })) || []
    })

    // 获取合同详情
    const getContractDetails = async (loadSilently = false) => {
      try {
        // 检查是否在合同详情页面
        if (route.name !== 'ContractDetail') {
          console.log('不在合同详情页面，跳过加载')
          return
        }
        
        // 检查contractId是否有效
        if (!contractId.value || contractId.value === 'contract' || isNaN(contractId.value)) {
          console.log('无效的合同ID:', contractId.value)
          // 不显示错误消息，只在控制台输出日志
          // ElMessage.error('无效的合同ID')
          router.push({ name: 'Contract' })
          return
        }
        
        isLoading.value = true
        const response = await getContractDetail(contractId.value)
        console.log('合同详情API响应:', response)
        
        // 确保response.data存在，适应request.js中的数据结构处理
        const contractData = response.data || response
        
        // 填充合同详情
        Object.keys(contractDetails).forEach(key => {
          if (key in contractData) {
            contractDetails[key] = contractData[key]
          }
        })
        
        // 特殊处理content字段
        if (contractData.content) {
          contractDetails.content = contractData.content
        } else {
          // 修正默认内容，移除空标签和无意义的省略号
          contractDetails.content = `<p>这里是合同文本内容，请编辑...</p>
<p><strong>甲方：</strong>我方公司名称</p>
<p><strong>乙方：</strong>${contractDetails.company || '对方公司'}</p>`
        }
        
        // 转换日期格式
        if (contractData.sign_date) contractDetails.signDate = contractData.sign_date
        if (contractData.start_date) contractDetails.startDate = contractData.start_date
        if (contractData.expire_date) contractDetails.expireDate = contractData.expire_date
        
        // 格式化金额
        if (contractData.amount) {
          contractDetails.amount = Number(contractData.amount).toLocaleString('zh-CN')
        }
        
        // 只有在非静默加载时才显示成功提示
        if (!loadSilently) {
          ElMessage.success('合同详情加载成功')
        }
      } catch (error) {
        console.error('加载合同详情失败:', error)
        ElMessage.error('加载合同详情失败，请稍后重试')
      } finally {
        isLoading.value = false
      }
    }

    // 返回列表
    const goBack = () => {
      router.push({ name: 'Contract' })
    }

    // 保存更改
    const saveChanges = async () => {
      try {
        isSaving.value = true
        const loading = ElLoading.service({
          lock: true,
          text: '保存中...',
          background: 'rgba(0, 0, 0, 0.7)'
        })
        
        // 准备更新数据
        const isValidDate = (str) => /^\d{4}-\d{2}-\d{2}$/.test(str);
        const isValidAmount = (val) => /^\d+(\.\d{1,2})?$/.test(val);
        const updateData = {
          title: contractDetails.title,
          type: contractDetails.type,
          amount: isValidAmount(contractDetails.amount.replace(/[^\d.]/g, '')) ? contractDetails.amount.replace(/[^\d.]/g, '') : null,
          company: contractDetails.company,
          sign_date: isValidDate(contractDetails.signDate) ? contractDetails.signDate : null,
          start_date: isValidDate(contractDetails.startDate) ? contractDetails.startDate : null,
          expire_date: isValidDate(contractDetails.expireDate) ? contractDetails.expireDate : null,
          content: contractDetails.content
        }
        
        // 调用API保存更新
        await updateContract(contractId.value, updateData)
        
        ElMessage.success('合同更改已保存')
        
        // 重新获取最新数据，静默加载不显示提示
        await getContractDetails(true)
        
        loading.close()
      } catch (error) {
        console.error('保存合同更改失败:', error)
        
        // 添加详细错误信息日志
        if (error.response && error.response.data) {
          console.error('错误响应数据:', error.response.data)
        }
        
        ElMessage.error('保存失败，请检查输入内容和日期格式')
      } finally {
        isSaving.value = false
      }
    }

    // 开始合同检查
    const startContractCheck = async () => {
      console.log("%c========== 开始合同检查 ==========", "background:#3a8ee6;color:white;padding:4px 8px;border-radius:4px;font-weight:bold;");
      console.log("startContractCheck函数被调用");
      
      // 强制修复滚动样式
      if (checkResultArea.value) {
        console.log("确保检查结果区域样式正确");
        
        // 确保check-result-area容器占满高度
        checkResultArea.value.style.height = '100%';
        
        // el-scrollbar将自动处理滚动，不需要额外设置
        console.log("使用el-scrollbar组件处理滚动");
      }
      
      // 不再尝试处理自定义滚动容器，而是完全依赖el-scrollbar
      
      // 尝试检索当前活动的标签
      console.log("当前活动标签：", activeTab.value);
      // 检查HTML是否存在
      if (document.querySelector(".contract-edit-container")) {
        console.log("合同检查容器DOM元素存在");
      } else {
        console.log("警告：合同检查容器DOM元素不存在！");
        // 尝试查找其他可能的容器
        if (document.querySelector(".contract-detail-container")) {
          console.log("发现合同详情容器元素");
        }
        if (document.getElementById("contractCheckContainer")) {
          console.log("通过ID找到合同检查容器元素");
        }
      }
      
      // 检查滚动容器状态
      if (checkResultArea.value) {
        const style = window.getComputedStyle(checkResultArea.value);
        console.log("检查结果区域样式:", {
          display: style.display,
          height: style.height,
          overflow: style.overflow,
          position: style.position
        });
        
        // 强制刷新布局
        console.log("强制刷新检查结果区域布局");
        checkResultArea.value.style.display = 'none';
        setTimeout(() => {
          checkResultArea.value.style.display = 'flex';
          
          // 获取滚动容器并检查
          let scrollWrapper = checkResultArea.value.querySelector('.check-content-scroll-wrapper');
          if (!scrollWrapper) {
            // 兼容el-scrollbar的内部结构
            const scrollbarWrap = checkResultArea.value.querySelector('.el-scrollbar__wrap');
            if (scrollbarWrap) {
              scrollWrapper = scrollbarWrap.querySelector('.check-content-scroll-wrapper');
            }
          }
          if (scrollWrapper) {
            const scrollStyle = window.getComputedStyle(scrollWrapper);
            console.log("滚动容器样式:", {
              height: scrollStyle.height,
              overflow: scrollStyle.overflow,
              position: scrollStyle.position
            });
          } else {
            // 不再报错，只输出一次警告
            console.warn("未找到滚动容器元素（check-content-scroll-wrapper），但不影响功能");
          }
        }, 50);
      } else {
        console.error("checkResultArea引用不存在！");
      }
      
      if (isChecking.value) {
        console.log("已有检查正在进行中，忽略此次点击");
        return;
      }
      
      // 检查合同ID是否有效
      if (!contractId.value || isNaN(contractId.value)) {
        console.error("合同ID无效:", contractId.value);
        ElMessage.error('合同ID无效，无法进行检查');
        return;
      }
      
      // 检查合同内容是否为空
      if (!contractDetails.content) {
        console.log("合同内容为空，提示用户");
        ElMessage.warning('请先在合同文本标签页输入合同内容');
        return;
      }
      
      // 输出关键信息
      console.log("开始执行合同检查 - 详细信息:");
      console.log("合同ID:", contractId.value, typeof contractId.value);
      console.log("内容长度:", contractDetails.content.length);
      console.log("检查偏好设置:", JSON.stringify(checkPreferences, null, 2));
      
      isChecking.value = true;
      aiCheckFinished.value = false;
      let loadingInstance = null;
      
      try {
        // 显示加载提示
        console.log("显示加载提示");
        loadingInstance = ElLoading.service({
          text: 'AI正在分析合同文本，请稍候...',
          background: 'rgba(255, 255, 255, 0.7)'
        });
        
        ElMessage.info('AI分析合同文本中...');
        
        // 准备请求参数，包含个性化设置
        const requestParams = {
          content: contractDetails.content,
          preferences: {
            contract_type: checkPreferences.contractType,
            check_depth: checkPreferences.checkDepth,
            check_areas: []
          }
        };
        
        // 添加检查区域
        if (checkPreferences.legalCompliance) {
          requestParams.preferences.check_areas.push('legal_compliance');
        }
        if (checkPreferences.completeness) {
          requestParams.preferences.check_areas.push('completeness');
        }
        if (checkPreferences.riskAlert) {
          requestParams.preferences.check_areas.push('risk_alert');
        }
        
        // 如果没有选择任何检查区域，默认选择所有区域
        if (requestParams.preferences.check_areas.length === 0) {
          console.log("未选择任何检查区域，使用默认全部检查");
          ElMessage.warning('未选择任何检查区域，将使用默认全部检查');
          requestParams.preferences.check_areas = ['legal_compliance', 'completeness', 'risk_alert'];
          // 同时更新UI中的复选框状态
          checkPreferences.legalCompliance = true;
          checkPreferences.completeness = true;
          checkPreferences.riskAlert = true;
        }
        
        console.log("发送检查请求参数:", JSON.stringify(requestParams, null, 2));
        console.log("发送到API:", `/api/contract/contracts/${contractId.value}/check_contract/`);
        
        // 开始发送请求的时间戳
        const startTime = new Date().getTime();
        console.log("开始请求时间:", new Date().toLocaleTimeString());
        
        // 发送API请求
        const apiResult = await checkContract(contractId.value, requestParams);
        const result = apiResult.data || apiResult; // 兼容响应拦截器包裹data的情况
        
        // 请求结束的时间戳
        const endTime = new Date().getTime();
        console.log("请求完成时间:", new Date().toLocaleTimeString());
        console.log("请求耗时:", (endTime - startTime) / 1000, "秒");
        console.log("收到检查响应:", result);
        
        if (result.error) {
          console.error("合同检查API返回错误:", result.error);
          ElMessage.error(`合同文本检查失败: ${result.error}`);
          return;
        }
        
        // 更新检查结果
        console.log("更新检查结果对象...");
        checkResult.totalIssues = result.totalIssues || 0;
        checkResult.criticalIssues = result.criticalIssues || 0;
        checkResult.warningIssues = result.warningIssues || 0;
        checkResult.suggestions = result.suggestions || 0;
        
        // 更新各项问题
        checkResult.legalComplianceIssues = result.legalComplianceIssues || [];
        checkResult.completenessIssues = result.completenessIssues || [];
        checkResult.riskAlerts = result.riskAlerts || [];
        
        if (checkResult.totalIssues > 0) {
          console.log(`发现${checkResult.totalIssues}个问题，提示用户查看详情`);
          ElMessage.warning(`发现${checkResult.totalIssues}个问题，请查看详情`);
        } else {
          console.log('未发现问题，提示用户合同文本质量良好');
          ElMessage.success('未发现明显问题，合同文本质量良好');
          
          // 在无问题时也自动展开一个分类以显示"未发现问题"的提示
          console.log("无问题时也自动展开法律合规性部分展示空结果");
          activeCollapse.value = ['legalCompliance'];
        }
        
        // 自动展开第一个有问题的部分
        if (checkResult.legalComplianceIssues.length > 0) {
          console.log("自动展开法律合规性部分");
          activeCollapse.value = ['legalCompliance'];
        } else if (checkResult.completenessIssues.length > 0) {
          console.log("自动展开条款完整性部分");
          activeCollapse.value = ['clauseCompleteness'];
        } else if (checkResult.riskAlerts.length > 0) {
          console.log("自动展开风险提示部分");
          activeCollapse.value = ['riskAlert'];
        }
        
        console.log("合同检查完成，结果:", checkResult);
        console.log("%c========== 合同检查完成 ==========", "background:#67c23a;color:white;padding:4px 8px;border-radius:4px;font-weight:bold;");
        
        aiCheckFinished.value = true;
      } catch (error) {
        console.error('%c合同文本检查失败:', 'color:red;font-weight:bold;', error);
        console.error('错误详情:', JSON.stringify(error, null, 2));
        // 尝试提取更多错误信息
        if (error.response) {
          console.error('服务器响应:', error.response.status, error.response.statusText);
          console.error('响应数据:', error.response.data);
        }
        ElMessage.error(`合同文本检查失败: ${error.message || '请稍后重试'}`);
        aiCheckFinished.value = false;
      } finally {
        // 关闭加载提示
        if (loadingInstance) {
          console.log("关闭加载提示");
          loadingInstance.close();
        }
        isChecking.value = false;
        console.log("重置检查状态 isChecking = false");
      }
    };

    // 预计时间提示
    const estimatedTime = computed(() => {
      const content = contractDetails.content || '';
      const charCount = content.length;
      
      // 根据字符数计算预估时间
      if (charCount <= 1000) return '约10秒';
      if (charCount <= 5000) return '约30秒';
      if (charCount <= 15000) return '约1分钟';
      if (charCount <= 30000) return '约2分钟';
      return '2-3分钟';
    });

    // 手动触发文本分析润色功能
    const manualAnalyzeText = async () => {
      // 检查是否有编辑器内容
      if (!contractDetails.content) {
        ElMessage.warning('请先输入合同内容');
        return;
      }
      
      // 清除所有旧的建议和高亮
      clearInlineEditSuggestions();
      aiSuggestions.syntax = [];
      aiSuggestions.terminology = [];
      
      // 强制重置AI面板相关状态
      isAiPanelCollapsed.value = false;
      
      // 更新状态，显示加载
      realTimePolishLoading.value = true;
      
      // 延迟500ms执行，确保加载状态显示
      setTimeout(() => {
        // 强制显示AI建议面板，确保用户能看到加载状态
        showAiSuggestions.value = true;
        console.log("AI分析开始，强制显示AI建议面板");
      }, 500);
      
      // 添加超时计时器
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('分析请求超时，服务器可能繁忙')), 180000); // 3分钟
      });
      
      // 显示加载提示
      const loadingInstance = ElLoading.service({
        text: 'AI正在分析文本，请稍候...',
        background: 'rgba(255, 255, 255, 0.7)'
      });
      
      // 检查文本长度
      const content = contractDetails.content;
      lastAnalyzedContent.value = content;
      lastAnalysisTime.value = Date.now();
      
      if (content.length > 10000) {
        ElMessage.warning('文本较长，分析可能需要较长时间，请耐心等待');
      }
      
      try {
        // 构建请求参数，包含个性化配置
        const requestParams = {
          content: content,
          is_manual: true,  // 标记为手动分析，确保每次都重新分析
          preferences: {
            style: polishPreferences.style,
            contract_type: polishPreferences.contractType,
            focus: polishPreferences.focus,
            custom_terminologies: customTerminologies.value
          }
        };
        
        console.log("发送分析请求，参数:", JSON.stringify(requestParams, null, 2));
        
        // 使用Promise.race竞争方式处理超时
        const result = await Promise.race([
          aiPolishContract(contractId.value, requestParams),
          timeoutPromise
        ]);
        
        console.log("API返回结果:", result);
        
        if (result && !result.error) {
          // 过滤与基本信息相关的建议
          const filterBasicInfoSuggestions = (suggestions) => {
            if (!Array.isArray(suggestions)) return [];
            
            const basicInfoKeywords = [
              '合同名称', '合同编号', '合同金额', '签约对方', '签约日期', 
              '生效日期', '到期日期', '甲方名称', '乙方名称', '标题'
            ];

            return suggestions.filter(suggestion => {
              return !basicInfoKeywords.some(keyword => 
                suggestion.original.includes(keyword) || 
                suggestion.suggested.includes(keyword) || 
                suggestion.explanation.includes(keyword)
              );
            });
          };
          
          // 更新建议，自动显示面板
          if (result.data && result.data.syntax) {
            aiSuggestions.syntax = filterBasicInfoSuggestions(result.data.syntax);
            console.log("语法建议:", aiSuggestions.syntax);
          }
          if (result.data && result.data.terminology) {
            aiSuggestions.terminology = filterBasicInfoSuggestions(result.data.terminology);
            console.log("术语建议:", aiSuggestions.terminology);
          }
            
          // 添加唯一ID
          aiSuggestions.syntax.forEach((s, i) => { s.id = `syntax-${i}`; });
          aiSuggestions.terminology.forEach((s, i) => { s.id = `term-${i}`; });
            
          // 如果启用了内联建议功能，则应用内联建议
          if (enableInlineSuggestions.value) {
            // 延迟一点应用，确保编辑器状态已更新
            setTimeout(() => {
              applyInlineSuggestions();
            }, 100);
          }
          
          // 确保面板显示（如果有建议）
          const totalSuggestions = aiSuggestions.syntax.length + aiSuggestions.terminology.length;
          if (totalSuggestions > 0) {
            showAiSuggestions.value = true;
            console.log("显示AI建议面板，共有建议:", totalSuggestions);
            // 通知用户有新的建议
            ElMessage.success(`AI分析完成：发现${totalSuggestions}条优化建议`);
          } else {
            console.log("未找到任何建议");
            ElMessage.info('AI分析完成，未发现需要优化的内容');
          }
        } else {
          console.error("AI分析返回结果异常:", result);
          ElMessage.warning('AI分析未返回有效结果，请稍后重试');
        }
      } catch (timeoutErr) {
        if (timeoutErr.message.includes('超时')) {
          ElMessageBox.confirm(
            '服务器响应时间过长，可能是文本较长或服务器繁忙。您希望如何处理？',
            '请求超时',
            {
              confirmButtonText: '再试一次',
              cancelButtonText: '取消操作',
              type: 'warning'
            }
          ).then(() => {
            // 用户选择重试
            ElMessage.info('正在重新尝试分析...');
            setTimeout(() => {
              manualAnalyzeText();
            }, 1000);
          }).catch(() => {
            // 用户取消操作
            ElMessage.info('已取消AI分析操作');
          });
        } else {
          throw timeoutErr; // 重新抛出其他类型的错误
        }
      } finally {
        // 关闭加载提示
        if (loadingInstance) {
          loadingInstance.close();
        }
        realTimePolishLoading.value = false;
      }
    };
    
    // 自动更新建议功能：当合同编辑器有变更且长达3秒没有新内容输入，就进行自动分析并提供更新建议
    // 使用防抖(debounce)机制实现，确保只有在用户停止输入3秒后才会触发分析，避免频繁API调用
    // 防抖处理的文本变化处理函数 - 由于改为手动润色，因此不再自动分析
    const debouncedAnalyzeText = debounce(() => {
      // 此处不再自动分析，手动润色时使用 manualAnalyzeText 函数
      console.log('内容已更改，可通过点击"AI润色分析"按钮进行分析');
    }, 3000);
    
    // 调整编辑器高度以适应窗口大小
    const adjustEditorHeight = () => {
      // 根据当前活动的标签页调整不同容器的高度
      console.log("调整高度，当前标签页:", activeTab.value);
      
      // 视口高度和其他通用计算
      const viewHeight = window.innerHeight;
      const marginBottom = 20; // 与CSS中的margin-bottom一致
      
      // 如果是合同文本标签页
      if (activeTab.value === 'contractText') {
        // 确保元素已加载
        if (!contractEditContainer.value || !aiPolishSidebar.value || !editorMainArea.value) {
          console.log("文本编辑容器未加载，跳过高度调整");
          return;
        }
        
        // 计算可用高度
        const containerRect = contractEditContainer.value.getBoundingClientRect();
        const topOffset = containerRect.top;
        
        // 计算理想的容器高度
        const containerHeight = Math.max(viewHeight - topOffset - marginBottom, 500);
        
        // 应用高度到容器
        contractEditContainer.value.style.height = `${containerHeight}px`;
        
        // 如果Quill编辑器已经初始化，刷新其布局
        if (quillEditor.value && quillEditor.value.getQuill) {
          try {
            const quill = quillEditor.value.getQuill();
            if (quill) {
              // 触发Quill布局刷新
              setTimeout(() => {
                quill.update();
              }, 100);
            }
          } catch (e) {
            console.warn('Quill编辑器刷新失败:', e);
          }
        }
      } 
      // 如果是合同检查标签页
      else if (activeTab.value === 'contractCheck') {
        // 确保检查容器已加载
        if (!contractCheckContainer.value) {
          console.log("合同检查容器未加载，跳过高度调整");
          return;
        }
        
        // 计算可用高度
        const containerRect = contractCheckContainer.value.getBoundingClientRect();
        const topOffset = containerRect.top;
        
        // 计算容器高度 - 减小顶部边距，让检查页面更大
        const containerHeight = Math.max(viewHeight - topOffset - marginBottom + 60, 600);
        
        // 应用高度到检查容器
        contractCheckContainer.value.style.height = `${containerHeight}px`;
        console.log("已设置合同检查容器高度:", containerHeight);
      }
    };
    
    // 添加窗口调整大小事件监听器
    const setupResizeListener = () => {
      window.addEventListener('resize', adjustEditorHeight);
      
      // 添加页面可见性变化监听
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
          console.log("页面重新变为可见，调整布局");
          nextTick(() => {
            adjustEditorHeight();
          });
        }
      });
    };
    
    // 清理窗口调整大小事件监听器
    const cleanupResizeListener = () => {
      window.removeEventListener('resize', adjustEditorHeight);
    };
    
    // 监听标签页变化，在激活不同标签页时执行相应操作
    watch(() => activeTab.value, (newTab) => {
      console.log("切换到标签页:", newTab);
      
      if (newTab === 'contractText') {
        // 切换到合同文本标签页
        console.log("处理合同文本标签页切换");
        
        // 调整编辑器高度
        nextTick(() => {
          adjustEditorHeight();
          // 重新设置DOM变化监听
          setupMutationObserver();
        });
        
        // 如果启用了内联建议，应用之前的建议
        if (enableInlineSuggestions.value) {
          setTimeout(() => {
            applyInlineSuggestions();
          }, 500);
        }
      } 
      else if (newTab === 'contractCheck') {
        // 切换到合同检查标签页
        console.log("处理合同检查标签页切换");
        
        // 在DOM更新后调整界面
        nextTick(() => {
          // 检查合同内容是否已加载
          if (contractDetails.content) {
            console.log("合同内容已加载，检查页面准备就绪");
          } else {
            console.log("合同内容未加载，提示用户先输入内容");
            ElMessage.info('请先在合同文本标签页输入合同内容，然后进行AI检查');
          }
          
          // 调整检查界面高度
          adjustEditorHeight();
          
          // 强制刷新滚动容器布局
          if (checkResultArea.value) {
            console.log("强制刷新检查结果区域布局");
            
            // 确保check-result-area容器占满高度
            checkResultArea.value.style.height = '100%';
            
            // el-scrollbar将自动处理滚动，不需要额外设置
            console.log("使用el-scrollbar组件处理滚动");
            
            // 触发重绘
            checkResultArea.value.style.display = 'none';
            setTimeout(() => {
              checkResultArea.value.style.display = 'flex';
            }, 50);
          }
        });
      } 
      else if (newTab === 'history') {
        // 切换到操作记录标签页
        console.log("处理操作记录标签页切换");
        
        // 在DOM更新后调整界面
        nextTick(() => {
          // 检查合同内容是否已加载
          if (contractDetails.content) {
            console.log("合同内容已加载，操作记录页面准备就绪");
          } else {
            console.log("合同内容未加载，提示用户先输入内容");
            ElMessage.info('请先在合同文本标签页输入合同内容，然后进行AI检查');
          }
          
          // 调整操作记录页面高度
          adjustEditorHeight();
          
          // 强制刷新滚动容器布局
          if (checkResultArea.value) {
            console.log("强制刷新检查结果区域布局");
            
            // 确保check-result-area容器占满高度
            checkResultArea.value.style.height = '100%';
            
            // el-scrollbar将自动处理滚动，不需要额外设置
            console.log("使用el-scrollbar组件处理滚动");
            
            // 触发重绘
            checkResultArea.value.style.display = 'none';
            setTimeout(() => {
              checkResultArea.value.style.display = 'flex';
            }, 50);
          }
        });
      } 
      else {
        // 切换到其他标签页
        console.log("切换到其他标签页:", newTab);
        
        // 离开合同文本标签页时，确保隐藏面板
        showAiSuggestions.value = false;
        
        // 清理DOM变化监听器
        if (resizeObserver) {
          resizeObserver.disconnect();
        }
      }
    });

    // 隐藏AI建议面板
    const hideAiPanel = () => {
      // 仅隐藏面板，保持润色功能开启
      showAiSuggestions.value = false
      // 确保下次显示时不是折叠状态
      isAiPanelCollapsed.value = false
      console.log("隐藏面板，showAiSuggestions设置为false")
    }

    // 采纳AI建议
    // eslint-disable-next-line no-unused-vars
    const adoptSuggestion = (type, sugIndex) => {
      const suggestion = aiSuggestions[type][sugIndex]
      
      if (!quillEditor.value || !suggestion) {
        ElMessage.error('编辑器未初始化或建议信息不完整')
        return
      }

      try {
        // 保存当前滚动位置
        const editor = quillEditor.value.getQuill()
        if (!editor) {
          throw new Error('无法获取编辑器实例')
        }
        const currentScrollTop = editor.root ? editor.root.scrollTop : 0

        // 获取编辑器中的纯文本内容和HTML内容
        const content = editor.getText()
        const htmlContent = contractDetails.content

        let replaced = false

        // 创建匹配函数数组 - 从精确到模糊依次尝试
        const matchingMethods = [
          // 1. 精确匹配 - 完全相同
          () => {
            const textIndex = content.indexOf(suggestion.original)
            if (textIndex !== -1) {
              editor.deleteText(textIndex, suggestion.original.length)
              editor.insertText(textIndex, suggestion.suggested)
              return true
            }
            return false
          },
          
          // 2. 去除首尾空格后匹配
          () => {
            const trimmedOriginal = suggestion.original.trim()
            const textIndex = content.indexOf(trimmedOriginal)
            if (textIndex !== -1) {
              editor.deleteText(textIndex, trimmedOriginal.length)
              editor.insertText(textIndex, suggestion.suggested)
              return true
          }
            return false
          },
          
          // 3. 替换多个空格为单个空格后匹配
          () => {
            const normalizedOriginal = suggestion.original.replace(/\s+/g, ' ').trim()
            const normalizedContent = content.replace(/\s+/g, ' ')
            const textIndex = normalizedContent.indexOf(normalizedOriginal)
            if (textIndex !== -1) {
              // 找到真实位置
              const realTextBefore = content.substring(0, textIndex)
              const additionalSpaces = suggestion.original.match(/^\s+/) ? suggestion.original.match(/^\s+/)[0].length : 0
              
              const adjustedIndex = textIndex - (realTextBefore.length - normalizedContent.substring(0, textIndex).length) + additionalSpaces
              const originalLength = suggestion.original.length
              
              editor.deleteText(adjustedIndex, originalLength)
              editor.insertText(adjustedIndex, suggestion.suggested)
              return true
            }
            return false
          },
          
          // 4. 在HTML内容中使用正则表达式查找
          () => {
            try {
            const escapedOriginal = suggestion.original.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
              const regex = new RegExp(escapedOriginal, 'g')
            
              if (htmlContent.match(regex)) {
                const newContent = htmlContent.replace(regex, suggestion.suggested)
                contractDetails.content = newContent
                return true
              }
            } catch (regexError) {
              console.error('正则表达式匹配失败:', regexError)
            }
            return false
          },
          
          // 5. 尝试模糊匹配 - 对特殊情况（如回车符被转换为<br>等）进行处理
          () => {
            try {
              // 处理可能的换行符差异
              const originalWithNormalizedBreaks = suggestion.original.replace(/[\r\n]+/g, ' ').trim()
              const contentWithNormalizedBreaks = content.replace(/[\r\n]+/g, ' ')
              
              const textIndex = contentWithNormalizedBreaks.indexOf(originalWithNormalizedBreaks)
              if (textIndex !== -1) {
                // 找到大致位置后进行替换
                let startPosition = textIndex
                
                // 在编辑器中查找最佳的起始位置
                const length = suggestion.original.length
                editor.deleteText(startPosition, length)
                editor.insertText(startPosition, suggestion.suggested)
                return true
              }
            } catch (error) {
              console.error('模糊匹配失败:', error)
            }
            return false
          }
        ]

        // 依次尝试各种匹配方法
        for (const matchMethod of matchingMethods) {
          if (matchMethod()) {
            replaced = true
            break
          }
        }

        // 如果成功替换了内容
        if (replaced) {
          // 从建议列表中移除 - 确保使用正确的索引参数
          aiSuggestions[type].splice(sugIndex, 1)
          ElMessage.success('已采纳建议')
          
          // 恢复滚动位置
          setTimeout(() => {
            if (editor && editor.root) {
              editor.root.scrollTop = currentScrollTop
            }
          }, 10)
          
          // 如果启用了内联建议，重新应用剩余的高亮
          if (enableInlineSuggestions.value) {
            clearInlineEditSuggestions()
            if (aiSuggestions.syntax.length > 0 || aiSuggestions.terminology.length > 0) {
              setTimeout(() => applyInlineSuggestions(), 100)
            }
          }
        } else {
          ElMessage.warning('无法找到匹配的文本，请手动编辑')
          console.warn('未能找到匹配文本:', suggestion.original)
        }
        } catch (error) {
          console.error('采纳建议出错:', error)
        ElMessage.error('采纳建议时出错: ' + (error.message || '未知错误'))
      }
    }

    // 忽略AI建议
    // eslint-disable-next-line no-unused-vars
    const ignoreSuggestion = (type, sugIndex) => {
      aiSuggestions[type].splice(sugIndex, 1)
      ElMessage.info('已忽略建议')
      
      // 如果启用了内联建议，重新应用剩余的高亮
      if (enableInlineSuggestions.value) {
        clearInlineEditSuggestions()
        if (aiSuggestions.syntax.length > 0 || aiSuggestions.terminology.length > 0) {
          setTimeout(() => applyInlineSuggestions(), 100)
        }
      }
    }

    // 应用所有采纳的建议
    // eslint-disable-next-line no-unused-vars
    const applyAllSuggestions = async () => {
      // 检查是否有要应用的建议
      if (aiSuggestions.syntax.length === 0 && aiSuggestions.terminology.length === 0) {
        ElMessage.info('没有待处理的建议');
        return;
      }
      
      try {
        const loading = ElLoading.service({
          lock: true,
          text: '应用所有建议...',
          background: 'rgba(0, 0, 0, 0.7)'
        });
        
        // 获取Quill编辑器实例
        if (!quillEditor.value || !quillEditor.value.getQuill) {
          throw new Error('编辑器未初始化');
        }
        const editor = quillEditor.value.getQuill();
        if (!editor) {
          throw new Error('无法获取编辑器实例');
        }
        
        // 保存当前滚动位置
        const currentScrollTop = editor.root ? editor.root.scrollTop : 0;
        
        // 获取编辑器当前文本内容
        const editorText = editor.getText();
        
        // 将所有建议合并到一个数组
        const allSuggestions = [...aiSuggestions.syntax, ...aiSuggestions.terminology];
        
        // 创建高级文本匹配函数
        const findBestMatch = (suggestion, content) => {
          // 各种匹配方法，返回索引和长度
          const methods = [
            // 1. 精确匹配
            () => {
              const index = content.indexOf(suggestion.original);
              return index !== -1 ? { index, length: suggestion.original.length } : null;
            },
            // 2. 去除首尾空格后匹配
            () => {
              const trimmedOriginal = suggestion.original.trim();
              const index = content.indexOf(trimmedOriginal);
              return index !== -1 ? { index, length: trimmedOriginal.length } : null;
            },
            // 3. 替换多个空格为单个空格
            () => {
              const normalizedOriginal = suggestion.original.replace(/\s+/g, ' ').trim();
              const normalizedContent = content.replace(/\s+/g, ' ');
              const index = normalizedContent.indexOf(normalizedOriginal);
              
              if (index !== -1) {
                // 计算真实位置
                const realTextBefore = content.substring(0, index);
                const offset = realTextBefore.length - realTextBefore.replace(/\s/g, '').length;
                const adjustedIndex = Math.max(0, index - offset);
                return { index: adjustedIndex, length: suggestion.original.length };
              }
              return null;
            },
            // 4. 处理换行符差异
            () => {
              const originalWithNormalizedBreaks = suggestion.original.replace(/[\r\n]+/g, ' ').trim();
              const contentWithNormalizedBreaks = content.replace(/[\r\n]+/g, ' ');
              
              const index = contentWithNormalizedBreaks.indexOf(originalWithNormalizedBreaks);
              if (index !== -1) {
                return { index, length: suggestion.original.length };
              }
              return null;
            }
          ];
          
          // 尝试所有方法找到最佳匹配
          for (const method of methods) {
            const result = method();
            if (result) return result;
          }
          
          return null; // 没有找到匹配
        };
        
        // 增强的索引查找
        const enhancedSuggestions = allSuggestions.map(suggestion => {
          const match = findBestMatch(suggestion, editorText);
          return match ? { ...suggestion, index: match.index, length: match.length } : { ...suggestion, index: -1 };
        }).filter(suggestion => suggestion.index !== -1);
        
        // 按照从后向前的顺序排序
        const sortedSuggestions = enhancedSuggestions.sort((a, b) => b.index - a.index);
        
        if (sortedSuggestions.length === 0) {
          loading.close();
          ElMessage.warning('未能找到任何匹配的建议文本');
          return;
        }
        
        // 记录成功和失败的次数
        let successCount = 0;
        let failCount = 0;
        
        // 从后往前逐个应用建议（避免前面的替换影响后面的索引）
        for (const suggestion of sortedSuggestions) {
          try {
            // 使用Quill API直接替换文本
            editor.deleteText(suggestion.index, suggestion.length);
            editor.insertText(suggestion.index, suggestion.suggested);
            successCount++;
          } catch (error) {
            console.error('替换建议失败:', error, suggestion);
            failCount++;
          }
        }
          
        // 清空建议列表
          aiSuggestions.syntax = [];
          aiSuggestions.terminology = [];
          
        // 恢复滚动位置
        setTimeout(() => {
          if (editor && editor.root) {
            editor.root.scrollTop = currentScrollTop;
          }
        }, 10);
        
        // 显示结果信息
        ElMessage.success(`成功应用${successCount}项建议${failCount > 0 ? `，${failCount}项失败` : ''}`);
        
        // 关闭加载提示
        loading.close();
        
        // 隐藏AI面板
        hideAiPanel();
        
      } catch (error) {
        console.error('应用所有建议失败:', error);
        ElMessage.error('应用所有建议失败: ' + (error.message || '未知错误'));
      }
    }

    // 下载合同
    // eslint-disable-next-line no-unused-vars
    const downloadContract = () => {
      isSaving.value = true;
      const loading = ElLoading.service({
        lock: true,
        text: '正在保存并生成Word文档...',
        background: 'rgba(0, 0, 0, 0.7)'
      });
      // 统一日期处理
      const normalizeDate = (val) => {
        if (!val) return null;
        if (typeof val === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(val)) return val;
        return null;
      };
      const isValidAmount = (val) => /^\d+(\.\d{1,2})?$/.test(val);
      const updateData = {
        title: contractDetails.title,
        type: contractDetails.type,
        amount: isValidAmount(contractDetails.amount.replace(/[^\d.]/g, '')) ? contractDetails.amount.replace(/[^\d.]/g, '') : null,
        company: contractDetails.company,
        sign_date: normalizeDate(contractDetails.signDate),
        start_date: normalizeDate(contractDetails.startDate),
        expire_date: normalizeDate(contractDetails.expireDate),
        content: contractDetails.content
      };
      updateContract(contractId.value, updateData)
        .then(() => {
          // 保存成功后调用下载API
          const downloadUrl = `/api/contract/contracts/${contractId.value}/download-docx/`;
          
          // 获取CSRF令牌 - 从Cookie中获取
          const getCookie = (name) => {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return '';
          };
          const csrfToken = getCookie('csrftoken');
          console.log('CSRF令牌:', csrfToken || '未找到');
          console.log('认证Cookie:', document.cookie);
          
          // 获取认证令牌
          const token = localStorage.getItem('token');
          console.log('认证令牌:', token ? '找到' : '未找到');
          
          // 使用axios直接下载文件，确保包含认证信息
          request({
            url: downloadUrl,
            method: 'GET',
            responseType: 'blob',
            headers: {
              'X-CSRFToken': csrfToken,
              'Authorization': token ? `Bearer ${token}` : ''
            }
          })
          .then(response => {
            // 创建Blob URL并下载
            const blob = new Blob([response.data], {
              type: response.headers['content-type'] || 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${contractDetails.number || '合同'}_${contractDetails.title || '未命名'}.docx`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            ElMessage.success('合同已保存并下载');
          })
          .catch(error => {
            console.error('下载合同出错:', error);
            ElMessage.error(`下载失败: ${error.message || '权限验证失败'}`);
          });
        })
        .catch(error => {
          console.error('保存合同出错:', error);
          ElMessage.error('保存失败，无法下载合同');
        })
        .finally(() => {
          loading.close();
          isSaving.value = false;
        });
    }
    
    // 查看法规详情
    // eslint-disable-next-line no-unused-vars
    const viewRegulation = (issue) => {
      // 使用全屏加载动画
      const loadingInstance = ElLoading.service({
        text: '正在查询相关法规...',
        background: 'rgba(255, 255, 255, 0.7)'
      });
      
      // 使用request模块调用后端API获取法规详情
      request({
        url: '/api/contract/regulation-query/',
        method: 'post',
        data: {
          issue_title: issue.title,
          issue_content: issue.current,
          issue_problem: issue.problem,
          contract_type: contractDetails.type
        }
      })
      .then(data => {
        loadingInstance.close();
        
        // 展示AI生成的法规详情
        ElMessageBox.alert(
          `<div class="regulation-detail">
            <h4>适用法规: ${data.regulation || '《中华人民共和国合同法》'}</h4>
            <div class="regulation-content">
              <p>${data.regulation_content || '根据相关法律法规，合同中应明确约定双方权利义务，避免含糊不清的条款。'}</p>
            </div>
            <div class="regulation-suggestion mt-2">
              <h5>修改建议:</h5>
              <p>${data.suggestion || '建议参照相关法律法规，明确表述合同条款，确保合同的有效性和可执行性。'}</p>
            </div>
          </div>`,
          '法规详情',
          {
            dangerouslyUseHTMLString: true,
            confirmButtonText: '了解',
            customClass: 'regulation-dialog'
          }
        );
      })
      .catch(error => {
        loadingInstance.close();
        console.error('获取法规详情失败:', error);
        ElMessage.error('获取法规详情失败，请稍后再试');
      });
    }

    // 监听路由变化
    watch(() => route.name, (newRouteName, oldRouteName) => {
      if (oldRouteName === 'ContractDetail' && newRouteName !== 'ContractDetail') {
        // 离开合同详情页面，确保重置状态
        console.log('离开合同详情页面，重置状态')
        contractId.value = null
        // 关闭所有加载状态
        isLoading.value = false
        isSaving.value = false
        realTimePolishLoading.value = false
        isChecking.value = false
      }
    }, { immediate: true })

    // 监听路由变化，重新加载数据
    watch(() => route.params.id, (newId, oldId) => {
      if (route.name === 'ContractDetail') {
        if (newId && newId !== 'undefined' && !isNaN(Number(newId))) {
          // 转换为数字进行比较
          const numNewId = Number(newId);
          const numOldId = oldId ? Number(oldId) : null;
          
          // 只有ID真正变化时才重新加载
          if (numNewId !== numOldId) {
            console.log('合同ID已变更，加载新合同', newId)
            contractId.value = numNewId
            
            // 如果是组件刚刚挂载，使用静默加载避免重复提示
            const silentLoad = !oldId || document.readyState !== 'complete';
            getContractDetails(silentLoad)
          }
        } else {
          console.log('无效的合同ID参数:', newId)
          router.push({ name: 'Contract' })
        }
      }
    }, { immediate: true })

    // 添加展开按钮到DOM
    const addFloatingButton = () => {
      // 如果按钮已存在，先移除
      const existingButton = document.getElementById('aiFloatingButton')
      if (existingButton) {
        document.body.removeChild(existingButton)
      }

      // 创建新按钮
      const button = document.createElement('div')
      button.id = 'aiFloatingButton'
      button.className = 'ai-floating-button'
      button.innerHTML = `
        <button class="el-button el-button--primary el-button--small is-circle">
          <i class="el-icon">
            <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
              <path fill="currentColor" d="M512 64a448 448 0 1 1 0 896 448 448 0 0 1 0-896zm0 832a384 384 0 0 0 0-768 384 384 0 0 0 0 768zm-94.656-298.656a32 32 0
                0 0 45.312 45.312l96-96a32 32 0 0 0 0-45.312l-96-96a32 32 0 0 0-45.312 45.312L466.752 512l-49.408 49.344z"></path>
            </svg>
          </i>
        </button>
      `
      
      // 添加样式
      const style = document.createElement('style')
      style.textContent = `
        .ai-floating-button {
          position: fixed;
          top: 50%;
          right: 0;
          transform: translateY(-50%);
          z-index: 2000;
          background-color: #fff;
          border-top-left-radius: 50%;
          border-bottom-left-radius: 50%;
          box-shadow: -2px 0 10px rgba(0,0,0,0.1);
          padding: 10px 5px 10px 10px;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        .ai-floating-button:hover {
          right: 5px;
        }
        .ai-floating-button button {
          margin: 0;
        }
      `
      document.head.appendChild(style)
      
      // 添加点击事件
      button.addEventListener('click', () => {
        showAiSuggestions.value = true
        console.log('点击展开按钮，showAiSuggestions设置为true')
      })
      
      // 添加到body
      document.body.appendChild(button)
    }
    
    // 更新展开按钮的显示状态
    const updateFloatingButton = () => {
      const button = document.getElementById('aiFloatingButton')
      if (!button) return
      
      if (activeTab.value === 'contractText' && !showAiSuggestions.value) {
        button.style.display = 'block'
      } else {
        button.style.display = 'none'
      }
    }
    
    // 监听showAiSuggestions和activeTab的变化，更新按钮显示状态
    watch([showAiSuggestions, activeTab], () => {
      updateFloatingButton()
    })
    
    // 采纳内联编辑器中的建议
    const adoptInlineEditSuggestion = (suggestionId) => {
      try {
        console.log('开始采纳建议:', suggestionId);
        // 在语法建议中查找
        let suggestionFound = false;
        let suggestionType = null;
        let suggestionIndex = -1;

      // 在语法建议中查找
        for (let i = 0; i < aiSuggestions.syntax.length; i++) {
          if (aiSuggestions.syntax[i].id === suggestionId) {
            suggestionFound = true;
            suggestionType = 'syntax';
            suggestionIndex = i;
            break;
          }
        }

        // 在术语建议中查找
        if (!suggestionFound) {
          for (let i = 0; i < aiSuggestions.terminology.length; i++) {
            if (aiSuggestions.terminology[i].id === suggestionId) {
              suggestionFound = true;
              suggestionType = 'terminology';
              suggestionIndex = i;
              break;
        }
      }
        }

        // 如果找到了建议，调用采纳函数
        if (suggestionFound && suggestionType && suggestionIndex > -1) {
          console.log('找到建议位置:', suggestionType, suggestionIndex);
          adoptSuggestion(suggestionType, suggestionIndex);
          return true;
        } else {
          console.error('未找到对应建议:', suggestionId);
          ElMessage.warning('无法找到对应的建议，请从侧边栏采纳');
          return false;
        }
      } catch (error) {
        console.error('采纳内联建议失败:', error);
        ElMessage.error('采纳建议失败: ' + (error.message || '未知错误'));
        return false;
      }
    };
    
    // 忽略内联编辑器中的建议
    const ignoreInlineEditSuggestion = (suggestionId) => {
      try {
        console.log('开始忽略建议:', suggestionId);
        // 在语法建议中查找
        let suggestionFound = false;
        let suggestionType = null;
        let suggestionIndex = -1;

      // 在语法建议中查找
        for (let i = 0; i < aiSuggestions.syntax.length; i++) {
          if (aiSuggestions.syntax[i].id === suggestionId) {
            suggestionFound = true;
            suggestionType = 'syntax';
            suggestionIndex = i;
            break;
          }
        }

        // 在术语建议中查找
        if (!suggestionFound) {
          for (let i = 0; i < aiSuggestions.terminology.length; i++) {
            if (aiSuggestions.terminology[i].id === suggestionId) {
              suggestionFound = true;
              suggestionType = 'terminology';
              suggestionIndex = i;
              break;
        }
      }
        }

        // 如果找到了建议，调用忽略函数
        if (suggestionFound && suggestionType && suggestionIndex > -1) {
          ignoreSuggestion(suggestionType, suggestionIndex);
          return true;
        } else {
          console.warn('未找到要忽略的建议:', suggestionId);
          return false;
        }
      } catch (error) {
        console.error('忽略建议出错:', error);
        ElMessage.error('忽略建议失败: ' + (error.message || '未知错误'));
        return false;
        }
    };

    // 更安全地获取Quill编辑器DOM元素的辅助函数
    const getQuillEditorElement = () => {
      try {
        if (!quillEditor.value) return null;
        
        // 尝试不同的方式获取编辑器DOM元素
        if (quillEditor.value.$el && typeof quillEditor.value.$el.querySelector === 'function') {
          // Vue组件实例方式
          return quillEditor.value.$el.querySelector('.ql-editor');
        } else if (quillEditor.value.container) {
          // 原生Quill实例方式
          return quillEditor.value.container.querySelector('.ql-editor');
        } else if (quillEditor.value.getQuill) {
          // @vueup/vue-quill方式
          const quill = quillEditor.value.getQuill();
          if (quill && quill.root) {
            return quill.root;
          }
        }
        
        // 最后尝试直接在文档中查找
        return document.querySelector('.contract-text-editor .ql-editor');
      } catch (e) {
        console.error('获取编辑器元素失败:', e);
        return null;
      }
    };

    // 清除所有内联编辑建议
    const clearInlineEditSuggestions = () => {
      const editorContainer = getQuillEditorElement();
      if (!editorContainer) {
        console.warn('无法获取编辑器元素，跳过清除操作');
        return;
      }
      
      try {
        // 查找所有建议高亮元素
        const highlights = editorContainer.querySelectorAll('.suggestion-highlight');
        
        // 替换回普通文本
        highlights.forEach(span => {
          const text = span.textContent;
          const parent = span.parentNode;
          if (parent) {
            const textNode = document.createTextNode(text);
            parent.replaceChild(textNode, span);
          }
        });
      } catch (e) {
        console.error('清除建议高亮失败:', e);
      }
    }
    
    // 修复应用内联建议函数
    const applyInlineSuggestions = () => {
      try {
        // 获取当前所有建议
        const allSuggestions = [
          ...(aiSuggestions.syntax || []), 
          ...(aiSuggestions.terminology || [])
        ];
        
        if (!allSuggestions.length) {
          return;
        }
        
        // 先清除所有现有高亮
        clearInlineEditSuggestions();
        
        // 获取编辑器DOM和Quill实例
        const editorContainer = getQuillEditorElement();
        if (!editorContainer) {
          console.warn('无法获取编辑器元素，无法应用内联建议');
          showAiSuggestions.value = true; // 如果无法应用内联建议，显示侧边栏
          return;
        }
        
        // 获取Quill实例
        const editor = quillEditor.value?.getQuill();
        if (!editor) {
          console.warn('无法获取Quill编辑器实例');
          return;
        }
        
        // 提取纯文本内容，用于更准确地匹配
        const plainText = editor.getText();
        
        // 成功匹配的建议数量
        let matchedCount = 0;
        
        // 预处理文本以提高匹配精度
        const normalizeText = (text) => {
          return text.replace(/\s+/g, ' ').trim();
        };
        
        // 优先按照长度从长到短排序建议，避免短文本错误匹配
        const sortedSuggestions = [...allSuggestions].sort((a, b) => 
          b.original.length - a.original.length
        );
        
        // 使用更精确的匹配方法
        const findTextPosition = (text, searchText) => {
          // 直接匹配
          const directIndex = text.indexOf(searchText);
          if (directIndex !== -1) {
            return { index: directIndex, length: searchText.length };
          }
          
          // 去除首尾空格匹配
          const trimmedSearch = searchText.trim();
          const trimmedIndex = text.indexOf(trimmedSearch);
          if (trimmedIndex !== -1) {
            return { index: trimmedIndex, length: trimmedSearch.length };
          }
          
          // 规范化空格后匹配
          const normalizedText = normalizeText(text);
          const normalizedSearch = normalizeText(searchText);
          const normalizedIndex = normalizedText.indexOf(normalizedSearch);
          
          if (normalizedIndex !== -1) {
            // 尝试映射回原始文本的实际位置
            let realIndex = -1;
            let normalizedPos = 0;
            
            // 字符一一对应查找真实位置
            for (let i = 0; i < text.length; i++) {
              if (normalizeText(text.substring(0, i+1)).length > normalizedPos) {
                normalizedPos++;
              }
              
              if (normalizedPos === normalizedIndex + 1) {
                realIndex = i - normalizedSearch.length + 1;
                break;
              }
            }
            
            if (realIndex !== -1) {
              return { index: realIndex, length: searchText.length };
            }
          }
          
          return { index: -1, length: 0 };
        };
        
        // 遍历所有建议并应用高亮
        sortedSuggestions.forEach(suggestion => {
          try {
            // 忽略空的原始文本
            if (!suggestion.original || suggestion.original.length === 0) {
              console.warn('忽略空的原始文本建议');
              return;
            }

            // 使用改进的文本位置查找
            const position = findTextPosition(plainText, suggestion.original);
            
            if (position.index === -1) {
              console.warn(`未找到原始文本: "${suggestion.original.substring(0, 30)}${suggestion.original.length > 30 ? '...' : ''}"，跳过高亮。`);
              return;
            }
            
            // 确保每个建议有一个唯一标识符
            if (!suggestion.id) {
              suggestion.id = `suggestion-${Math.random().toString(36).substring(2, 9)}`;
            }
            
            try {
              // 创建一个Quill格式对象用于高亮
              const highlightFormat = {
                'background-color': 'rgba(255, 217, 102, 0.3)',
                'border-bottom': '1px dashed #ffb300',
                'cursor': 'pointer',
                'data-suggestion-id': suggestion.id,
                'data-original': suggestion.original,
                'data-suggested': suggestion.suggested,
                'data-explanation': suggestion.explanation || '',
                'title': '点击查看修改建议',
                'class': 'suggestion-highlight',
                'style': 'pointer-events: auto !important; cursor: pointer !important; z-index: 9999 !important; position: relative !important;'
              };
              
              // 应用格式
              editor.formatText(position.index, position.length, highlightFormat, 'api');
              
              // 延迟处理，确保DOM已更新
              setTimeout(() => {
                // 使用document.querySelectorAll进行全局查找，可能更可靠
                const spans = document.querySelectorAll(`[data-suggestion-id="${suggestion.id}"]`);
                if (spans.length > 0) {
                  spans.forEach(span => {
                    // 强制确保属性正确保存
                    span.setAttribute('data-original', suggestion.original);
                    span.setAttribute('data-suggested', suggestion.suggested);
                    if (suggestion.explanation) {
                      span.setAttribute('data-explanation', suggestion.explanation);
                    }
                    
                    // 直接操作DOM样式，确保可点击
                    span.style.setProperty('pointer-events', 'auto', 'important');
                    span.style.setProperty('cursor', 'pointer', 'important');
                    span.style.setProperty('position', 'relative', 'important');
                    span.style.setProperty('z-index', '9999', 'important');
                    span.classList.add('suggestion-highlight');
                    
                    // 加强点击处理：使用多种事件绑定方式
                    // 方式1：标准事件监听器
                    span.addEventListener('click', function(e) {
                      e.preventDefault();
                      e.stopPropagation();
                      console.log('高亮元素点击 - addEventListener:', suggestion.id);
                      handleHighlightElement(span, e);
                    }, true);
                    
                    // 方式2：内联onclick属性（兼容性更好）
                    span.onclick = function(e) {
                      e.preventDefault();
                      e.stopPropagation();
                      console.log('高亮元素点击 - onclick:', suggestion.id);
                      handleHighlightElement(span, e);
                    };
                  });
                } else {
                  console.warn(`未找到高亮元素 ID:${suggestion.id}`);
                }
              }, 200); // 增加延迟以确保DOM更新
              
              matchedCount++;
            } catch (e) {
              console.error('应用Quill格式失败:', e);
              
              // DOM回退方案代码保持不变
              // ... existing code ...
            }
          } catch (e) {
            console.error('处理建议失败:', e, suggestion);
          }
        });
        
        // 通知用户
        if (matchedCount > 0) {
          ElMessage.info(`在编辑器中高亮了${matchedCount}条建议修改，点击高亮部分可查看详情`);
          
          // 添加document级别的事件委托，作为额外的保障
          document.removeEventListener('click', documentHighlightClickHandler, true);
          document.addEventListener('click', documentHighlightClickHandler, true);
          console.log('添加文档级高亮点击事件委托');
          
          // 确保事件监听器正确添加到编辑器
          const editorElement = getQuillEditorElement();
          if (editorElement) {
            // 先移除之前可能存在的事件监听器
            editorElement.removeEventListener('click', delegatedHighlightClick, true);
            // 重新添加事件监听器，使用捕获阶段（第三个参数为true）
            editorElement.addEventListener('click', delegatedHighlightClick, true);
            console.log('已重新绑定编辑器高亮点击事件');
          }
        } else if (allSuggestions.length > 0) {
          ElMessage.warning('无法在当前文本中匹配建议内容，建议在侧边栏查看');
          showAiSuggestions.value = true;
        }
      } catch (error) {
        console.error('应用内联建议失败:', error);
        showAiSuggestions.value = true; // 如果内联失败，显示侧边栏
      }
    };
    
    // 显示建议工具提示
    const showSuggestionTooltip = (element, suggestion, tooltipContainer) => {
      const rect = element.getBoundingClientRect()
      
      // 清除现有内容和事件监听器
      tooltipContainer.innerHTML = ''
      
      // 记录当前活跃的tooltip，以便后续引用
      window.activeSuggestionTooltip = tooltipContainer
      
      // 生成差异对比（使用增强版算法）
      let diffHtml = '';
      if (window.enhancedDiffDisplay) {
        // 使用补丁中提供的增强版差异算法
        diffHtml = window.enhancedDiffDisplay(suggestion.original, suggestion.suggested);
      } else {
        // 回退到简单版本
        diffHtml = generateDiff(suggestion.original, suggestion.suggested);
      }
      
      // 设置工具提示内容
      const content = document.createElement('div')
      content.className = 'suggestion-tooltip-content'
      content.innerHTML = `
        <div class="suggestion-tooltip-header">
          <span class="suggestion-tooltip-title">AI文本优化建议</span>
          <span class="suggestion-tooltip-close">&times;</span>
        </div>
        <div class="suggestion-tooltip-body">
          <div class="suggestion-comparison">
            <div class="suggestion-column">
              <div class="suggestion-label">原文本:</div>
              <div class="suggestion-original">${escapeHtml(suggestion.original)}</div>
            </div>
            <div class="suggestion-divider"></div>
            <div class="suggestion-column">
              <div class="suggestion-label">建议修改为:</div>
              <div class="suggestion-suggested">${escapeHtml(suggestion.suggested)}</div>
            </div>
          </div>
          <div class="suggestion-diff-container">
            <div class="suggestion-label">差异对比:</div>
            <div class="suggestion-diff">${diffHtml}</div>
          </div>
          ${suggestion.explanation ? `
          <div class="suggestion-explanation-container">
            <div class="suggestion-label">修改说明:</div>
            <div class="suggestion-explanation">${escapeHtml(suggestion.explanation)}</div>
          </div>` : ''}
        </div>
        <div class="suggestion-actions">
          <button class="btn-adopt" type="button">采纳此建议</button>
          <button class="btn-ignore" type="button">忽略</button>
        </div>
      `
      
      tooltipContainer.appendChild(content)
      
      // 定位工具提示 - 使用CSS而非内联样式
      tooltipContainer.style.position = 'absolute'
      tooltipContainer.style.top = `${rect.bottom + window.scrollY + 5}px`
      tooltipContainer.style.left = `${rect.left + window.scrollX}px`
      tooltipContainer.style.display = 'block'
      
      // 确保tooltip在视口内
      setTimeout(() => {
        const tooltipRect = tooltipContainer.getBoundingClientRect();
        if (tooltipRect.right > window.innerWidth) {
          tooltipContainer.style.left = `${Math.max(10, window.innerWidth - tooltipRect.width - 10)}px`;
        }
        if (tooltipRect.bottom > window.innerHeight) {
          tooltipContainer.style.top = `${Math.max(10, window.innerHeight - tooltipRect.height - 10) + window.scrollY}px`;
        }
      }, 0);
      
      // 添加按钮事件
      const adoptBtn = tooltipContainer.querySelector('.btn-adopt')
      const ignoreBtn = tooltipContainer.querySelector('.btn-ignore')
      const closeBtn = tooltipContainer.querySelector('.suggestion-tooltip-close')
      
      // 移除旧的事件监听器，避免重复绑定
      const oldAdoptBtn = adoptBtn.cloneNode(true);
      const oldIgnoreBtn = ignoreBtn.cloneNode(true);
      const oldCloseBtn = closeBtn.cloneNode(true);
      
      adoptBtn.parentNode.replaceChild(oldAdoptBtn, adoptBtn);
      ignoreBtn.parentNode.replaceChild(oldIgnoreBtn, ignoreBtn);
      closeBtn.parentNode.replaceChild(oldCloseBtn, closeBtn);
      
      // 添加新的事件监听器
      oldAdoptBtn.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        console.log('采纳建议:', suggestion.id);
        try {
          adoptInlineEditSuggestion(suggestion.id);
          tooltipContainer.style.display = 'none';
        } catch (error) {
          console.error('采纳建议出错:', error);
          ElMessage.error('采纳建议时出错，请稍后再试');
        }
      })
      
      oldIgnoreBtn.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        console.log('忽略建议:', suggestion.id);
        try {
          ignoreInlineEditSuggestion(suggestion.id);
          tooltipContainer.style.display = 'none';
        } catch (error) {
          console.error('忽略建议出错:', error);
          ElMessage.error('忽略建议时出错，请稍后再试');
        }
      })
      
      oldCloseBtn.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        tooltipContainer.style.display = 'none';
      })
      
      // 点击外部隐藏工具提示
      const clickOutsideHandler = (e) => {
        if (!tooltipContainer.contains(e.target) && 
            !element.contains(e.target)) {
          tooltipContainer.style.display = 'none';
          document.removeEventListener('click', clickOutsideHandler);
        }
      }
      
      // 确保不会连续触发
      setTimeout(() => {
        document.removeEventListener('click', clickOutsideHandler); // 先移除可能存在的处理器
        document.addEventListener('click', clickOutsideHandler);
      }, 100)
    }
    
    // 转义HTML特殊字符
    const escapeHtml = (unsafe) => {
      return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }
    
    // 生成差异对比（简单版本，作为备用）
    const generateDiff = (original, suggested) => {
      try {
        if (!original || !suggested) return ''
        
        // 使用更精确的分词方法
        const tokenize = (text) => {
          // 保留标点符号作为单独的标记，同时保持中文字符的完整性
          return text.split(/([,.!?;:，。！？；：\s]+|[\u4e00-\u9fa5])/g).filter(token => token !== '');
        };
        
        const tokens1 = tokenize(original);
        const tokens2 = tokenize(suggested);
        
        // 构建差异HTML
        let html = '<div class="diff-content">';
        
        // 使用改进的差异对比算法
        const matched = new Set(); // 记录已匹配的索引
        
        // 第一步：找出完全相同的部分
        const commonParts = [];
        for (let i1 = 0; i1 < tokens1.length; i1++) {
          for (let j1 = 0; j1 < tokens2.length; j1++) {
            if (tokens1[i1] === tokens2[j1] && !matched.has(`2:${j1}`)) {
              commonParts.push({ index1: i1, index2: j1, token: tokens1[i1] });
              matched.add(`2:${j1}`);
              break;
            }
          }
        }
        
        // 按照第二个文本的顺序排序
        commonParts.sort((a, b) => a.index2 - b.index2);
        
        // 第二步：根据共同部分构建差异
        let lastIndex1 = -1;
        let lastIndex2 = -1;
        
        for (const part of commonParts) {
          // 处理第一个文本中的删除部分
          if (part.index1 > lastIndex1 + 1) {
            html += '<span class="diff-removed">';
            for (let k = lastIndex1 + 1; k < part.index1; k++) {
              html += escapeHtml(tokens1[k]);
            }
            html += '</span>';
          }
          
          // 处理第二个文本中的添加部分
          if (part.index2 > lastIndex2 + 1) {
            html += '<span class="diff-added">';
            for (let k = lastIndex2 + 1; k < part.index2; k++) {
              html += escapeHtml(tokens2[k]);
            }
            html += '</span>';
          }
          
          // 添加共同部分
          html += `<span class="diff-common">${escapeHtml(part.token)}</span>`;
          
          lastIndex1 = part.index1;
          lastIndex2 = part.index2;
        }
        
        // 处理剩余的部分
        if (lastIndex1 < tokens1.length - 1) {
          html += '<span class="diff-removed">';
          for (let k = lastIndex1 + 1; k < tokens1.length; k++) {
            html += escapeHtml(tokens1[k]);
          }
          html += '</span>';
        }
        
        if (lastIndex2 < tokens2.length - 1) {
          html += '<span class="diff-added">';
          for (let k = lastIndex2 + 1; k < tokens2.length; k++) {
            html += escapeHtml(tokens2[k]);
          }
          html += '</span>';
        }
        
        html += '</div>';
        return html;
      } catch (e) {
        console.error('生成差异对比失败:', e);
        return `<div class="diff-error">无法生成差异对比: ${e.message}</div>`;
      }
    }

    // 内联建议开关切换处理
    const onInlineSuggestionsToggle = (value) => {
      if (value) {
        ElMessage.info('已启用内联建议，润色结果将直接显示在编辑器中')
        // 启用并立即应用当前的建议
        setTimeout(() => {
          if (getQuillEditorElement()) {
            // 如果已经进行过AI分析且有建议，则应用它们
            if (aiSuggestions.syntax.length > 0 || aiSuggestions.terminology.length > 0) {
              // 只有当分析内容和当前内容一致时才应用高亮
              if (lastAnalyzedContent.value === contractDetails.content) {
              applyInlineSuggestions()
              ElMessage.success('已将现有建议应用到编辑器中')
              } else {
                ElMessage.warning('内容已更改，请重新点击"AI润色分析"按钮获取最新建议')
              }
            } else {
              ElMessage.info('没有可应用的建议，请点击"AI润色分析"按钮获取建议')
            }
          } else {
            console.warn('无法获取编辑器元素，将使用侧边栏显示建议');
            showAiSuggestions.value = true;
            enableInlineSuggestions.value = false;
          }
        }, 100)
      } else {
        ElMessage.info('已禁用内联建议，建议将只在侧边栏显示')
        // 禁用时清除所有标记
        setTimeout(() => {
          try {
            clearInlineEditSuggestions();
          } catch (error) {
            console.error('清除建议标记失败:', error);
          }
        }, 100);
      }
    }
    
    // 设置键盘快捷键
    const setupKeyboardShortcuts = () => {
      const handleKeyDown = (e) => {
        // 检查是否为 Ctrl+Shift+A (润色分析)
        if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'a') {
          // 确保当前在合同文本标签并且不在加载中状态
          if (activeTab.value === 'contractText' && !realTimePolishLoading.value) {
            e.preventDefault(); // 阻止默认行为
            manualAnalyzeText();
            ElMessage.info('已通过快捷键触发AI润色分析');
          }
        }
        
        // 检查是否为 Ctrl+Shift+C (合同检查)
        if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'c') {
          // 确保当前在合同检查标签并且不在检查中状态
          if (activeTab.value === 'contractCheck' && !isChecking.value) {
            e.preventDefault(); // 阻止默认行为
            startContractCheck();
            ElMessage.info('已通过快捷键触发AI合同检查');
          }
        }
      };
      
      window.addEventListener('keydown', handleKeyDown);
      
      // 清理事件监听器
      return () => {
        window.removeEventListener('keydown', handleKeyDown);
      };
    };

    // 组件挂载时添加按钮和快捷键
    onMounted(async () => {
      // 检查路由状态中是否包含新创建的合同数据
      const newContractData = history.state.newContractData;

      if (newContractData) {
        // 如果有，直接用这份数据填充页面，避免API调用和缓存问题
        console.log('检测到导航状态中的新合同数据，直接填充:', newContractData);
        // 创建一个函数来填充数据，避免代码重复
        const populateDetails = (data) => {
          Object.keys(contractDetails).forEach(key => {
            if (key in data) {
              contractDetails[key] = data[key];
            }
          });
          if (data.sign_date) contractDetails.signDate = data.sign_date;
          if (data.start_date) contractDetails.startDate = data.start_date;
          if (data.expire_date) contractDetails.expireDate = data.expire_date;
          if (data.amount) contractDetails.amount = Number(data.amount).toLocaleString('zh-CN');
        };
        populateDetails(newContractData);
        isLoading.value = false;
        ElMessage.success('AI生成合同加载成功');
      } else if (route.name === 'ContractDetail' && contractId.value) {
        // 否则，走常规的API加载流程
        console.log('组件挂载，开始加载合同详情:', contractId.value);
        await getContractDetails(true);
      } else {
        console.log('组件挂载但不在合同详情页面或合同ID无效，跳过加载');
      }
      
      console.log("组件挂载完成，UI初始化")
      
      // 强制修复滚动样式
      setTimeout(() => {
        if (checkResultArea.value) {
          console.log('强制修复滚动区域样式');
          // 修复右侧内容区域样式 - 使用flex布局
          checkResultArea.value.style.display = 'flex';
          checkResultArea.value.style.flexDirection = 'column';
          checkResultArea.value.style.overflow = 'hidden';
          checkResultArea.value.style.height = '100%';
          
          // 修复滚动容器样式 - 使用flex子元素
          const scrollWrapper = checkResultArea.value.querySelector('.check-content-scroll-wrapper');
          if (scrollWrapper) {
            scrollWrapper.style.flex = '1';
            scrollWrapper.style.overflowY = 'auto';
            scrollWrapper.style.padding = '15px';
            scrollWrapper.style.height = '0'; // 关键：flex布局中设置height:0让flex-grow工作
          }
        }
      }, 300);
      
      // 确保Quill正确加载
      checkAndInitQuill()
      
      // 初始化编辑器高度
      nextTick(() => {
        adjustEditorHeight();
        // 设置窗口大小调整监听器
        setupResizeListener();
        
        // 设置MutationObserver来监控DOM变化
        setupMutationObserver();
      });
      
      // 检查是否直接进入合同文本标签，不再自动分析
      if (activeTab.value === 'contractText') {
        console.log("直接进入文本编辑标签，可以点击润色按钮进行分析")
      }
      
      // 添加展开按钮
      addFloatingButton()
      // 初始状态下更新按钮显示
      updateFloatingButton()
      
      // 设置键盘快捷键
      const cleanupShortcuts = setupKeyboardShortcuts();
      
      // 保存清理函数引用到外部变量
      keyboardShortcutsCleanup.value = cleanupShortcuts;
      
      // 添加页面可见性监听，当用户切回标签页时重新调整高度
      document.addEventListener("visibilitychange", handleVisibilityChange);
      
      // 修改：使用更具优先级的CSS选择器，添加!important标记确保样式生效
      const styleEl = document.createElement('style');
      styleEl.id = 'suggestion-highlight-fix-style';
      styleEl.textContent = `
        /* 单独的通用高亮样式 */
        .suggestion-highlight, 
        [data-suggestion-id],
        body .ql-editor .suggestion-highlight,
        body .ql-editor [data-suggestion-id],
        .ql-container .ql-editor .suggestion-highlight,
        .ql-container .ql-editor [data-suggestion-id] {
          pointer-events: auto !important; /* 确保点击事件可以触发 */
          cursor: pointer !important;
          background-color: rgba(255, 217, 102, 0.3) !important;
          border-bottom: 1px dashed #ffb300 !important;
          z-index: 9999 !important; /* 提高z-index确保在最上层 */
          position: relative !important;
        }
        
        /* 确保tooltip容器也具有足够的z-index */
        .suggestion-tooltip,
        #suggestion-tooltip-container {
          position: fixed !important; /* 改为fixed定位，避免受父级影响 */
          z-index: 10000 !important; /* 比高亮元素更高 */
          pointer-events: auto !important;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2) !important;
        }

        /* 确保Quill编辑器不会阻止点击事件传播 */
        .ql-editor {
          position: relative !important;
        }
      `;
      document.head.appendChild(styleEl);
      
      // 调整编辑器高度
      nextTick(() => {
        adjustEditorHeight();
        setupMutationObserver();
        setupResizeListener();
      });
    });
    
    // 处理页面可见性变化
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        // 页面重新变为可见时，重新调整高度
        console.log("页面重新获得焦点，调整布局高度");
        setTimeout(adjustEditorHeight, 100);
      }
    };
    
    // 组件卸载时清理资源
    onUnmounted(() => {
      const button = document.getElementById('aiFloatingButton')
      if (button) {
        document.body.removeChild(button)
      }
      
      // 重置contractId，确保离开页面时清理
      contractId.value = null

      // 清理suggestion tooltip
      const tooltip = document.querySelector('.ql-suggestion-tooltip')
      if (tooltip) {
        document.body.removeChild(tooltip)
      }
      
      // 移除动态添加的样式
      const styleElem = document.getElementById('suggestion-styles')
      if (styleElem) {
        document.head.removeChild(styleElem)
      }
      
      // 清理MutationObserver
      if (quillEditor.value) {
        try {
          const editor = quillEditor.value.getQuill()
          if (editor) {
            const suggestionModule = editor.getModule('suggestion')
            if (suggestionModule && typeof suggestionModule.destroy === 'function') {
              suggestionModule.destroy()
            }
          }
        } catch (error) {
          console.error('清理建议模块失败:', error)
        }
      }
      
      // 清理键盘快捷键
      if (keyboardShortcutsCleanup.value) {
        keyboardShortcutsCleanup.value();
      }
      
      // 清理窗口大小调整事件监听器
      cleanupResizeListener();
      
      // 清理DOM变化监听器
      if (resizeObserver) {
        resizeObserver.disconnect();
        resizeObserver = null;
      }
      
      // 移除页面可见性监听
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      
      // 移除文档级的点击事件处理器
      document.removeEventListener('click', documentHighlightClickHandler, true);
      
      // 清理样式元素
      const styleEl = document.getElementById('suggestion-highlight-fix-style');
      if (styleEl) {
        document.head.removeChild(styleEl);
      }
    })

    // 用于存储清理函数的引用
    const keyboardShortcutsCleanup = ref(null);
    
    // 创建用来存储MutationObserver的变量
    let resizeObserver = null;
    
    // 设置MutationObserver来监控DOM变化
    const setupMutationObserver = () => {
      // 确保之前的observer已被清理
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      
      // 如果在合同文本标签页，设置observer
      if (activeTab.value === 'contractText' && contractEditContainer.value) {
        resizeObserver = new MutationObserver(() => {
          // 当DOM变化时，调整编辑器高度
          adjustEditorHeight();
        });
        
        // 配置observer监控子节点变化和属性变化
        resizeObserver.observe(contractEditContainer.value, {
          childList: true,
          subtree: true,
          attributes: true
        });
        
        console.log('已设置DOM变化监听器');
      }
    };
    
    // 检查并初始化Quill
    const checkAndInitQuill = () => {
      // 先检查是否已经直接可用
      if (typeof window !== 'undefined' && window.Quill) {
        try {
          console.log('Quill已加载，初始化扩展')
          initQuillExtensions()
          
          // 在初始化后添加安全性检查
          setTimeout(() => {
            const editorElement = getQuillEditorElement();
            if (!editorElement) {
              console.warn('Quill编辑器DOM元素无法访问，可能导致某些功能不可用');
              enableInlineSuggestions.value = false;
            }
          }, 300);
        } catch (error) {
          console.error('初始化Quill扩展失败:', error)
          enableInlineSuggestions.value = false
        }
        return
      }
      
      // 如果不可用，尝试多种途径加载Quill
      console.log('Quill未加载，尝试加载资源')
      
      // 定义多个可能的CDN资源路径
      const cdnSources = [
        {
          js: `${window.location.origin}/static/lib/quill/quill.min.js`,
          css: `${window.location.origin}/static/lib/quill/quill.snow.css`
        },
        {
          js: 'https://cdn.jsdelivr.net/npm/quill@1.3.7/dist/quill.min.js',
          css: 'https://cdn.jsdelivr.net/npm/quill@1.3.7/dist/quill.snow.css'
        },
        {
          js: 'https://cdnjs.cloudflare.com/ajax/libs/quill/1.3.7/quill.min.js',
          css: 'https://cdnjs.cloudflare.com/ajax/libs/quill/1.3.7/quill.snow.css'
        },
        {
          js: 'https://unpkg.com/quill@1.3.7/dist/quill.min.js',
          css: 'https://unpkg.com/quill@1.3.7/dist/quill.snow.css'
        }
      ];
      
      // 跟踪加载尝试
      let currentSourceIndex = 0;
      const maxRetries = cdnSources.length;
      
      // 加载CSS资源
      const loadCss = (source) => {
        return new Promise((resolve, reject) => {
          // 检查是否已经加载过
          const existingLink = document.getElementById('quill-snow-css');
          if (existingLink) {
            document.head.removeChild(existingLink);
          }
          
          const cssLink = document.createElement('link');
          cssLink.rel = 'stylesheet';
          cssLink.id = 'quill-snow-css';
          cssLink.href = source;
          
          cssLink.onload = () => {
            console.log('Quill CSS 加载成功:', source);
            resolve();
          };
          
          cssLink.onerror = () => {
            console.error('Quill CSS 加载失败:', source);
            reject();
          };
          
          document.head.appendChild(cssLink);
        });
      };
      
      // 加载JS资源
      const loadJs = (source) => {
        return new Promise((resolve, reject) => {
          // 检查是否已经加载过
          const existingScript = document.getElementById('quill-js');
          if (existingScript) {
            document.body.removeChild(existingScript);
          }
          
          const script = document.createElement('script');
          script.src = source;
          script.id = 'quill-js';
          script.async = true;
          
          script.onload = () => {
            console.log('Quill JS 加载成功:', source);
            resolve();
          };
          
          script.onerror = () => {
            console.error('Quill JS 加载失败:', source);
            reject();
          };
          
          document.body.appendChild(script);
        });
      };
      
      // 尝试加载下一个源
      const tryNextSource = () => {
        if (currentSourceIndex >= maxRetries) {
          console.error('所有Quill资源加载尝试都失败了');
          fallbackToBasicEditor();
          return;
        }
        
        const source = cdnSources[currentSourceIndex];
        currentSourceIndex++;
        
        console.log(`尝试加载Quill资源 (${currentSourceIndex}/${maxRetries}):`, source);
        
        // 先尝试加载CSS，然后加载JS
        loadCss(source.css)
          .then(() => loadJs(source.js))
          .then(() => {
            // 加载成功后初始化
            console.log('Quill资源加载完成，初始化扩展');
            setTimeout(() => {
              try {
                if (window.Quill) {
                  initQuillExtensions();
                  
                  // 如果在合同文本标签页，尝试应用内联建议
                  if (activeTab.value === 'contractText' && enableInlineSuggestions.value) {
                    setTimeout(applyInlineSuggestions, 500);
                  }
                } else {
                  console.error('Quill未能正确加载，脚本可能已执行但Quill对象未定义');
                  tryNextSource();
                }
              } catch (error) {
                console.error('初始化Quill扩展失败:', error);
                tryNextSource();
              }
            }, 300);
          })
          .catch(() => {
            console.log('资源加载失败，尝试下一个源');
            tryNextSource();
          });
      };
      
      // 降级到基本编辑器
      const fallbackToBasicEditor = () => {
        ElMessage.warning('高级编辑器加载失败，使用基本编辑器功能');
        enableInlineSuggestions.value = false;
        showAiSuggestions.value = true;
        
        // 添加基本样式
        const inlineStyles = document.createElement('style');
        inlineStyles.id = 'quill-basic-styles';
        inlineStyles.textContent = `
          .ql-container{border:1px solid #ccc;font-family:sans-serif;}
          .ql-editor{min-height:300px;padding:12px 15px;}
          .ql-toolbar{border-top:none;border-left:none;border-right:none;border-bottom:1px solid #e0e0e0;background-color:#f8f9fa;}
        `;
        document.head.appendChild(inlineStyles);
      };
      
      // 开始尝试加载
      tryNextSource();
    }

    // 在mounted钩子中读取本地存储的术语
    onMounted(() => {
      // 加载合同详情
      getContractDetails();
      
      // 加载本地存储的自定义术语
      const savedTerminologies = localStorage.getItem('customTerminologies');
      if (savedTerminologies) {
        try {
          customTerminologies.value = JSON.parse(savedTerminologies);
        } catch (e) {
          console.error('解析存储的术语出错:', e);
        }
      }
      
      // 读取本地存储的润色偏好
      const savedPreferences = localStorage.getItem('polishPreferences');
      if (savedPreferences) {
        try {
          const preferences = JSON.parse(savedPreferences);
          // 确保focus是数组类型
          if (preferences.focus && !Array.isArray(preferences.focus)) {
            preferences.focus = ['grammar', 'terminology'];
          }
          Object.assign(polishPreferences, preferences);
          console.log('已加载润色偏好设置:', polishPreferences);
        } catch (e) {
          console.error('解析存储的润色偏好出错:', e);
        }
      }
      
      // 读取本地存储的检查偏好
      const savedCheckPreferences = localStorage.getItem('checkPreferences');
      if (savedCheckPreferences) {
        try {
          const preferences = JSON.parse(savedCheckPreferences);
          Object.assign(checkPreferences, preferences);
          console.log('已加载检查偏好设置:', checkPreferences);
        } catch (e) {
          console.error('解析存储的检查偏好出错:', e);
        }
      }
      
      // 绑定编辑器高亮点击事件
      const editorContainer = getQuillEditorElement();
      if (editorContainer) {
        editorContainer.addEventListener('click', delegatedHighlightClick, true);
        
        // 添加全局点击监听作为备份
        setTimeout(() => {
          document.addEventListener('click', function globalHighlightClickHandler(e) {
            // 检查是否点击了高亮元素
            let target = e.target;
            if ((target.classList && target.classList.contains('suggestion-highlight')) ||
                (target.hasAttribute && target.hasAttribute('data-suggestion-id'))) {
              console.log('全局点击监听捕获到高亮元素点击');
              
              // 获取建议ID
              const suggestionId = target.getAttribute('data-suggestion-id');
              if (!suggestionId) return;
              
              // 处理高亮元素点击
              handleHighlightElement(target, e);
            }
          }, true);
        }, 500);
      }
      
      // 调整编辑器高度
      nextTick(() => {
        adjustEditorHeight();
        setupMutationObserver();
        setupResizeListener();
      });
    });

    // 监听润色偏好变化，保存到本地存储
    watch(polishPreferences, (newPreferences) => {
      console.log('保存润色偏好:', newPreferences);
      localStorage.setItem('polishPreferences', JSON.stringify({
        style: newPreferences.style, 
        contractType: newPreferences.contractType,
        focus: newPreferences.focus
      }));
    }, { deep: true });

    // 监听合同内容变化，延迟执行分析
    watch(() => contractDetails.content, (newContent, oldContent) => {
      if (newContent && newContent !== oldContent && newContent !== lastAnalyzedContent.value) {
        // 当内容变化时，清除所有内联建议高亮
        clearInlineEditSuggestions();
        debouncedAnalyzeText();
      }
    });

    // 监听检查偏好设置变化，保存到本地
    watch(checkPreferences, (newPreferences) => {
      console.log('保存检查偏好:', newPreferences);
      localStorage.setItem('checkPreferences', JSON.stringify(newPreferences));
    }, { deep: true });

    // 在组件卸载前清理所有事件监听
    onBeforeUnmount(() => {
      // 清理窗口调整大小事件
      cleanupResizeListener();
      
      // 清理页面可见性变化监听
      document.removeEventListener('visibilitychange', () => {});
      
      // 清理DOM变化观察器
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      
      // 清理全局样式
      const styleEl = document.getElementById('suggestion-highlight-fix-style');
      if (styleEl) {
        document.head.removeChild(styleEl);
      }
      
      console.log('组件即将卸载，已清理所有事件监听器');
    });

    const aiCheckFinished = ref(false)

    // 自动滚动到底部
    function scrollQuillToBottom() {
      if (quillEditor.value && quillEditor.value.getQuill) {
        const quill = quillEditor.value.getQuill();
        if (quill && quill.root) {
          quill.root.scrollTop = quill.root.scrollHeight;
        }
      }
    }

    // 合同文本内容变更时自动滚动到底部
    function onContractContentChange() {
      // 移除自动滚动到底部的逻辑
      // scrollQuillToBottom();
    }

    // 1. 在onMounted中为编辑器容器绑定事件委托
    onMounted(() => {
      const editorContainer = getQuillEditorElement();
      if (editorContainer) {
        editorContainer.addEventListener('click', delegatedHighlightClick, true);
      }
    });

    onBeforeUnmount(() => {
      const editorContainer = getQuillEditorElement();
      if (editorContainer) {
        editorContainer.removeEventListener('click', delegatedHighlightClick, true);
      }
    });

    // 2. 实现事件委托处理函数
    function delegatedHighlightClick(e) {
      try {
        console.log('捕获到编辑器点击事件', e.target);
        let el = e.target;
        
        // 使用函数检测是否为高亮元素，增强可靠性
        const isHighlightElement = (element) => {
          if (!element) return false;
          
          // 多种检查方式
          return (element.classList && element.classList.contains('suggestion-highlight')) ||
                 (element.hasAttribute && element.hasAttribute('data-suggestion-id')) || 
                 (element.getAttribute && element.getAttribute('data-suggestion-id'));
        };
        
        // 检查当前元素
        if (isHighlightElement(el)) {
          console.log('直接匹配到高亮元素');
          e.preventDefault();
          e.stopPropagation();
          handleHighlightElement(el, e);
          return;
        }
        
        // 向上查找高亮元素
        while (el && el !== document.body) {
          if (isHighlightElement(el)) {
            console.log('在父级找到高亮元素');
            e.preventDefault();
            e.stopPropagation();
            handleHighlightElement(el, e);
            return;
          }
          el = el.parentElement;
        }
        
        // 查找可能的子元素
        const highlightElements = e.target.querySelectorAll && e.target.querySelectorAll('.suggestion-highlight, [data-suggestion-id]');
        if (highlightElements && highlightElements.length > 0) {
          console.log('在子元素中找到高亮元素');
          e.preventDefault();
          e.stopPropagation();
          handleHighlightElement(highlightElements[0], e);
          return;
        }
      } catch (error) {
        console.error('高亮点击处理出错:', error);
      }
    }

    // 处理高亮元素的函数，提取逻辑便于复用
    function handleHighlightElement(el, e) {
      // 阻止默认行为和事件冒泡
      e.preventDefault();
      e.stopPropagation();
      
      // 获取suggestion信息
      const suggestionId = el.getAttribute('data-suggestion-id');
      if (!suggestionId) {
        console.error('未找到suggestion-id属性');
        return;
      }
      
      console.log('处理高亮元素点击:', suggestionId);
      
      // 优先从DOM属性中获取完整信息，确保与高亮的内容一致
      const original = el.getAttribute('data-original');
      const suggested = el.getAttribute('data-suggested');
      const explanation = el.getAttribute('data-explanation') || '';
      
      if (original && suggested) {
        // 使用DOM中的属性创建建议对象
        const suggestionFromDOM = {
          id: suggestionId,
          original: original,
          suggested: suggested,
          explanation: explanation
        };
        
        // 创建或获取tooltip容器
        let tooltipContainer = document.getElementById('suggestion-tooltip-container');
        if (!tooltipContainer) {
          tooltipContainer = document.createElement('div');
          tooltipContainer.id = 'suggestion-tooltip-container';
          tooltipContainer.className = 'suggestion-tooltip';
          tooltipContainer.style.display = 'none';
          document.body.appendChild(tooltipContainer);
        }
        
        // 直接使用DOM属性中的建议显示tooltip
        showSuggestionTooltip(el, suggestionFromDOM, tooltipContainer);
        console.log('从DOM属性显示建议:', suggestionFromDOM);
        return;
      }
      
      // 如果DOM属性不完整，再尝试从建议列表中查找
      let fullSuggestion = null;
      
      // 在语法建议中查找
      for (let i = 0; i < aiSuggestions.syntax.length; i++) {
        if (aiSuggestions.syntax[i].id === suggestionId) {
          fullSuggestion = aiSuggestions.syntax[i];
          break;
        }
      }
      
      // 在术语建议中查找
      if (!fullSuggestion) {
        for (let i = 0; i < aiSuggestions.terminology.length; i++) {
          if (aiSuggestions.terminology[i].id === suggestionId) {
            fullSuggestion = aiSuggestions.terminology[i];
            break;
          }
        }
      }
      
      if (!fullSuggestion) {
        console.error('无法找到对应的建议内容:', suggestionId);
        ElMessage.warning('无法找到对应的建议内容');
        return;
      }
      
      // 获取tooltip容器
      let tooltipContainer = document.getElementById('suggestion-tooltip-container');
      if (!tooltipContainer) {
        tooltipContainer = document.createElement('div');
        tooltipContainer.id = 'suggestion-tooltip-container';
        tooltipContainer.className = 'suggestion-tooltip';
        tooltipContainer.style.display = 'none';
        document.body.appendChild(tooltipContainer);
      }
      
      // 显示tooltip
      showSuggestionTooltip(el, fullSuggestion, tooltipContainer);
    }

    // 监听标签页切换，清除高亮
    watch(activeTab, (newTab) => {
      // 如果切换到了合同文本标签
      if (newTab === 'contractText') {
        // 确保只在有AI建议的情况下才应用高亮
        if (enableInlineSuggestions.value) {
          // 先清除可能存在的旧高亮
          clearInlineEditSuggestions();
          
          // 只在已经进行过AI分析且有建议的情况下应用高亮
          if (lastAnalyzedContent.value === contractDetails.content && 
              (aiSuggestions.syntax.length > 0 || aiSuggestions.terminology.length > 0)) {
            setTimeout(() => {
              applyInlineSuggestions();
            }, 300);
          }
        }
      } else {
        // 切换到其他标签页时，清除高亮
        clearInlineEditSuggestions();
      }
    });

    // 在onMounted的最后添加全局点击监听
    onMounted(() => {
      // 已有的代码保持不变
      // ...
      
      // 添加全局点击监听作为备份
      document.addEventListener('click', function(e) {
        // 检查是否点击了高亮元素
        let target = e.target;
        if (target.classList && target.classList.contains('suggestion-highlight') ||
            target.hasAttribute && target.hasAttribute('data-suggestion-id')) {
          console.log('全局点击监听捕获到高亮元素点击');
          
          // 获取建议ID
          const suggestionId = target.getAttribute('data-suggestion-id');
          if (!suggestionId) return;
          
          // 查找建议
          let suggestion = null;
          for (const s of aiSuggestions.syntax) {
            if (s.id === suggestionId) {
              suggestion = s;
              break;
            }
          }
          
          if (!suggestion) {
            for (const s of aiSuggestions.terminology) {
              if (s.id === suggestionId) {
                suggestion = s;
                break;
              }
            }
          }
          
          if (suggestion) {
            // 处理高亮元素点击事件
            handleHighlightElement(target, e);
          }
        }
      });
    });

    // 添加文档级别的事件处理函数
    function documentHighlightClickHandler(e) {
      // 检查点击的是否是高亮元素或其子元素
      let target = e.target;
      const isHighlight = (element) => {
        return (element.classList && element.classList.contains('suggestion-highlight')) || 
               (element.hasAttribute && element.hasAttribute('data-suggestion-id'));
      };
      
      if (isHighlight(target)) {
        console.log('文档级事件捕获到高亮点击');
        e.preventDefault();
        e.stopPropagation();
        handleHighlightElement(target, e);
        return;
      }
      
      // 向上查找父元素
      while (target && target !== document.body) {
        if (isHighlight(target)) {
          console.log('文档级事件捕获到高亮父元素点击');
          e.preventDefault();
          e.stopPropagation();
          handleHighlightElement(target, e);
          return;
        }
        target = target.parentElement;
      }
    }

    // 监听查询参数_refresh变化，强制刷新数据
    watch(() => route.query._refresh, (newVal) => {
      if (newVal && route.name === 'ContractDetail') {
        console.log('检测到刷新参数变化，强制刷新合同详情:', newVal)
        getContractDetails(false)
      }
    })

    return {
      activeTab,
      activeCollapse,
      activeSuggestionCollapse,
      contractId,
      contractDetails,
      contractTitle,
      checkResult,
      aiSuggestions,
      contractHistory,
      polishPreferences,
      checkPreferences,
      customTerminologies,
      newTerminology,
      addCustomTerminology,
      removeCustomTerminology,
      isChecking,
      quillEditor,
      editorOption,
      showAiSuggestions,
      goBack,
      saveChanges,
      isLoading,
      isSaving,
      isRealTimePolishing,
      realTimePolishLoading,
      toggleAiPanelCollapse,
      isAiPanelCollapsed,
      adoptInlineEditSuggestion,
      ignoreInlineEditSuggestion,
      applyInlineSuggestions,
      enableInlineSuggestions,
      onInlineSuggestionsToggle,
      debouncedAnalyzeText,
      clearInlineEditSuggestions,
      showSuggestionTooltip,
      generateDiff,
      manualAnalyzeText,
      estimatedTime,
      startContractCheck, // 添加合同检查函数
      viewRegulation, 
      downloadContract, 
      adoptSuggestion, 
      ignoreSuggestion, 
      applyAllSuggestions, 
      hideAiPanel, 
      // 添加引用变量
      contractEditContainer,
      aiPolishSidebar,
      editorMainArea,
      contractCheckContainer, // 合同检查容器引用
      checkSidebar, // 检查侧边栏引用
      checkResultArea, // 检查结果区域引用
      scrollQuillToBottom,
      onContractContentChange
    }
  }
}
</script>

<style scoped>
.contract-detail-container {
  padding: 20px;
  position: relative;
  /* overflow-x: hidden; 移除，允许主页面滚动 */
}

.card {
  border: none;
  border-radius: 10px;
  box-shadow: 0 0 10px rgba(0,0,0,0.05);
  margin-bottom: 20px;
}

.card-header {
  background-color: #fff;
  border-bottom: 1px solid #f0f0f0;
  padding: 15px 20px;
  font-weight: 600;
  font-size: 16px;
  color: #343a40;
}

.card-body {
  padding: 20px;
  overflow: visible; /* 确保不剪裁badge */
}

.contract-text-editor {
  min-height: 100%;
  height: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 0;
  margin-bottom: 0;
  background-color: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.contract-text-editor .ql-toolbar {
  border-top: none;
  border-left: none;
  border-right: none;
  border-bottom: 1px solid #e0e0e0;
  background-color: #f8f9fa;
  padding: 8px 15px;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  flex-shrink: 0;
}

.contract-text-editor .ql-container {
  border: none;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Microsoft YaHei', Arial, sans-serif;
}

.contract-text-editor .ql-editor {
  height: 100%;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.8;
  padding: 15px 20px;
  color: #333;
  scrollbar-width: thin; /* Firefox滚动条样式 */
  scrollbar-color: #ddd transparent; /* Firefox滚动条颜色 */
  scroll-behavior: smooth; /* 平滑滚动 */
}

/* 增加编辑器的滚动条样式 */
.contract-text-editor .ql-editor::-webkit-scrollbar {
  width: 6px;
  background-color: transparent;
}

.contract-text-editor .ql-editor::-webkit-scrollbar-thumb {
  background-color: #ddd;
  border-radius: 3px;
  transition: background-color 0.2s;
}

.contract-text-editor .ql-editor::-webkit-scrollbar-thumb:hover {
  background-color: #bbb;
}

.check-item {
  margin-bottom: 15px;
}

.me-1 {
  margin-right: 4px;
}

.me-2 {
  margin-right: 8px;
}

.ms-2 {
  margin-left: 8px;
}

.mt-3 {
  margin-top: 16px;
}

.mb-0 {
  margin-bottom: 0;
}

.mb-1 {
  margin-bottom: 4px;
}

.mb-2 {
  margin-bottom: 8px;
}

.mb-3 {
  margin-bottom: 16px;
}

.fs-4 {
  font-size: 1.5rem;
}

/* AI建议面板样式 */
.ai-suggestions-panel {
  position: fixed;
  top: 70px;  /* 调整顶部距离 */
  right: 20px; /* 调整右侧距离，避免紧贴边缘 */
  bottom: 20px;
  width: 350px; /* 稍微增加宽度 */
  max-height: calc(100vh - 100px); /* 限制最大高度 */
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px; /* 四边都有圆角 */
  padding: 15px;
  overflow-y: auto;
  transition: transform 0.3s ease-in-out, opacity 0.3s ease-in-out;
  opacity: 0;
  transform: translateX(100%);
  z-index: 1040;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.1); /* 更柔和的阴影 */
}

.ai-suggestions-panel.show {
  opacity: 1;
  transform: translateX(0);
}

.ai-suggestions-panel.collapsed {
  transform: translateX(calc(100% - 35px));
  border-top-left-radius: 20px;
  border-bottom-left-radius: 20px;
}

.ai-suggestions-panel.collapsed .panel-header h5,
.ai-suggestions-panel.collapsed .suggestion-item,
.ai-suggestions-panel.collapsed > div:not(.panel-header) {
  display: none;
}

.ai-suggestions-panel.collapsed .panel-header {
  writing-mode: vertical-lr;
  transform: rotate(180deg);
  position: absolute;
  top: 0;
  bottom: 0;
  left: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-suggestions-panel.collapsed .panel-controls {
  transform: rotate(180deg);
  position: absolute;
  top: 10px;
  left: 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.panel-controls {
  display: flex;
  align-items: center;
}

.suggestion-item {
  background-color: #fff;
  border: 1px solid #e9ecef;
  border-radius: 5px;
  padding: 10px;
  margin-bottom: 10px;
  font-size: 0.85rem;
}

.original-text {
  text-decoration: line-through;
  color: #dc3545;
  font-size: 0.8rem;
  display: block;
  margin-bottom: 3px;
}

.suggested-text {
  color: #28a745;
  font-weight: bold;
  display: block;
  margin-bottom: 5px;
}

.explanation {
  font-size: 0.75rem;
  color: #6c757d;
  margin-bottom: 8px;
}

.text-danger {
  color: #dc3545;
}

.text-warning {
  color: #ffc107;
}

.text-info {
  color: #17a2b8;
}

.text-success {
  color: #28a745;
}

.text-primary {
  color: #007bff;
}

.text-muted {
  color: #6c757d;
}

.text-center {
  text-align: center;
}

.text-end {
  text-align: right;
}

.d-flex {
  display: flex;
}

.flex-shrink-0 {
  flex-shrink: 0;
}

.flex-grow-1 {
  flex-grow: 1;
}

.justify-content-between {
  justify-content: space-between;
}

.align-items-center {
  align-items: center;
}

.p-3 {
  padding: 1rem;
}

.ms-3 {
  margin-left: 1rem;
}

.gap-2 {
  gap: 0.5rem;
}

.border {
  border: 1px solid #dee2e6;
}

.rounded {
  border-radius: 0.25rem;
}

.bg-light {
  background-color: #f8f9fa;
}

.row {
  display: flex;
  flex-wrap: wrap;
  margin-right: -15px;
  margin-left: -15px;
}

.col-md-3 {
  flex: 0 0 25%;
  max-width: 25%;
  padding-left: 15px;
  padding-right: 15px;
}

.col-md-6 {
  flex: 0 0 50%;
  max-width: 50%;
  padding-left: 15px;
  padding-right: 15px;
}

@media (max-width: 767.98px) {
  .col-md-3, .col-md-6 {
    flex: 0 0 100%;
    max-width: 100%;
  }
}

/* 永久可见的展开按钮样式 */
.panel-open-button {
  position: fixed;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  z-index: 1039;
  padding: 8px 5px 8px 8px;
  background-color: rgba(255, 255, 255, 0.95);
  border-top-left-radius: 50%;
  border-bottom-left-radius: 50%;
  box-shadow: -2px 0 5px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
}

.panel-open-button:hover {
  right: 8px;
  background-color: #f0f9ff;
}

.panel-open-button .el-button {
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.2);
}

/* 添加内联建议相关的样式 */
.suggestion-highlight {
  background-color: rgba(255, 217, 102, 0.3);
  border-bottom: 1px dashed #ffb300;
  cursor: pointer;
  position: relative;
}

.suggestion-highlight:hover {
  background-color: rgba(255, 217, 102, 0.5);
}

.ql-suggestion-tooltip {
  position: absolute;
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1100;
  width: auto;
  max-width: 300px;
}

.suggestion-tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.suggestion-original {
  text-decoration: line-through;
  color: #dc3545;
  font-size: 0.9rem;
}

.suggestion-suggested {
  color: #28a745;
  font-weight: bold;
  font-size: 0.9rem;
}

.suggestion-arrow {
  color: #6c757d;
  margin: 0 5px;
}

.suggestion-actions {
  display: flex;
  justify-content: flex-end;
  gap: 5px;
  margin-top: 5px;
}

.suggestion-actions button {
  border: none;
  border-radius: 3px;
  padding: 3px 8px;
  font-size: 0.8rem;
  cursor: pointer;
}

.suggestion-actions .btn-adopt {
  background-color: #28a745;
  color: white;
}

.suggestion-actions .btn-ignore {
  background-color: #6c757d;
  color: white;
}

/* 添加增强的差异对比样式 */
.diff-content {
  margin: 8px 0;
  padding: 5px;
  background: #f8f9fa;
  border-radius: 4px;
  line-height: 1.5;
  font-family: Consolas, Monaco, monospace;
  word-break: break-word;
}

.diff-common {
  color: #333;
}

.diff-removed {
  background-color: #ffecec;
  color: #b30000;
  text-decoration: line-through;
  padding: 0 2px;
  border-radius: 2px;
}

.diff-added {
  background-color: #eaffea;
  color: #006700;
  font-weight: bold;
  padding: 0 2px;
  border-radius: 2px;
}

.suggestion-diff-container {
  margin-top: 10px;
  border-top: 1px solid #eee;
  padding-top: 8px;
}

.suggestion-tooltip-content {
  min-width: 280px;
  max-width: 450px;
}

.suggestion-tooltip-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
  margin-bottom: 8px;
}

.suggestion-tooltip-title {
  font-weight: bold;
  color: #333;
}

.suggestion-tooltip-close {
  cursor: pointer;
  color: #999;
  font-size: 16px;
}

.suggestion-comparison {
  display: flex;
  margin-bottom: 8px;
}

.suggestion-column {
  flex: 1;
  padding: 0 5px;
}

.suggestion-divider {
  width: 1px;
  background-color: #eee;
  margin: 0 8px;
}

.suggestion-label {
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 3px;
  font-weight: bold;
}

.suggestion-explanation-container {
  margin-top: 8px;
  border-top: 1px solid #eee;
  padding-top: 8px;
}

.suggestion-explanation {
  font-style: italic;
  color: #666;
  font-size: 0.9rem;
}

/* 重新设计的AI润色按钮和侧边栏 */
.ai-polish-sidebar {
  width: 250px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef2f8 100%);
  border-radius: 10px;
  padding: 20px 15px;
  position: relative;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e6ebf5;
  height: 100%;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(100, 180, 255, 0.3) transparent;
  scroll-behavior: smooth;
  overflow-x: hidden;
}

.ai-polish-button {
  width: 100%;
  padding: 12px 15px;
  font-size: 16px;
  font-weight: bold;
  transition: all 0.3s ease;
  background: linear-gradient(45deg, #409EFF, #64b5f6);
  box-shadow: 0 4px 10px rgba(64, 158, 255, 0.3);
  margin: 5px 0 15px;
  border-radius: 8px;
  border: none;
}

.ai-polish-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
  background: linear-gradient(45deg, #3a8ee6, #5aadf6);
}

.ai-polish-button:active {
  transform: translateY(1px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}

.ai-polish-button-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-polish-icon {
  font-size: 20px;
  margin-right: 8px;
  animation: glow 2s infinite alternate;
}

@keyframes glow {
  0% {
    opacity: 0.8;
    filter: drop-shadow(0 0 2px rgba(255, 255, 255, 0.6));
  }
  100% {
    opacity: 1;
    filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.9));
  }
}

.ai-polish-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin: 5px 0 15px;
  width: 100%;
}

.time-estimate, .shortcut-hint {
  display: flex;
  align-items: center;
  color: #606266;
  font-size: 13px;
  background-color: rgba(255, 255, 255, 0.7);
  padding: 6px 12px;
  border-radius: 6px;
  width: 100%;
  justify-content: flex-start;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.time-estimate .el-icon, .shortcut-hint .el-icon {
  color: #409EFF;
  margin-right: 8px;
  font-size: 16px;
}

.ai-polish-features {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  margin-top: 10px;
  width: 100%;
  padding: 12px 15px;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.feature-item {
  display: flex;
  align-items: center;
  color: #303133;
  font-size: 14px;
  width: 100%;
  padding: 5px 0;
}

.feature-item .el-icon {
  color: #67c23a;
  margin-right: 10px;
  font-size: 18px;
  background-color: rgba(103, 194, 58, 0.1);
  padding: 4px;
  border-radius: 50%;
}

/* 合同文本编辑区的左右布局 */
.contract-edit-container {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  margin-top: 5px;
  /* height: calc(100vh - 220px); 允许内容撑开页面 */
  min-height: 600px;
  transition: height 0.3s ease;
  overflow: visible;
}

.editor-main-area {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: height 0.3s ease;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
}

/* 编辑器获得焦点时的美化效果 */
.contract-text-editor:focus-within {
  box-shadow: 0 2px 15px rgba(64, 158, 255, 0.15);
  border-color: rgba(64, 158, 255, 0.5);
}

/* 更美观的滚动条 */
.ai-polish-sidebar::-webkit-scrollbar {
  width: 6px;
  background-color: transparent;
}

.ai-polish-sidebar::-webkit-scrollbar-thumb {
  background-color: rgba(100, 180, 255, 0.3);
  border-radius: 3px;
  transition: background-color 0.2s;
}

.ai-polish-sidebar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(100, 180, 255, 0.5);
}

/* 删除无用的badge相关样式 */
.contract-edit-wrapper {
  position: relative;
  margin-bottom: 20px;
}

/* 合同检查结果区域样式 */
.check-sidebar {
  background: linear-gradient(135deg, #f6f8fa 0%, #eef5ff 100%);
}

.check-result-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  padding: 20px; /* 增加内边距 */
  margin-bottom: 20px; /* 增加下边距 */
  flex-shrink: 0; /* 不收缩 */
}

.check-result-area {
  flex: 1;
  position: relative;
  height: 100%;
  /* 移除overflow设置，全部交给el-scrollbar处理 */
}

/* 调整内部滚动容器 */
.check-content-scroll-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 15px 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  height: 0; /* 关键：flex布局中设置height:0让flex-grow工作 */
  scrollbar-width: thin;
  scrollbar-color: #ddd transparent;
}

.check-content-scroll-wrapper::-webkit-scrollbar {
  width: 6px;
  background-color: transparent;
}

.check-content-scroll-wrapper::-webkit-scrollbar-thumb {
  background-color: #ddd;
  border-radius: 3px;
  transition: background-color 0.2s;
}

.check-content-scroll-wrapper::-webkit-scrollbar-thumb:hover {
  background-color: #bbb;
}

.check-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  border-bottom: 1px solid #f0f0f5;
  padding-bottom: 12px; /* 增加边距 */
}

.check-result-header h6 {
  font-size: 17px; /* 增大字体 */
  font-weight: 600;
  color: #303133;
}

.check-result-stats {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
}

.stat-item {
  flex: 1;
  min-width: 100px;
  text-align: center;
  padding: 10px;
  border-radius: 6px;
  background-color: #f9f9fa;
  margin: 0 5px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 5px;
  color: #409EFF;
}

.stat-value.danger {
  color: #F56C6C;
}

.stat-value.warning {
  color: #E6A23C;
}

.stat-value.info {
  color: #909399;
}

.stat-label {
  font-size: 13px;
  color: #606266;
}

.check-result-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.check-collapse {
  border: none;
}

.collapse-header {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  
  .el-icon {
    margin-right: 8px;
  }
}

.check-issue-card {
  background-color: #fafafa;
  border-radius: 8px; /* 增加圆角 */
  padding: 18px; /* 增加内边距 */
  margin-bottom: 20px; /* 增加下边距 */
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05); /* 增强阴影 */
  
  &:last-child {
    margin-bottom: 0;
  }
}

.issue-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px; /* 增加边距 */
  
  .el-icon {
    margin-right: 12px; /* 增加边距 */
    font-size: 20px; /* 增大图标 */
  }
  
  h6 {
    margin: 0;
    font-size: 16px; /* 增大字体 */
    font-weight: 600;
  }
}

.issue-content {
  margin-bottom: 15px;
}

.issue-field {
  margin-bottom: 8px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.field-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  margin-bottom: 4px;
}

.field-value {
  font-size: 14px;
  line-height: 1.5;
  color: #333;
  background-color: white;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #eee;
}

.issue-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.empty-result {
  padding: 30px 0;
  color: #909399;
  text-align: center;
}

.check-options {
  .el-checkbox {
    margin-right: 0;
    margin-left: 0;
    display: block;
    margin-bottom: 8px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

/* 适配键盘快捷键处理器 */
.check-keyboard-shortcut {
  display: none;
}

/* 优化检查偏好设置控件样式 */
.check-sidebar {
  .preference-option {
    margin-bottom: 12px;
    
    .el-select {
      width: 100%;  /* 将下拉框宽度设为100% */
      margin-top: 6px;  /* 增加上边距 */
    }
    
    span {
      display: block;  /* 标签单独一行 */
      margin-bottom: 4px;
      font-weight: 500;
    }
  }
  
  .check-options {
    padding: 5px 0;
    
    .el-checkbox {
      height: 32px;
      display: flex;
      align-items: center;
      border-radius: 4px;
      transition: background-color 0.2s;
      padding: 0 8px;
      margin-bottom: 6px;  /* 减小复选框之间的间距 */
      
      &:hover {
        background-color: rgba(64, 158, 255, 0.08);
      }
      
      &:last-child {
        margin-bottom: 0;  /* 最后一个没有底部边距 */
      }
    }
  }
  
  .ai-polish-button {
    margin-bottom: 20px; /* 增加按钮下边距 */
  }

  /* 检查页面特定样式优化 */
  .ai-polish-personalization {
    background-color: #f7f9ff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    width: 100%;
    padding: 15px;
    margin: 12px 0;
    
    .personalization-title {
      font-size: 14px;
      margin-bottom: 12px;
      padding-bottom: 6px;  /* 减小标题下方空间 */
      
      &:after {
        width: 30px;  /* 减小下划线长度 */
        height: 2px;
      }
    }
    
    .personalization-section {
      margin-bottom: 14px;
      background-color: rgba(255, 255, 255, 0.6);
      border-radius: 6px;
      padding: 10px;
      
      &:last-child {
        margin-bottom: 0;  /* 最后一个区段没有底部边距 */
      }
      
      .section-header {
        margin-bottom: 8px;
        .el-icon {
          font-size: 15px;
        }
        
        span {
          font-size: 13px;  /* 稍微小一点的字体 */
        }
      }
    }
  }
  
  /* 特性列表优化 */
  .ai-polish-features {
    margin-top: 12px;
    
    .feature-item {
      padding: 4px 0;  /* 减小特性项目之间的空间 */
      
      &:last-child {
        padding-bottom: 0;
      }
    }
  }
  
  /* 整体宽度控制 */
  width: 240px;  /* 控制左侧栏宽度，使其更紧凑 */
}

/* 添加自定义scrollbar样式 */
.contract-check-scrollbar {
  height: 100% !important;
}

.contract-check-scrollbar .el-scrollbar__wrap {
  overflow-x: hidden;
}

.suggestion-tooltip {
  position: fixed !important;
  right: 18px !important;
  bottom: 18px !important;
  left: auto !important;
  top: auto !important;
  z-index: 2001 !important;
  width: 260px !important;
  max-width: 280px !important;
  min-width: 180px !important;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,.13);
  padding: 10px 12px 8px 12px;
  font-size: 12px;
  transition: box-shadow 0.2s;
  pointer-events: auto;
}
.suggestion-tooltip-content {
  min-width: 140px;
  max-width: 260px;
  font-size: 12px;
  line-height: 1.5;
  padding: 0;
}
.suggestion-tooltip-header {
  font-size: 13px;
  padding-bottom: 4px;
  margin-bottom: 6px;
}
.suggestion-tooltip-close {
  font-size: 16px;
  top: 4px;
  right: 8px;
}
.suggestion-comparison, .suggestion-diff-container, .suggestion-explanation-container {
  font-size: 12px;
}
.suggestion-diff {
  font-size: 11px;
}
.suggestion-actions {
  margin-top: 8px;
  gap: 6px;
}
.suggestion-actions button {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}
</style>

<style>
/* 法规弹窗自定义样式 */
.regulation-dialog .el-message-box__content {
  max-height: 70vh;
  overflow-y: auto;
}

.regulation-detail h4 {
  color: #409EFF;
  margin-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 10px;
}

.regulation-detail .regulation-content {
  background-color: #f8f9fa;
  padding: 12px;
  border-left: 4px solid #409EFF;
  border-radius: 4px;
  margin: 10px 0;
}

.regulation-detail .regulation-suggestion h5 {
  color: #67c23a;
  margin-bottom: 10px;
}

.regulation-detail .regulation-suggestion p {
  background-color: #f0f9eb;
  padding: 10px;
  border-left: 4px solid #67c23a;
  border-radius: 4px;
}
</style> 

<style lang="scss" scoped>
// ... existing code ...

/* 个性化定制区域样式 */
.ai-polish-personalization {
  background-color: #f9f9ff;
  border-radius: 8px;
  padding: 15px;
  margin: 15px 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.personalization-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 15px;
  position: relative;
  padding-bottom: 8px;
  
  &:after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 40px;
    height: 2px;
    background-color: #409EFF;
  }
}

.personalization-section {
  margin-bottom: 15px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  
  .el-icon {
    margin-right: 6px;
    color: #409EFF;
  }
}

.preference-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
  
  span {
    color: #606266;
  }
  
  .el-select {
    width: 60%;
  }
}

.optimization-options {
  .el-checkbox-group {
    display: flex;
    flex-wrap: wrap;
    
    .el-checkbox {
      margin-right: 15px;
      margin-bottom: 8px;
      font-size: 13px;
    }
  }
}

.terminology-manager {
  .terminology-input {
    margin-bottom: 10px;
  }
  
  .terminology-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
    
    .terminology-tag {
      margin-right: 5px;
      margin-bottom: 5px;
    }
  }
  
  .terminology-empty {
    font-size: 12px;
    color: #909399;
    text-align: center;
    padding: 8px 0;
  }
}
// ... existing code ...

/* 合同检查结果区域样式 */
.check-sidebar {
  background: linear-gradient(135deg, #f6f8fa 0%, #eef5ff 100%);
}

.check-result-area {
  display: flex;
  flex-direction: column;
  gap: 15px;
  overflow-y: auto;
  padding: 0;
  background-color: #f9f9fc;
}

.check-result-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  padding: 15px 20px;
}

.check-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  border-bottom: 1px solid #f0f0f5;
  padding-bottom: 10px;
}

.check-result-header h6 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.check-result-stats {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
}

.stat-item {
  flex: 1;
  min-width: 100px;
  text-align: center;
  padding: 10px;
  border-radius: 6px;
  background-color: #f9f9fa;
  margin: 0 5px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 5px;
  color: #409EFF;
}

.stat-value.danger {
  color: #F56C6C;
}

.stat-value.warning {
  color: #E6A23C;
}

.stat-value.info {
  color: #909399;
}

.stat-label {
  font-size: 13px;
  color: #606266;
}

.check-result-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.check-collapse {
  border: none;
}

.collapse-header {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  
  .el-icon {
    margin-right: 8px;
  }
}

.check-issue-card {
  background-color: #fafafa;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  
  &:last-child {
    margin-bottom: 0;
  }
}

.issue-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  
  .el-icon {
    margin-right: 10px;
  }
  
  h6 {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
  }
}

.issue-content {
  margin-bottom: 15px;
}

.issue-field {
  margin-bottom: 8px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.field-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  margin-bottom: 4px;
}

.field-value {
  font-size: 14px;
  line-height: 1.5;
  color: #333;
  background-color: white;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #eee;
}

.issue-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.empty-result {
  padding: 30px 0;
  color: #909399;
  text-align: center;
}

.check-options {
  .el-checkbox {
    margin-right: 0;
    margin-left: 0;
    display: block;
    margin-bottom: 8px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

/* 适配键盘快捷键处理器 */
.check-keyboard-shortcut {
  display: none;
}

/* 优化检查偏好设置控件样式 */
.check-sidebar {
  .preference-option {
    margin-bottom: 12px;
    
    .el-select {
      width: 100%;  /* 将下拉框宽度设为100% */
      margin-top: 6px;  /* 增加上边距 */
    }
    
    span {
      display: block;  /* 标签单独一行 */
      margin-bottom: 4px;
      font-weight: 500;
    }
  }
  
  .check-options {
    padding: 5px 0;
    
    .el-checkbox {
      height: 32px;
      display: flex;
      align-items: center;
      border-radius: 4px;
      transition: background-color 0.2s;
      padding: 0 8px;
      margin-bottom: 6px;  /* 减小复选框之间的间距 */
      
      &:hover {
        background-color: rgba(64, 158, 255, 0.08);
      }
      
      &:last-child {
        margin-bottom: 0;  /* 最后一个没有底部边距 */
      }
    }
  }
  
  .ai-polish-button {
    margin-bottom: 20px; /* 增加按钮下边距 */
  }

  /* 检查页面特定样式优化 */
  .ai-polish-personalization {
    background-color: #f7f9ff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    width: 100%;
    padding: 15px;
    margin: 12px 0;
    
    .personalization-title {
      font-size: 14px;
      margin-bottom: 12px;
      padding-bottom: 6px;  /* 减小标题下方空间 */
      
      &:after {
        width: 30px;  /* 减小下划线长度 */
        height: 2px;
      }
    }
    
    .personalization-section {
      margin-bottom: 14px;
      background-color: rgba(255, 255, 255, 0.6);
      border-radius: 6px;
      padding: 10px;
      
      &:last-child {
        margin-bottom: 0;  /* 最后一个区段没有底部边距 */
      }
      
      .section-header {
        margin-bottom: 8px;
        .el-icon {
          font-size: 15px;
        }
        
        span {
          font-size: 13px;  /* 稍微小一点的字体 */
        }
      }
    }
  }
  
  /* 特性列表优化 */
  .ai-polish-features {
    margin-top: 12px;
    
    .feature-item {
      padding: 4px 0;  /* 减小特性项目之间的空间 */
      
      &:last-child {
        padding-bottom: 0;
      }
    }
  }
  
  /* 整体宽度控制 */
  width: 240px;  /* 控制左侧栏宽度，使其更紧凑 */
}
// ... existing code ...
</style> 

<style lang="scss">
/* 深色模式适配 */
:deep([data-theme="dark"]), :deep(body.is-dark) {
  /* 主容器和卡片 */
  .contract-detail-container {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
  }
  
  .card {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
    border-color: var(--border-color) !important;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.15) !important;
  }

  .card-header {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
    border-bottom-color: var(--border-color) !important;
  }

  .card-body {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
  }
  
  /* 白色容器元素 - 主要针对截图中显示的问题 */
  .contract-detail-container .el-card,
  .contract-detail-container .el-form,
  .contract-detail-container .row {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
  }
  
  /* 表单区域 */
  :deep(.el-form) {
    background-color: var(--bg-color) !important;
    
    .el-form-item {
      background-color: var(--bg-color) !important;
      
      .el-form-item__label {
        color: var(--text-color) !important;
      }
      
      .el-form-item__content {
        background-color: var(--bg-color) !important;
      }
    }
  }
  
  /* 输入框 */
  :deep(.el-input),
  :deep(.el-select),
  :deep(.el-date-editor) {
    background-color: var(--bg-color) !important;
    
    .el-input__wrapper {
      background-color: var(--bg-color) !important;
      box-shadow: 0 0 0 1px var(--border-color) inset !important;
    }
    
    .el-input__inner {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }
  }
  
  /* 标签页 */
  :deep(.el-tabs) {
    background-color: var(--bg-color) !important;
    
    .el-tabs__header {
      background-color: var(--bg-color) !important;
      border-bottom-color: var(--border-color) !important;
    }
    
    .el-tabs__nav-wrap::after {
      background-color: var(--border-color) !important;
    }
    
    .el-tabs__item {
      color: var(--text-color-secondary) !important;
    }
    
    .el-tabs__item.is-active {
      color: var(--primary-color) !important;
    }
    
    .el-tabs__content {
      background-color: var(--bg-color) !important;
    }
    
    .el-tab-pane {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }
  }
  
  /* 合同文本编辑器和检查区域 */
  .contract-edit-wrapper,
  .contract-edit-container,
  .editor-main-area,
  .check-result-area {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
  }
  
  /* 修复白色背景卡片 */
  #contractTitleHeader {
    color: var(--text-color) !important;
  }
  
  h5, h6 {
    color: var(--text-color) !important;
  }
  
  /* 修复基本信息表单区域 */
  .row, .col-md-6 {
    background-color: var(--bg-color) !important;
  }
  
  /* 富文本编辑器 */
  .contract-text-editor {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
    border-color: var(--border-color) !important;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.15) !important;
    
    :deep(.ql-toolbar) {
      background-color: var(--bg-color-secondary) !important;
      border-color: var(--border-color) !important;
    }
    
    :deep(.ql-container) {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
      border-color: var(--border-color) !important;
    }
    
    :deep(.ql-editor) {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }
  }
  
  /* AI润色侧边栏 */
  .ai-polish-sidebar,
  .check-sidebar {
    background: linear-gradient(135deg, var(--bg-color-secondary) 0%, var(--bg-color-tertiary) 100%) !important;
    border-color: var(--border-color) !important;
  }
  
  /* 修复空状态图片 */
  :deep(.el-empty) {
    background-color: transparent !important;
    
    .el-empty__image, 
    .el-empty__description {
      color: var(--text-color-secondary) !important;
    }
  }
  
  /* 时间线 */
  :deep(.el-timeline) {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
    
    .el-timeline-item__tail {
      border-left-color: var(--border-color) !important;
    }
    
    .el-timeline-item__node {
      background-color: var(--primary-color) !important;
    }
    
    .el-timeline-item__content {
      color: var(--text-color) !important;
    }
    
    .el-timeline-item__timestamp {
      color: var(--text-color-secondary) !important;
    }
  }
  
  /* 修复分割线 */
  hr {
    border-color: var(--border-color) !important;
    background-color: var(--border-color) !important;
  }
  
  /* 修复下拉菜单 */
  :deep(.el-dropdown-menu) {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
    
    .el-dropdown-menu__item {
      color: var(--text-color) !important;
    }
    
    .el-dropdown-menu__item:hover {
      background-color: var(--bg-color-tertiary) !important;
    }
  }
  
  /* 修复弹窗和对话框 */
  :deep(.el-dialog),
  :deep(.el-message-box) {
    background-color: var(--bg-color) !important;
    border-color: var(--border-color) !important;
    
    .el-dialog__header,
    .el-message-box__header {
      background-color: var(--bg-color) !important;
      border-bottom-color: var(--border-color) !important;
    }
    
    .el-dialog__title,
    .el-message-box__title {
      color: var(--text-color) !important;
    }
    
    .el-dialog__body,
    .el-message-box__content {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }
    
    .el-dialog__footer,
    .el-message-box__btns {
      background-color: var(--bg-color) !important;
      border-top-color: var(--border-color) !important;
    }
  }
  
  /* 修复个性化定制区域 */
  .ai-polish-personalization {
    background-color: var(--bg-color-secondary) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    
    .personalization-section {
      background-color: var(--bg-color) !important;
      
      .section-header {
        color: var(--text-color) !important;
        
        span {
          color: var(--text-color) !important;
        }
      }
    }
    
    .personalization-title {
      color: var(--text-color) !important;
    }
  }
  
  /* 修复检查结果区域 */
  .check-result-card,
  .check-result-details,
  .check-issue-card {
    background-color: var(--bg-color-secondary) !important;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2) !important;
  }
  
  .check-content-inner {
    background-color: var(--bg-color) !important;
  }
  
  .check-collapse {
    background-color: transparent !important;
    
    :deep(.el-collapse-item__header) {
      background-color: var(--bg-color-secondary) !important;
      color: var(--text-color) !important;
      border-bottom-color: var(--border-color) !important;
    }
    
    :deep(.el-collapse-item__content) {
      background-color: var(--bg-color-secondary) !important;
      color: var(--text-color) !important;
    }
  }
  
  /* 修复统计项 */
  .stat-item {
    background-color: var(--bg-color) !important;
  }
  
  /* 修复工具提示 */
  :deep(.el-tooltip__popper) {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
    color: var(--text-color) !important;
  }
  
  /* 修复滚动区域 */
  .contract-check-scrollbar {
    background-color: var(--bg-color) !important;
    
    :deep(.el-scrollbar__view) {
      background-color: var(--bg-color) !important;
    }
    
    :deep(.el-scrollbar__bar) {
      background-color: var(--bg-color-tertiary) !important;
    }
  }
  
  /* 修复底部操作按钮区域 */
  .text-end {
    background-color: var(--bg-color) !important;
  }

  /* 修复选择器 */
  :deep(.el-select-dropdown) {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
    
    .el-select-dropdown__item {
      color: var(--text-color) !important;
    }
    
    .el-select-dropdown__item.hover, 
    .el-select-dropdown__item:hover {
      background-color: var(--bg-color-tertiary) !important;
    }
    
    .el-select-dropdown__item.selected {
      color: var(--primary-color) !important;
      background-color: rgba(64, 158, 255, 0.1) !important;
    }
  }
  
  /* 日期选择器 */
  :deep(.el-picker-panel) {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
    color: var(--text-color) !important;
    
    .el-date-picker__header {
      background-color: var(--bg-color-secondary) !important;
      color: var(--text-color) !important;
    }
    
    .el-date-table {
      background-color: var(--bg-color-secondary) !important;
      color: var(--text-color) !important;
      
      th, td {
        background-color: var(--bg-color-secondary) !important;
        color: var(--text-color) !important;
      }
      
      td.current:not(.disabled) span {
        background-color: var(--primary-color) !important;
        color: white !important;
      }
      
      td.available:hover {
        color: var(--primary-color) !important;
      }
      
      td.next-month, td.prev-month {
        color: var(--text-color-tertiary) !important;
      }
    }
  }
  
  /* 复选框 */
  :deep(.el-checkbox) {
    .el-checkbox__label {
      color: var(--text-color) !important;
    }
    
    .el-checkbox__input.is-checked .el-checkbox__inner {
      background-color: var(--primary-color) !important;
      border-color: var(--primary-color) !important;
    }
    
    .el-checkbox__inner {
      background-color: var(--bg-color) !important;
      border-color: var(--border-color) !important;
    }
  }
  
  /* 标签 */
  :deep(.el-tag) {
    background-color: rgba(64, 158, 255, 0.1) !important;
    border-color: rgba(64, 158, 255, 0.2) !important;
    color: var(--primary-color) !important;
    
    &.el-tag--danger {
      background-color: rgba(245, 108, 108, 0.1) !important;
      border-color: rgba(245, 108, 108, 0.2) !important;
      color: #F56C6C !important;
    }
    
    &.el-tag--success {
      background-color: rgba(103, 194, 58, 0.1) !important;
      border-color: rgba(103, 194, 58, 0.2) !important;
      color: #67C23A !important;
    }
    
    &.el-tag--warning {
      background-color: rgba(230, 162, 60, 0.1) !important;
      border-color: rgba(230, 162, 60, 0.2) !important;
      color: #E6A23C !important;
    }
    
    &.el-tag--info {
      background-color: rgba(144, 147, 153, 0.1) !important;
      border-color: rgba(144, 147, 153, 0.2) !important;
      color: #909399 !important;
    }
  }
  
  /* 开关 */
  :deep(.el-switch) {
    .el-switch__core {
      background-color: var(--border-color) !important;
    }
    
    &.is-checked .el-switch__core {
      background-color: var(--primary-color) !important;
    }
  }
}
</style> 

<style lang="scss">
/* 深色模式适配 - 更强力的全局覆盖 */
html[data-theme="dark"] body, body.is-dark {
  /* 强制应用深色背景到所有默认白色元素 */
  .contract-detail-container,
  .contract-detail-container *:not([class*="el-icon"]):not(i):not(svg):not(path) {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
  }
  
  .contract-detail-container {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
    
    /* 卡片样式 */
    .card, .el-card {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
      border-color: var(--border-color) !important;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.15) !important;
      
      .card-header, .el-card__header {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        border-bottom-color: var(--border-color) !important;
      }
      
      .card-body, .el-card__body {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
      }
    }
    
    /* 标签页 */
    .el-tabs {
      background-color: var(--bg-color) !important;
      
      .el-tabs__header {
        background-color: var(--bg-color) !important;
        border-bottom-color: var(--border-color) !important;
      }
      
      .el-tabs__nav-wrap::after {
        background-color: var(--border-color) !important;
      }
      
      .el-tabs__item {
        color: var(--text-color-secondary) !important;
      }
      
      .el-tabs__item.is-active {
        color: var(--primary-color) !important;
      }
      
      .el-tabs__content {
        background-color: var(--bg-color) !important;
      }
      
      .el-tab-pane {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
      }
    }
    
    /* 表单元素 */
    .el-form {
      background-color: var(--bg-color) !important;
      
      .el-form-item {
        background-color: var(--bg-color) !important;
        
        .el-form-item__label {
          color: var(--text-color) !important;
        }
        
        .el-form-item__content {
          background-color: var(--bg-color) !important;
        }
      }
    }
    
    /* 输入框和控件 */
    .el-input__wrapper,
    .el-textarea__wrapper {
      background-color: var(--bg-color) !important;
      box-shadow: 0 0 0 1px var(--border-color) inset !important;
    }
    
    .el-input__inner,
    .el-textarea__inner {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }
    
    .el-select .el-input__wrapper {
      background-color: var(--bg-color) !important;
    }
    
    .el-date-editor {
      background-color: var(--bg-color) !important;
      
      .el-input__wrapper {
        background-color: var(--bg-color) !important;
      }
    }
    
    /* 修复编辑器区域 */
    .ql-toolbar.ql-snow {
      background-color: var(--bg-color-secondary) !important;
      border-color: var(--border-color) !important;
    }
    
    .ql-container.ql-snow {
      background-color: var(--bg-color) !important;
      border-color: var(--border-color) !important;
    }
    
    .ql-editor {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }
    
    /* 合同文本编辑器和检查区域 */
    .contract-edit-wrapper,
    .contract-edit-container {
      background-color: var(--bg-color) !important;
      
      .editor-main-area,
      .check-result-area {
        background-color: var(--bg-color) !important;
      }
    }
    
    /* AI润色侧边栏 */
    .ai-polish-sidebar,
    .check-sidebar {
      background: linear-gradient(135deg, var(--bg-color-secondary) 0%, var(--bg-color-tertiary) 100%) !important;
      border-color: var(--border-color) !important;
    }
    
    /* 个性化定制区域 */
    .ai-polish-personalization {
      background-color: var(--bg-color-secondary) !important;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
      
      .personalization-section {
        background-color: var(--bg-color) !important;
        
        .section-header {
          color: var(--text-color) !important;
          
          span {
            color: var(--text-color) !important;
          }
        }
      }
      
      .personalization-title {
        color: var(--text-color) !important;
      }
    }
    
    /* 统计项 */
    .stat-item {
      background-color: var(--bg-color) !important;
      
      .stat-label {
        color: var(--text-color-secondary) !important;
      }
    }
    
    /* 检查结果区域 */
    .check-result-card,
    .check-result-details,
    .check-issue-card {
      background-color: var(--bg-color-secondary) !important;
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2) !important;
    }
    
    .check-content-inner {
      background-color: var(--bg-color) !important;
      padding: 15px 20px !important;
    }
    
    /* 滚动区域 */
    .el-scrollbar {
      background-color: var(--bg-color) !important;
      
      .el-scrollbar__view {
        background-color: var(--bg-color) !important;
      }
    }
    
    /* 强制应用到动态生成的元素 */
    div[class*="contract"],
    div[class*="card"],
    div[class*="box"],
    div[class*="panel"],
    div[class*="content"],
    div[class*="wrapper"],
    div[class*="container"] {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }
    
    /* 表格 */
    .el-table {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
      
      .el-table__header, 
      .el-table__body, 
      .el-table__footer {
        background-color: var(--bg-color) !important;
      }
      
      th, td {
        background-color: var(--bg-color) !important;
        border-bottom-color: var(--border-color) !important;
      }
      
      .el-table__row {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
      }
      
      .el-table__cell {
        background-color: var(--bg-color) !important;
      }
    }
  }
  
  /* 强制覆盖弹出元素 */
  .el-select-dropdown,
  .el-dropdown-menu,
  .el-picker-panel,
  .el-tooltip__popper {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
    color: var(--text-color) !important;
    
    .el-select-dropdown__item,
    .el-dropdown-menu__item,
    .el-date-table td,
    .el-date-table th,
    .el-month-table td,
    .el-year-table td {
      color: var(--text-color) !important;
      background-color: var(--bg-color-secondary) !important;
    }
    
    .el-select-dropdown__item.hover, 
    .el-select-dropdown__item:hover,
    .el-dropdown-menu__item:hover {
      background-color: var(--bg-color-tertiary) !important;
    }
    
    .el-select-dropdown__item.selected {
      color: var(--primary-color) !important;
      background-color: rgba(64, 158, 255, 0.1) !important;
    }
    
    .el-date-table td.current:not(.disabled) span {
      background-color: var(--primary-color) !important;
      color: white !important;
    }
  }
  
  /* 修复时间线 */
  .el-timeline {
    background-color: var(--bg-color) !important;
    color: var(--text-color) !important;
    
    .el-timeline-item__tail {
      border-left-color: var(--border-color) !important;
    }
    
    .el-timeline-item__node {
      background-color: var(--primary-color) !important;
    }
    
    .el-timeline-item__content {
      color: var(--text-color) !important;
    }
    
    .el-timeline-item__timestamp {
      color: var(--text-color-secondary) !important;
    }
  }
  
  /* 修复空状态 */
  .el-empty {
    background-color: transparent !important;
    
    .el-empty__image, 
    .el-empty__description {
      color: var(--text-color-secondary) !important;
    }
  }
  
  /* 对话框和消息框 */
  .el-dialog,
  .el-message-box {
    background-color: var(--bg-color) !important;
    border-color: var(--border-color) !important;
    
    .el-dialog__header,
    .el-message-box__header {
      background-color: var(--bg-color) !important;
      border-bottom-color: var(--border-color) !important;
    }
    
    .el-dialog__title,
    .el-message-box__title {
      color: var(--text-color) !important;
    }
    
    .el-dialog__body,
    .el-message-box__content {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }
    
    .el-dialog__footer,
    .el-message-box__btns {
      background-color: var(--bg-color) !important;
      border-top-color: var(--border-color) !important;
    }
  }
  
  /* 修复组件边框 */
  hr, 
  .el-divider {
    border-color: var(--border-color) !important;
    background-color: var(--border-color) !important;
  }

  /* 专门处理运行时生成的编辑器框架 */
  iframe.ql-video {
    background-color: black !important;
  }
  
  .ql-picker-options {
    background-color: var(--bg-color-secondary) !important;
    color: var(--text-color) !important;
    border-color: var(--border-color) !important;
  }
  
  .ql-tooltip {
    background-color: var(--bg-color-secondary) !important;
    color: var(--text-color) !important;
    border-color: var(--border-color) !important;
    
    input[type="text"] {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
      border-color: var(--border-color) !important;
    }
  }
  
  /* 修复可能的内联样式问题 */
  [style*="background-color: white"],
  [style*="background-color:#fff"],
  [style*="background-color:#ffffff"],
  [style*="background: white"],
  [style*="background:#fff"],
  [style*="background:#ffffff"] {
    background-color: var(--bg-color) !important;
  }
  
  [style*="color:black"],
  [style*="color: black"],
  [style*="color:#000"],
  [style*="color:#000000"] {
    color: var(--text-color) !important;
  }
  
  /* 修复AI建议面板 */
  .ai-suggestions-panel {
    background-color: var(--bg-color-secondary) !important;
    border-color: var(--border-color) !important;
    box-shadow: -3px 0 10px rgba(0, 0, 0, 0.15) !important;
    
    .panel-header {
      color: var(--text-color) !important;
      background-color: var(--bg-color-secondary) !important;
    }
    
    .suggestion-item {
      background-color: var(--bg-color) !important;
      border-color: var(--border-color) !important;
    }
    
    .explanation {
      color: var(--text-color-secondary) !important;
    }
  }
  
  /* 按钮和浮动元素 */
  .panel-open-button {
    background-color: var(--bg-color-secondary) !important;
    box-shadow: -2px 0 5px rgba(0, 0, 0, 0.2) !important;
  }
  
  /* 修复AI按钮在深色模式下的显示问题 */
  .ai-polish-button, 
  .check-sidebar .ai-polish-button,
  button.el-button.ai-polish-button {
    background: linear-gradient(45deg, #409EFF, #64b5f6) !important;
    
    .ai-polish-button-content {
      background: transparent !important;
    }
    
    /* 特别针对图标区域的背景色问题 */
    .el-icon,
    .ai-polish-icon,
    .ai-polish-icon svg,
    svg,
    path {
      background-color: transparent !important;
      box-shadow: none !important;
      fill: currentColor !important;
    }
    
    /* 修复文本区域 */
    span {
      background-color: transparent !important;
      color: white !important;
    }
    
    /* 给所有子元素强制应用透明背景 */
    * {
      background-color: transparent !important;
    }
  }
  
  /* 强制修复像素级别图标 */
  .ai-polish-icon.no-bg,
  .ai-polish-icon.no-bg svg,
  .ai-polish-icon.no-bg path {
    background-color: transparent !important;
    background: transparent !important;
    color: white !important;
    fill: white !important;
  }
  
  /* 去掉特定元素的背景 */
  .contract-edit-wrapper .ai-polish-sidebar *,
  .contract-edit-wrapper .check-sidebar * {
    &:not(.ai-polish-personalization):not(.ai-polish-features) {
      background-color: transparent !important;
    }
  }
}
</style>

/* 修复建议工具提示样式 */
.suggestion-tooltip {
  z-index: 9999;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  padding: 0;
  max-width: 450px;
  border: 1px solid #ebeef5;
  font-size: 14px;
  position: absolute !important;
  pointer-events: auto !important;
}

.suggestion-tooltip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f5f7fa;
  padding: 10px 15px;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.suggestion-tooltip-title {
  font-weight: bold;
  color: #303133;
}

.suggestion-tooltip-close {
  cursor: pointer;
  color: #909399;
  font-size: 18px;
}

.suggestion-tooltip-body {
  padding: 15px;
}

.suggestion-comparison {
  display: flex;
  margin-bottom: 10px;
  gap: 10px;
}

.suggestion-column {
  flex: 1;
}

.suggestion-divider {
  width: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.suggestion-divider:before {
  content: "→";
  color: #909399;
  font-size: 18px;
}

.suggestion-label {
  font-weight: bold;
  margin-bottom: 5px;
  color: #606266;
}

.suggestion-original {
  background-color: #fff5f5;
  color: #f56c6c;
  border: 1px solid #fde2e2;
  padding: 8px 12px;
  border-radius: 4px;
  word-break: break-word;
}

.suggestion-suggested {
  background-color: #f0f9eb;
  color: #67c23a;
  border: 1px solid #e1f3d8;
  padding: 8px 12px;
  border-radius: 4px;
  word-break: break-word;
}

.suggestion-diff-container {
  margin-bottom: 10px;
}

.suggestion-diff {
  background-color: #fafafa;
  border: 1px solid #ebeef5;
  padding: 8px 12px;
  border-radius: 4px;
  word-break: break-word;
}

.suggestion-explanation-container {
  margin-bottom: 10px;
}

.suggestion-explanation {
  font-style: italic;
  color: #606266;
}

.suggestion-actions {
  padding: 10px 15px;
  border-top: 1px solid #e4e7ed;
  text-align: right;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.suggestion-actions button {
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.3s;
}

.suggestion-actions .btn-adopt {
  background-color: #67c23a;
  color: white;
}

.suggestion-actions .btn-adopt:hover {
  background-color: #5daf34;
}

.suggestion-actions .btn-ignore {
  background-color: #f4f4f5;
  color: #909399;
  border-color: #dcdfe6;
}

.suggestion-actions .btn-ignore:hover {
  background-color: #e9e9eb;
}

/* 全局样式确保高亮建议可点击 */
.suggestion-highlight, 
[data-suggestion-id],
.ql-editor [data-suggestion-id],
.ql-editor .suggestion-highlight {
  pointer-events: auto !important;
  cursor: pointer !important;
  background-color: rgba(255, 217, 102, 0.3) !important;
  border-bottom: 1px dashed #ffb300 !important;
  z-index: 999 !important;
  position: relative !important;
  display: inline-block !important;
}

/* 添加新的顶部导航栏样式 */
.top-navigation-bar {
  background-color: #ffffff;
  padding: 10px 20px 0;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

/* 修改标签页样式使其更美观 */
.contract-detail-tabs .el-tabs__header {
  margin-bottom: 0;
}

.contract-detail-tabs .el-tabs__nav {
  border: none;
}

.contract-detail-tabs .el-tabs__item {
  height: 40px;
  line-height: 40px;
  font-size: 15px;
  font-weight: 500;
}

.contract-detail-tabs .el-tabs__item.is-active {
  font-weight: bold;
  color: #409eff;
}

/* 卡片样式优化 */
.card {
  border: none;
  border-radius: 6px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
