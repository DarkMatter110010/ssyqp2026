<div align="center">

<img src="server/static/img/GDEHS.png" alt="广东实验中学校徽" width="132"/>

# 益起跑 · 班级里程展示与统计系统

**广东实验中学「益起跑」公益跑步活动 · 2026**

> **此程序基于MIT许可证开源**

`Python / Flask`　·　`Vue 3`　·　`SQLite`　·　`Nginx`　·　`PyQt6`

</div>

<br/>

---

## 📖 项目简介

「益起跑」是广东实验中学的公益跑步活动。系统以 **班级** 为单位累计跑步里程，
将全校师生的每一段脚步实时汇聚成一场看得见的公益接力：

- 🖥️ **现场大屏**展示全校总里程与班级里程排行，营造活动氛围；
- ⌨️ 由各班代表在 **数据录入页**（支持触屏小键盘）快速登记里程；
- 🔐 所有写操作均需口令校验，数据全程 **加盐哈希**，明文密码不落库、不传输；
- 📦 全部依赖 **离线可用**（内置 Vue、字体、Nginx、OpenSSL），内网部署零外链。

---

## ✨ 核心功能

| 功能模块 | 说明 |
| --- | --- |
| 🖥️ 里程展示大屏 | 总里程大卡片 + 数字滚动动画、班级实时排行、公益格言轮播；每 **5 秒** 自动轮询刷新 |
| 📝 班级里程录入 | 面向触屏/大屏的录入页：**自动弹出小键盘**、输入自动过滤非数字、滚轮可按 **400 米**（一圈操场）步进 |
| 📊 数据管理客户端 | 基于 PyQt6 的桌面工具，通过网络 API 完成 **写入 / 累加 / 删除 / 查看**，不直接接触数据库 |
| 🛠️ 数据库调试工具 | 服务器本机直连 SQLite 的调试工具，便于快速纠错、冲减多记里程 |
| 🔒 HTTPS 内网加密 | 内置 Nginx 反向代理 + 本地 CA 自签名证书，浏览器一键信任，全程加密传输 |
| 🔑 口令保护 | 管理操作需要口令，前端计算 `SHA-256(密码 + 盐)` 后比对密文，采用常数时间比较防时序攻击 |

---

## 🏗️ 系统架构

```
┌──────────────┐   ┌────────────────┐   ┌────────────────────┐   ┌───────────┐
│   现场大屏    │   │  HTTPS 网关     │   │   Flask 后端        │   │  SQLite   │
│ Vue 3 看板   │──▶│  Nginx :7443   │──▶│  127.100.10.1:5050 │──▶│  data.db  │
│   (浏览器)    │   │  (反向代理+SSL) │   │   (main.py)        │   │  (单文件)  │
└──────────────┘   └────────────────┘   └────────────────────┘   └───────────┘
┌──────────────┐            ▲ HTTPS(7443)
│   数据录入页   │────────────┘
│ (config.html)│
└──────────────┘
┌─────────────────────┐            ▲ HTTPS API（写入/累加/删除/查询）
│  数据管理客户端       │────────────┘
│  data_client/*.py   │
└─────────────────────┘
┌─────────────────────┐            ▲ 直接读写（仅限服务器本机调试）
│  数据库调试工具       │────────────┘
│  server/db_debug.py │
└─────────────────────┘
```

| 组件 | 技术选型 | 职责 |
| --- | --- | --- |
| 页面展示 | Vue 3（本地 `vue.global.prod.js`，CDN 离线可用） | 大屏看板、数据录入、结果反馈 |
| Web 服务 | Python Flask | 路由渲染 + 提供 `/api/*` JSON 接口 |
| 网关层 | Nginx for Windows | `:7443` HTTPS 反向代理到后端 `:5050` |
| 数据存储 | SQLite（`server/data.db` 单文件） | 每班一条记录：`班级代号` + `里程(米)` |
| 桌面端 | PyQt6 | 数据管理客户端 / 本机数据库调试工具 |

---

## 📁 目录结构

```
益起跑网页程序/
├─ start.bat                  # 🚀 一键启动：Flask + Nginx + 浏览器 + 管理客户端
├─ stop.bat                   # 🛑 一键停止全部服务
├─ README.md
│
├─ server/                    # ── 后端服务 ──
│  ├─ main.py                 # Flask 主程序（路由 + API）
│  ├─ db_tool.py              # SQLite 数据库操作模块
│  ├─ db_debug.py             # 本机数据库调试工具（PyQt6，直连库）
│  ├─ config.json             # 服务端配置（端口 / SSL / 口令哈希）
│  ├─ data.db                 # SQLite 数据库文件
│  ├─ templates/              # index.html 大屏 / config.html 录入页
│  ├─ static/                 # css / js / 字体 / 校徽等静态资源
│  ├─ nginx/                  # 内置 Nginx（HTTPS 反向代理）
│  ├─ ssl/                    # 本地 CA 与自签名证书（gen_cert.bat 可重建）
│  └─ openssl/                # 内置 OpenSSL 工具（生成证书用）
│
├─ data_client/               # ── 桌面管理客户端 ──
│  ├─ db_client.py            # PyQt6 客户端：写入/累加/删除/查看
│  └─ settings.ini            # 客户端配置（服务器地址 / 盐）
│
└─ .venv/                     # Python 虚拟环境（Flask、PyQt6）
```

