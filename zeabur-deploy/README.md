# Hermes Agent → Zeabur 部署指南 (飞书网关模式)

## 📋 前提条件

- ✅ Zeabur 账号 (已登录 CLI `zeabur auth login`)
- ✅ 飞书应用已创建 (App ID + Secret，需开启 WebSocket 长连接)
- ✅ 模型提供商 API Key (Nous/OpenRouter/其他)

## 🏗️ 架构

```
┌──────────────────────────────┐
│  Zeabur Container (~200MB)   │
│  python:3.13-slim + lark-oapi│
│  hermes gateway run          │
│  Volume: /opt/data           │
└──────────┬───────────────────┘
           │ WebSocket (出站)
           ▼
    ┌──────────────┐
    │  飞书服务器    │◄── 你 (手机/电脑)
    └──────────────┘
```

- **连接**: WebSocket (容器→飞书，无需暴露端口)
- **持久化**: Volume `/opt/data` (config, sessions, memory)
- **资源**: ~200MB RAM, 空闲时接近 0 CPU

## 📁 文件说明

| 文件 | 用途 |
|------|------|
| `Dockerfile.zeabur` | 轻量 Dockerfile (repo 根目录) |
| `docker-entrypoint.sh` | 容器启动脚本 |
| `zeabur-deploy/.env.example` | 环境变量模板 |
| `zeabur-deploy/config.yaml` | 云部署配置模板 |

## 🚀 部署步骤

### 1. 推送代码到 GitHub

```bash
cd ~/.hermes/hermes-agent

# 如果还没有 fork：
gh repo fork NousResearch/hermes-agent --clone=false
git remote add my-fork https://github.com/YOUR_USERNAME/hermes-agent.git

# 推送部署文件
git add Dockerfile.zeabur docker-entrypoint.sh zeabur-deploy/
git commit -m "feat: add Zeabur deployment config (Feishu gateway)"
git push my-fork main
```

### 2. 在 Zeabur 创建服务

**方式 A — Dashboard (推荐)**:
1. 打开 https://zeabur.com → New Project
2. "Import from GitHub" → 选择你的 hermes-agent fork
3. **Build Settings**:
   - Dockerfile Path: `Dockerfile.zeabur`
   - Root Directory: `/` (repo root)

**方式 B — CLI**:
```bash
cd ~/.hermes/hermes-agent
zeabur deploy --create --name hermes-feishu
```

### 3. 配置环境变量

在 Zeabur Dashboard → Service → Variables 添加:

```bash
# 飞书
FEISHU_APP_ID=cli_a955a5373f38dcd4
FEISHU_APP_SECRET=<你的飞书App Secret>
FEISHU_DOMAIN=feishu
FEISHU_CONNECTION_MODE=websocket
FEISHU_GROUP_POLICY=open

# 模型 (选一个)
NOUS_API_KEY=<你的Nous Key>
# 或
OPENROUTER_API_KEY=<你的OpenRouter Key>
```

### 4. 添加持久化 Volume

Zeabur Dashboard → Service → Volumes:
- Mount Path: `/opt/data`
- Size: 1GB

### 5. 部署! 🎉

点击 Deploy，首次构建约 2-5 分钟。

## 🔧 首次启动后

容器启动后会自动复制默认 config.yaml 到 Volume。你可能需要修改：

**通过 Zeabur Console 编辑**:
1. Dashboard → Service → Console
2. `vi /opt/data/config.yaml`

关键配置项:
```yaml
model:
  default: "xiaomi/mimo-v2-pro"
  provider: "nous"          # 或 openrouter
  base_url: "https://inference-api.nousresearch.com/v1"
```

修改后重启容器生效。

## 💰 费用

| Zeabur 计划 | 月费 | 适合 |
|------------|------|------|
| Free | $0 | 测试 (会休眠) |
| Developer | ~$5 | 24/7 轻量服务 ✅ |
| Team | ~$20 | 生产环境 |

实际消耗: 内存 ~200MB, CPU 极低, 带宽仅心跳+API调用。

## ❓ 常见问题

**飞书连不上？**
- 检查应用是否开启了 "WebSocket 长连接"
- 应用需已发布/上线
- `FEISHU_CONNECTION_MODE` 必须是 `websocket`

**如何更新？**
```bash
git push my-fork main  # Zeabur 自动重新部署
```

**如何查看日志？**
Dashboard → Service → Logs

**想启用更多工具 (terminal/file/web)？**
编辑 config.yaml 对应 toolset，但注意容器安全风险。

## ⚠️ 注意事项

- 云部署中默认禁用 browser/terminal 工具 (安全考虑)
- API Keys 使用 Zeabur 加密变量存储
- Volume 保证数据持久化，但不包含 hermes-agent 源码更新
