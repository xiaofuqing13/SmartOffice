# 3D办公AI形象模型说明

## 模型要求

请在此目录放置名为`office_avatar.glb`的3D模型文件，该模型应满足以下要求：

1. 使用glTF 2.0格式（.glb文件）
2. 包含办公主题的人形角色
3. 最好包含以下动画：
   - 待机/呼吸动画
   - 说话/回应动画
   - 点头/手势动画

## 推荐资源

您可以从以下资源获取合适的3D模型：

1. [Sketchfab](https://sketchfab.com/) - 有许多免费和付费的3D模型
2. [Mixamo](https://www.mixamo.com/) - Adobe提供的角色和动画
3. [Ready Player Me](https://readyplayer.me/) - 创建自定义3D头像
4. [TurboSquid](https://www.turbosquid.com/) - 专业3D模型市场

## 自定义配置

如果您使用的模型文件名不是`office_avatar.glb`，请修改`Office3DAvatar.vue`组件中的`modelPath`属性。

## 性能注意事项

为了获得最佳性能：
- 模型多边形数量应控制在10,000以下
- 纹理分辨率不应超过2048x2048
- 动画关键帧应适当优化 