---

## 🚀 快速开始

### 1. 环境要求

| 依赖 | 说明 |
| --- | --- |
| Windows | 本项目面向内网 Windows 部署 |
| Python 3.9+ | 需安装并勾选 *Add to PATH* |
| 虚拟环境 `.venv` | 已随项目就绪；若需重建：`python -m venv .venv`，再安装 `flask`、`pyqt6` |

> 💡 若在新机器重建虚拟环境，可在项目根目录执行：
> ```bat
> python -m venv .venv
> .venv\Scripts\pip install flask pyqt6
> ```

### 2. 一键启动

双击项目根目录的 **`start.bat`**，脚本会自动完成：

1. 清理可能残留的 `nginx.exe` 与占用 `:5050` 的进程；
2. 启动 Flask 后端（`.venv` 中运行 `server\main.py`）；
3. 启动内置 Nginx（监听 `https://127.100.10.1:7443`）；
4. 自动打开浏览器访问 **大屏主页**；
5. 同时弹出 **数据管理客户端** 窗口。

浏览器访问地址：

```
https://127.100.10.1:7443/
```

| 页面 | 地址 |
| --- | --- |
| 🖥️ 里程大屏主页 | `https://127.100.10.1:7443/` |
| 📝 班级里程录入 | `https://127.100.10.1:7443/config.html` |

### 3. 一键停止

双击 **`stop.bat`** 即可结束 Nginx 与 Python 服务进程。

> ⚠️ 注意：`stop.bat` 会结束**本机所有** `python.exe` 进程，请先保存其他 Python 程序的运行结果再执行。

### 4. 手动运行（可选）

```bat
:: 启动后端（默认 https://127.100.10.1:7443）
.venv\Scripts\python server\main.py

:: 本机数据库调试工具（直连 data.db，不经网络）
.venv\Scripts\python server\db_debug.py

:: 桌面数据管理客户端（走 HTTPS API）
.venv\Scripts\python data_client\db_client.py
```

---

## ⚙️ 配置说明

### 服务端 `server/config.json`

```json
{
  "database": { "path": "data.db", "table": "data_table" },
  "server":   { "host": "127.100.10.1", "port": 5050,
                "access_url": "https://127.100.10.1:7443/" },
  "ssl":      { "enabled": true, "cert": "ssl/cert.pem", "key": "ssl/key.pem" },
  "password": { "hash": "82ba…24291", "salt": "b7c85d29-…-bc9" }
}
```

| 配置项 | 含义 |
| --- | --- |
| `database.path` | SQLite 文件路径（相对 `server/`） |
| `server.host / port` | Flask 监听地址与端口（默认 `5050`） |
| `server.access_url` | 启动成功后提示访问的完整地址 |
| `ssl` | 是否启用 HTTPS 及证书文件位置（证书缺失时自动回退 HTTP） |
| `password.hash / salt` | 管理口令的密文（`SHA-256(口令+盐)`）与盐值 |

### 客户端 `data_client/settings.ini`

```ini
[server]
url  = https://127.100.10.1:7443   ; 接口根地址（留空则取 host+port）
host = 127.100.10.1
port = 7443

[security]
salt = b7c85d29-…-bc9              ; 必须与 server/config.json 的 salt 一致

[setting]
topmost  = true                    ; 客户端窗口启动即置顶
selfclean = false                  ; 提交后是否自动清空班级/里程输入框
```

### 🔑 修改管理口令

口令校验方式是 `SHA-256(口令 + salt)`，密文保存在 `server/config.json`。修改方法：

```bat
:: 用 Python 计算新口令的密文（示例：把口令和盐替换为你自己的）
.venv\Scripts\python -c "import hashlib;print(hashlib.sha256(('你的口令'+'你的盐').encode()).hexdigest())"
```

将输出的 64 位十六进制串填入 `config.json` 的 `password.hash`，
**并确保** `config.json`、`settings.ini`、`static/js/config.js` 三处的 `salt` 一致。

---

## 🏫 班级代号规则

班级代号为 **3 位数字**：`百位` 表示年级段，`十位个位`（1–99）表示班号。

| 代号范围 | 年级段 | 大屏显示前缀 |
| --- | --- | --- |
| `101`–`199` | 高一 | D |
| `201`–`299` | 高二 | E |
| `301`–`399` | 高三 | F |
| `401`–`499` | 高一国际部 | DAP |
| `501`–`599` | 高二国际部 | EAP |
| `601`–`699` | 高三国际部 | FAP |

