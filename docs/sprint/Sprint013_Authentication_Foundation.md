# Sprint013 - Authentication Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 WorkOps Authentication Foundation。

实现：

- User 基础模型
- Session 登录机制
- Cookie Session 管理
- Login 页面
- Logout
- Current User 状态

---

# Goals

- 建立 Login Page
- 建立 Session 管理
- 建立 User Store
- 建立 Auth Service
- 建立 Permission 基础结构
- 使用 Components

---

# Scope

允许：

- Session Authentication
- Cookie
- Login Form
- Logout
- User Store
- Auth Service
- Permission 基础结构

禁止：

- JWT
- OAuth
- External Identity Provider
- LDAP
- SSO
- MFA
- 真实用户数据库

---

# User Fields

仅允许：

- id
- username
- password_hash
- role
- enabled

不得新增字段。

---

# Role

三种角色：

- Admin — 全部权限
- Operator — 执行操作 + 查看历史
- Viewer — 只读

---

# Session 机制

Session 存储在服务端（内存或文件）。

Cookie 存储 Session ID。

Session 过期时间：24 小时。

---

# Mock User Store

默认用户：

- admin / admin123 / Admin
- operator / operator123 / Operator
- viewer / viewer123 / Viewer

全部 Mock。

不得读取真实数据库。

---

# Login Page

显示：

- Logo / 品牌名
- 用户名输入框
- 密码输入框
- 登录按钮
- 错误提示

使用 Components。

---

# Logout

清除 Session Cookie。

重定向到 Login Page。

---

# Current User 状态

登录后：

- 顶部显示当前用户名
- 显示角色标签
- 显示退出按钮

---

# Module Constraints

MOCK_USER_STORE 必须保持模块私有。

不得暴露 getUsers()。

window.AuthModule 只允许暴露：

- renderLogin
- renderUserBadge
- login
- logout
- getCurrentUser
- isLoggedIn

---

# 前端路由

未登录时：

- 只显示 Login Page
- 禁止访问其他页面

登录后：

- 正常显示所有页面
- 顶部显示用户信息

---

# i18n

所有新增文字必须使用：

WorkOps.t()

key 命名空间使用：

- auth.*
- auth.role.*

不得修改已有 key。

---

# Mobile

保持 Sprint002 响应式布局。

不得新增移动端逻辑。

---

# Existing Modules

必须保持兼容。

不得删除。

不得重构。

不得修改业务逻辑。

---

# 不要实现

以下放后续 Sprint：

- Permission Detail Matrix
- API Token
- Audit Log
- Password Reset

---

# Output

完成后输出：

1. 修改文件
2. 新增文件
3. Mock 用户数据
4. 用户测试项
5. 已知限制
6. Technical Debt

完成后立即停止。
