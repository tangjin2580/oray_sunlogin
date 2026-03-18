# Oray Sunlogin Home Assistant Integration

基于向日葵官方API开发的Home Assistant自定义集成组件，用于控制向日葵智能插座、插线板等硬件设备。

## 功能特点

- 支持控制向日葵智能插座（C1、C2、C1Pro等）
- 支持控制向日葵智能插线板（P1、P2、P4等）
- 支持获取用电量数据
- 支持获取功率数据
- 云端API控制，无需本地局域网
- 支持配置刷新间隔

## 支持的设备

- 向日葵智能插座 C1/C1-2/C1Pro/C1Pro-BLE
- 向日葵智能插座 C2/C2-BLE
- 向日葵智能插线板 P1/P1Pro/P2/P4/P8/P8Pro

## 安装方式

### 方法1：手动安装

1. 下载本仓库
2. 将 `custom_components/oray_sunlogin` 文件夹复制到 Home Assistant 配置目录下的 `custom_components` 文件夹中

```bash
# 示例（Linux/macOS）
cp -r custom_components/oray_sunlogin ~/.homeassistant/custom_components/
```

### 方法2：通过HACS安装

1. 打开HACS
2. 点击右上角的「Custom repositories」
3. 输入仓库地址：`https://github.com/your-repo/oray_sunlogin`
4. 选择类型为「Integration」
5. 点击「Add」
6. 安装完成后重启Home Assistant

## 配置

### 首次配置

1. 进入 Home Assistant「设置」→「设备与服务」
2. 点击「添加集成」
3. 搜索「Oray Sunlogin」并点击
4. 输入贝锐账号（手机号或邮箱）和密码
5. 点击「提交」

### 配置选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| 扫描间隔 | 设备状态刷新间隔（秒） | 30秒 |

## 开发说明

### API接口

本插件使用向日葵开放平台API：

- 身份授权：`POST /common/v1/authorization`
- 获取插座列表：`GET /socket/list`
- 获取插座状态：`GET /socket/status?deviceId=xxx`
- 控制插座：`POST /socket/control`
- 获取用电量：`GET /socket/electricity?deviceId=xxx`

### 文件结构

```
custom_components/oray_sunlogin/
├── __init__.py           # 组件初始化
├── manifest.json         # 组件清单
├── config_flow.py       # 配置流程
├── const.py             # 常量定义
├── api.py               # API封装类
├── coordinator.py       # 数据协调器
├── switch.py           # 开关实体
├── sensor.py           # 传感器实体
└── translations/        # 翻译文件
    ├── zh.json
    └── en.json
```

## 注意事项

1. 本插件需要向日葵企业+版账号才能使用API功能
2. 插件通过云端API控制设备，需要保持网络连接
3. 首次配置需要提供贝锐账号密码用于获取API访问凭证
4. 凭证会自动刷新，无需手动处理

## 许可证

Apache License 2.0

## 贡献

欢迎提交Issue和Pull Request！