> 示例：`201` → **E1**（高二 1 班）、`405` → **DAP5**（高一国际部 5 班）。
> 前后端均会校验代号合法性，不合法的代号将被拒绝。

---

## 🔌 接口文档（RESTful JSON）

所有接口均为 `POST`，请求体为 JSON。写操作需要 `password` 字段（前端已加盐哈希的密文）。

| 接口 | 功能 | 鉴权 | 请求体 |
| --- | --- | --- | --- |
| `POST /api/add` | 为某班 **累加** 里程（不存在则新建） | ✅ 需密码 | `{class_code, distance, password}` |
| `POST /api/write` | **覆盖设置** 某班里程 | ✅ 需密码 | `{class_code, distance, password}` |
| `POST /api/delete` | 删除某班记录 | ✅ 需密码 | `{class_code, password}` |
| `POST /api/query` | 查询某班当前里程 | — | `{class_code}` |
| `POST /api/sum` | 全校总里程 | — | `{}` |
| `POST /api/list` | 全部班级排行（里程降序） | — | `{}` |

**统一响应结构：**

```jsonc
// 成功
{ "status": "ok",    "distance": 1200 }
// 失败
{ "status": "error", "message": "密码错误" }
```

**示例调用（PowerShell）：**

```powershell
# 为 201 班累加 400 米
$body = @{ class_code = "201"; distance = 400; password = "<口令哈希>" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://127.100.10.1:7443/api/add" `
                  -Method Post -ContentType "application/json" -Body $body
```

> 💡 里程单位为 **米**，取值范围 `0 ~ 9,999,999` 的整数；录入页的滚轮步进按一圈操场 **400 米** 计算。

---

## 🔐 安全设计

- 🔑 口令不以明文出现在数据库中，也不以明文在网络中传输；
- 🧂 前端先拼接盐值再做 SHA-256 哈希，服务端仅比对密文；
- ⏱️ 密文比对使用 `hmac.compare_digest` 常数时间比较，降低时序侧信道风险；
- 🛡️ 写入 / 累加 / 删除均为幂等外写操作，客户端对**读接口**才启用断线自动重连，避免写操作被重复执行；
- 🔒 全程走 HTTPS：Nginx 承担 TLS 终结，后端亦可选启用 SSL；
- 🗄️ 数据落库前统一校验：班级代号合法性、里程数值范围、口令是否为空。

---

## 🛠️ HTTPS 证书（首次 / 换机部署）

项目已内置生成好的本地 CA 与服务器证书；当需要**重建证书**时，双击：

```
server\ssl\gen_cert.bat
```

脚本将使用内置 OpenSSL 依次完成：备份旧证书 → 创建本地根 CA → 签发服务器证书 →
合成 Nginx 所需 `cert.pem` → **自动导入 Windows 受信任根证书**。
重新生成后无需修改任何配置，重启服务即可生效。

> 若浏览器提示“证书不受信任”，运行一次 `gen_cert.bat` 即可把本地 CA 装进系统受信任根证书库；若目标设备与服务器不在同一系统（如投影终端），可手动把 `server/ssl/ca.crt` 导入其受信任根证书存储。

---

## ❓ 常见问题

<details>
<summary><b>启动后浏览器无法访问页面？</b></summary>

依次排查：① 查看 `server/nginx/logs/error.log`；② 确认 `:5050`、`:7443` 未被其他程序占用
（可先执行 `stop.bat` 后重新运行 `start.bat`）；③ 若改动过监听地址，需同步修改
`config.json`、`nginx/conf/nginx.conf` 与 `settings.ini` 三处。
</details>

<details>
<summary><b>想在其他电脑（如大屏终端）访问页面？</b></summary>

当前默认地址 `127.100.10.1` 为回环地址，只能在本机访问。若需跨设备访问，请改用服务器
真实局域网 IP（如 `192.168.x.x`），并同步更新上述三处配置；浏览器首次访问时确认信任自签名证书。
</details>

<details>
<summary><b>数据库如何备份 / 迁移？</b></summary>

数据全部保存在单个文件 `server/data.db`，**直接复制该文件**即可完成备份或迁移；迁移后保持
文件位于 `server/` 目录、文件名与 `config.json` 一致即可。
</details>

<details>
<summary><b>忘记管理口令怎么办？</b></summary>

按上文「修改管理口令」一节重新计算密文，替换 `config.json` 中的 `password.hash` 即可（盐值可保持不变）。
</details>

<details>
<summary><b>多记了里程怎么冲减？</b></summary>

若在服务器本机，可用 `server/db_debug.py` 对指定班级直接**累加负数**来冲减，或使用“写入”功能覆盖为正确值。
</details>

<br/>

---

<div align="center">

**广东实验中学 · 益起跑 2026**

跑出健康 · 跑出公益 · 跑向更好的未来 🏃

</div>
