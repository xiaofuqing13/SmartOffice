// 不使用defineConfig函数，直接导出配置对象
module.exports = {
  transpileDependencies: ['quill'],
  devServer: {
    port: 8080,
    host: 'localhost',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
        // 移除了 pathRewrite 规则
      }
    }
  },
  chainWebpack: config => {
    config.plugin('define').tap(definitions => {
      // 确保对象存在
      if (!definitions[0]) {
        definitions[0] = {}
      }
      if (!definitions[0]['__VUE_OPTIONS_API__']) {
        definitions[0]['__VUE_OPTIONS_API__'] = true
      } else {
        definitions[0]['__VUE_OPTIONS_API__'] = true
      }
      
      if (!definitions[0]['__VUE_PROD_DEVTOOLS__']) {
        definitions[0]['__VUE_PROD_DEVTOOLS__'] = false
      } else {
        definitions[0]['__VUE_PROD_DEVTOOLS__'] = false
      }
      
      definitions[0]['__VUE_PROD_HYDRATION_MISMATCH_DETAILS__'] = JSON.stringify(false)
      
      return definitions
    })
  }
}