const state = {
  config: null,
  discovery: null,
  jobs: [],
  workflow: null,
  profile: null,
  capabilities: null,
  inventory: null,
  sshPassword: "",
  connectionResult: null,
  cloudSession: {},
  notices: [],
  activeJobs: {},
  restoreDraft: {
    snapshot: "latest",
    target: "",
    paths: [],
  },
};

let noticeCounter = 0;
const OPERATION_POLL_MS = 1500;

const CLOUD_GUIDES = [
  {
    id: "baidu-webdav-gateway",
    label: "百度网盘（WebDAV 网关）",
    provider: "baidu",
    backendType: "webdav",
    vendor: "other",
    summary:
      "适合你已经通过 AList、NAS 网关或其他中间层，把百度网盘暴露成一个 WebDAV 地址的场景。",
    warning:
      "rclone 官方当前没有百度网盘直连 backend。这里是通过 WebDAV 网关接入，不是官方百度网盘直连。",
    authType: "gateway-password",
    successCriteria: "执行远端验证后能列出网关映射的百度网盘目录，并且目标目录与 Restic 仓库目录相互独立。",
    troubleshooting: [
      {
        problem: "401 或用户名密码错误",
        fix: "检查的是 WebDAV 网关账号，不是百度网盘网页登录密码；必要时在网关内重新生成专用账号。",
      },
      {
        problem: "404 或看不到目标目录",
        fix: "确认填写的是网关 DAV 根地址，并检查网关里百度网盘挂载路径与 remote_path 是否一致。",
      },
    ],
    visual: [
      "先准备 WebDAV 网关 URL",
      "再填写用户名和密码",
      "用 rclone 创建 remote",
      "最后用 lsd 或 sync 验证",
    ],
    fields: [
      {
        key: "remote_name",
        label: "Remote 名称",
        placeholder: "baidu-alist",
        kind: "text",
        persistent: true,
      },
      {
        key: "endpoint",
        label: "WebDAV URL",
        placeholder: "https://alist.example.com/dav/",
        kind: "text",
        persistent: true,
      },
      {
        key: "username",
        label: "用户名",
        placeholder: "your-user",
        kind: "text",
        persistent: true,
      },
      {
        key: "password",
        label: "密码",
        placeholder: "仅用于当前会话",
        kind: "password",
        persistent: false,
        sensitive: true,
      },
      {
        key: "remote_path",
        label: "云端目录",
        placeholder: "backup/restic-repo",
        kind: "text",
        persistent: true,
      },
      {
        key: "verify_path",
        label: "验证路径",
        placeholder: "backup",
        kind: "text",
        persistent: true,
      },
    ],
    steps: [
      "在网关侧先确认百度网盘内容已经能通过 WebDAV 看到。",
      "把 WebDAV 根地址填入向导，而不是百度网盘网页地址。",
      "先创建 remote，再运行 rclone lsd remote: 或 remote:子目录 做验证。",
      "确认能列目录后，再把 Restic 仓库同步到目标路径。",
    ],
    sources: [
      {
        label: "Rclone WebDAV 官方文档",
        url: "https://rclone.org/webdav/",
      },
      {
        label: "Rclone config create 官方文档",
        url: "https://rclone.org/commands/rclone_config_create/",
      },
      {
        label: "Rclone 支持的存储系统列表",
        url: "https://rclone.org/commands/rclone_config/",
      },
    ],
  },
  {
    id: "generic-webdav",
    label: "通用 WebDAV",
    provider: "webdav",
    backendType: "webdav",
    vendor: "other",
    summary:
      "适合 Nextcloud、Owncloud、SharePoint、群晖 WebDAV 或其他标准 WebDAV 服务。",
    warning: "",
    authType: "service-password",
    successCriteria: "执行远端验证后能列出预期目录，并确认该账号对备份目录具备读取和写入权限。",
    troubleshooting: [
      {
        problem: "返回网页 HTML 或 404",
        fix: "当前地址多半是网页登录页；改用服务商文档给出的 WebDAV 终点路径。",
      },
      {
        problem: "能列目录但无法上传",
        fix: "检查账号对目标目录的写权限、配额和服务端文件大小限制。",
      },
    ],
    visual: [
      "准备服务端 URL",
      "确认 WebDAV 用户名密码",
      "创建 remote",
      "先 lsd 验证，再 sync",
    ],
    fields: [
      {
        key: "remote_name",
        label: "Remote 名称",
        placeholder: "company-webdav",
        kind: "text",
        persistent: true,
      },
      {
        key: "endpoint",
        label: "WebDAV URL",
        placeholder: "https://example.com/remote.php/webdav/",
        kind: "text",
        persistent: true,
      },
      {
        key: "username",
        label: "用户名",
        placeholder: "webdav-user",
        kind: "text",
        persistent: true,
      },
      {
        key: "password",
        label: "密码",
        placeholder: "仅用于当前会话",
        kind: "password",
        persistent: false,
        sensitive: true,
      },
      {
        key: "remote_path",
        label: "云端目录",
        placeholder: "backup/restic-repo",
        kind: "text",
        persistent: true,
      },
      {
        key: "verify_path",
        label: "验证路径",
        placeholder: "",
        kind: "text",
        persistent: true,
      },
    ],
    steps: [
      "先确认这个地址真的是 WebDAV 终点，而不是网页登录页。",
      "如果服务商有 vendor 选项，优先在服务商文档里查标准 WebDAV 路径。",
      "创建 remote 后先运行 lsd，能列出目录再继续同步。",
      "第一次正式同步前，建议先把 remote_path 指向一个测试目录。",
    ],
    sources: [
      {
        label: "Rclone WebDAV 官方文档",
        url: "https://rclone.org/webdav/",
      },
      {
        label: "Rclone config create 官方文档",
        url: "https://rclone.org/commands/rclone_config_create/",
      },
    ],
  },
  {
    id: "microsoft-onedrive",
    label: "Microsoft OneDrive",
    provider: "onedrive",
    backendType: "onedrive",
    vendor: "",
    authType: "oauth",
    summary:
      "适合 Microsoft 个人账号、Microsoft 365 工作或学校账号。通过浏览器 OAuth 授权，不在本应用里填写微软账号密码。",
    warning:
      "请只在 Microsoft 官方授权页面登录。远程 OMV 没有浏览器时，可在有浏览器的电脑运行 rclone config 完成授权，再把生成的 remote 配置安全地部署到 OMV。",
    successCriteria: "rclone config 已创建 OneDrive remote，远端验证能列出所选 Drive 内的目标目录。",
    troubleshooting: [
      {
        problem: "OMV 上无法打开授权浏览器",
        fix: "在有浏览器的电脑完成 rclone config，再把生成的 remote 配置安全复制到实际执行同步的系统。",
      },
      {
        problem: "授权成功但列错了盘",
        fix: "重新运行 rclone config，核对个人盘、工作或学校账号以及 SharePoint/Drive 的选择。",
      },
    ],
    visual: [
      "运行 rclone config",
      "选择 Microsoft OneDrive",
      "在官方页面完成 OAuth",
      "返回本页验证并同步",
    ],
    fields: [
      {
        key: "remote_name",
        label: "Remote 名称",
        placeholder: "onedrive-backup",
        kind: "text",
        persistent: true,
      },
      {
        key: "remote_path",
        label: "云端目录",
        placeholder: "NAS-Backup/restic-repo",
        kind: "text",
        persistent: true,
      },
      {
        key: "verify_path",
        label: "验证路径",
        placeholder: "NAS-Backup",
        kind: "text",
        persistent: true,
      },
    ],
    steps: [
      "在实际运行 rclone 的系统上执行 rclone config，并新建一个 remote。",
      "Storage 选择 Microsoft OneDrive，然后按提示在 Microsoft 官方页面授权；不要把微软登录密码填入本应用。",
      "配置完成后，把本页 Remote 名称改成刚创建的名称，再执行远端验证。",
      "能列出目标目录后，再同步加密后的 Restic 仓库；恢复时先拉回仓库，再由 Restic 恢复文件。",
    ],
    sources: [
      {
        label: "Rclone OneDrive 官方文档",
        url: "https://rclone.org/onedrive/",
      },
      {
        label: "Rclone config 官方文档",
        url: "https://rclone.org/commands/rclone_config/",
      },
    ],
  },
  {
    id: "google-drive",
    label: "Google Drive",
    provider: "drive",
    backendType: "drive",
    vendor: "",
    authType: "oauth",
    summary:
      "适合 Google Drive。通过 Google 官方 OAuth 页面授权，不在本应用里填写 Google 账号密码。",
    warning:
      "远程 OMV 没有浏览器时，可在有浏览器的电脑运行 rclone config 完成授权，再把生成的 remote 配置安全地部署到 OMV。不要在第三方页面输入 Google 密码。",
    successCriteria: "rclone config 已创建 Google Drive remote，远端验证能列出目标文件夹。",
    troubleshooting: [
      {
        problem: "OMV 上无法完成浏览器授权",
        fix: "在有浏览器的电脑完成 rclone config，再把生成的 remote 配置安全复制到实际执行同步的系统。",
      },
      {
        problem: "授权后看不到共享云端硬盘",
        fix: "重新配置 remote，并核对是否选中了正确账号、共享云端硬盘或根目录。",
      },
    ],
    visual: [
      "运行 rclone config",
      "选择 Google Drive",
      "在官方页面完成 OAuth",
      "返回本页验证并同步",
    ],
    fields: [
      {
        key: "remote_name",
        label: "Remote 名称",
        placeholder: "google-backup",
        kind: "text",
        persistent: true,
      },
      {
        key: "remote_path",
        label: "云端目录",
        placeholder: "NAS-Backup/restic-repo",
        kind: "text",
        persistent: true,
      },
      {
        key: "verify_path",
        label: "验证路径",
        placeholder: "NAS-Backup",
        kind: "text",
        persistent: true,
      },
    ],
    steps: [
      "在实际运行 rclone 的系统上执行 rclone config，并新建一个 remote。",
      "Storage 选择 Google Drive，然后按提示在 Google 官方页面授权；不要把 Google 登录密码填入本应用。",
      "配置完成后，把本页 Remote 名称改成刚创建的名称，再执行远端验证。",
      "验证通过后再同步加密后的 Restic 仓库；需要恢复时使用本页拉回功能取得仓库副本。",
    ],
    sources: [
      {
        label: "Rclone Google Drive 官方文档",
        url: "https://rclone.org/drive/",
      },
      {
        label: "Rclone config 官方文档",
        url: "https://rclone.org/commands/rclone_config/",
      },
    ],
  },
  {
    id: "aws-s3",
    label: "AWS S3",
    provider: "s3",
    backendType: "s3",
    vendor: "AWS",
    summary:
      "适合标准 AWS S3。配置时重点是 remote、region、Access Key、Secret Key，以及桶路径。",
    warning: "",
    authType: "access-key",
    successCriteria: "远端验证能列出指定 bucket，并且专用 IAM 凭据只拥有备份所需的最小权限。",
    troubleshooting: [
      {
        problem: "AccessDenied",
        fix: "检查 IAM 策略是否允许列出 bucket 和读写目标前缀，并确认 Access Key 仍然有效。",
      },
      {
        problem: "重定向或 region 错误",
        fix: "核对 bucket 所在 region，确保向导里的 region 与实际区域一致。",
      },
    ],
    visual: [
      "准备 AK / SK 和 region",
      "创建 S3 remote",
      "先 lsd remote:bucket 验证",
      "再把 Restic 仓库同步到 bucket/path",
    ],
    fields: [
      {
        key: "remote_name",
        label: "Remote 名称",
        placeholder: "aws-backup",
        kind: "text",
        persistent: true,
      },
      {
        key: "region",
        label: "Region",
        placeholder: "ap-east-1",
        kind: "text",
        persistent: true,
      },
      {
        key: "access_key_id",
        label: "Access Key ID",
        placeholder: "仅用于当前会话",
        kind: "password",
        persistent: false,
        sensitive: true,
      },
      {
        key: "secret_access_key",
        label: "Secret Access Key",
        placeholder: "仅用于当前会话",
        kind: "password",
        persistent: false,
        sensitive: true,
      },
      {
        key: "remote_path",
        label: "桶与目录",
        placeholder: "my-bucket/restic-repo",
        kind: "text",
        persistent: true,
      },
      {
        key: "verify_path",
        label: "验证路径",
        placeholder: "my-bucket",
        kind: "text",
        persistent: true,
      },
    ],
    steps: [
      "先在 AWS 或 IAM 侧准备只用于备份的 Access Key 和 Secret Key。",
      "remote_path 里要包含 bucket 名，比如 my-bucket/restic-repo。",
      "先用 lsd 验证 bucket 可访问，再正式同步。",
      "如果只想读写某个桶，建议把权限限制在该桶范围内。",
    ],
    sources: [
      {
        label: "Rclone S3 官方文档",
        url: "https://rclone.org/s3/",
      },
      {
        label: "Rclone config create 官方文档",
        url: "https://rclone.org/commands/rclone_config_create/",
      },
    ],
  },
  {
    id: "alibaba-oss",
    label: "阿里云 OSS",
    provider: "s3",
    backendType: "s3",
    vendor: "Alibaba",
    summary:
      "阿里云 OSS 通过 rclone 的 S3 兼容配置接入，provider 应设置为 Alibaba。",
    warning: "",
    authType: "access-key",
    successCriteria: "远端验证能列出指定 OSS Bucket，并确认 RAM 用户权限只覆盖备份所需目录。",
    troubleshooting: [
      {
        problem: "SignatureDoesNotMatch",
        fix: "重新核对 AccessKey、Secret、Region 与 Endpoint，避免混用内网和公网 Endpoint。",
      },
      {
        problem: "AccessDenied",
        fix: "检查 RAM 用户或 Bucket Policy 是否允许列目录并读写目标前缀。",
      },
    ],
    visual: [
      "准备 OSS AccessKey 和 Endpoint 信息",
      "用 provider=Alibaba 创建 remote",
      "先 lsd 验证桶访问",
      "再同步到 bucket/path",
    ],
    fields: [
      {
        key: "remote_name",
        label: "Remote 名称",
        placeholder: "aliyun-oss",
        kind: "text",
        persistent: true,
      },
      {
        key: "region",
        label: "Region",
        placeholder: "cn-hangzhou",
        kind: "text",
        persistent: true,
      },
      {
        key: "endpoint",
        label: "Endpoint（可选）",
        placeholder: "oss-cn-hangzhou.aliyuncs.com",
        kind: "text",
        persistent: true,
      },
      {
        key: "access_key_id",
        label: "Access Key ID",
        placeholder: "仅用于当前会话",
        kind: "password",
        persistent: false,
        sensitive: true,
      },
      {
        key: "secret_access_key",
        label: "Access Key Secret",
        placeholder: "仅用于当前会话",
        kind: "password",
        persistent: false,
        sensitive: true,
      },
      {
        key: "remote_path",
        label: "桶与目录",
        placeholder: "my-bucket/restic-repo",
        kind: "text",
        persistent: true,
      },
      {
        key: "verify_path",
        label: "验证路径",
        placeholder: "my-bucket",
        kind: "text",
        persistent: true,
      },
    ],
    steps: [
      "provider 需要选 Alibaba，不要误用 AWS。",
      "如果服务商文档给了标准 endpoint，可以一并填入；没有时通常可留空由 provider 处理。",
      "先列桶，再正式同步。",
      "第一次建议先同步到测试目录，确认速度和权限都正常。",
    ],
    sources: [
      {
        label: "Rclone S3 官方文档",
        url: "https://rclone.org/s3/",
      },
      {
        label: "Rclone config create 官方文档",
        url: "https://rclone.org/commands/rclone_config_create/",
      },
    ],
  },
  {
    id: "baidu-s3-gateway",
    label: "百度网盘（S3 网关）",
    provider: "baidu",
    backendType: "s3",
    vendor: "Other",
    summary:
      "适合你已经有能把百度网盘暴露成 S3-compatible 的网关，例如某些 AList 或中间层方案。",
    warning:
      "rclone 官方当前没有百度网盘直连 backend。这里是通过 S3 兼容网关接入，不是官方百度网盘直连。",
    authType: "gateway-access-key",
    successCriteria: "远端验证能通过网关列出目标 bucket 或目录，并确认 endpoint 指向 S3 接口而不是网页或 WebDAV。",
    troubleshooting: [
      {
        problem: "连接被拒绝或 endpoint 无效",
        fix: "确认网关已启用 S3-compatible 服务、端口可达，并使用网关提供的完整 Endpoint。",
      },
      {
        problem: "签名错误或无法列目录",
        fix: "核对网关生成的 AK/SK、Region 和路径风格设置；这些凭据不是百度网盘登录凭据。",
      },
    ],
    visual: [
      "准备 S3 兼容 endpoint",
      "填写会话级 Access Key / Secret",
      "先验证 bucket 或顶层目录",
      "再同步 Restic 仓库",
    ],
    fields: [
      {
        key: "remote_name",
        label: "Remote 名称",
        placeholder: "baidu-s3",
        kind: "text",
        persistent: true,
      },
      {
        key: "endpoint",
        label: "S3 Endpoint",
        placeholder: "https://alist.example.com",
        kind: "text",
        persistent: true,
      },
      {
        key: "region",
        label: "Region（可留空）",
        placeholder: "us-east-1",
        kind: "text",
        persistent: true,
      },
      {
        key: "access_key_id",
        label: "Access Key ID",
        placeholder: "仅用于当前会话",
        kind: "password",
        persistent: false,
        sensitive: true,
      },
      {
        key: "secret_access_key",
        label: "Secret Access Key",
        placeholder: "仅用于当前会话",
        kind: "password",
        persistent: false,
        sensitive: true,
      },
      {
        key: "remote_path",
        label: "桶与目录",
        placeholder: "backup/restic-repo",
        kind: "text",
        persistent: true,
      },
      {
        key: "verify_path",
        label: "验证路径",
        placeholder: "backup",
        kind: "text",
        persistent: true,
      },
    ],
    steps: [
      "先确认你的网关确实提供 S3-compatible 接口，而不是 WebDAV。",
      "endpoint 填网关提供的 S3 地址，不要填百度网页地址。",
      "先创建 remote，再用 lsd 试列目录或 bucket。",
      "确认可读写后，再让 Restic 仓库做云端副本。",
    ],
    sources: [
      {
        label: "Rclone S3 官方文档",
        url: "https://rclone.org/s3/",
      },
      {
        label: "Rclone config create 官方文档",
        url: "https://rclone.org/commands/rclone_config_create/",
      },
      {
        label: "Rclone 支持的存储系统列表",
        url: "https://rclone.org/commands/rclone_config/",
      },
    ],
  },
];

const CLOUD_SESSION_ONLY_KEYS = [
  "password",
  "pass",
  "secret_access_key",
  "access_key_id",
  "bearer_token",
  "session_token",
  "api_key",
  "client_id",
  "client_secret",
  "refresh_token",
];

const CLOUD_PERSISTED_KEYS = [
  "enabled",
  "provider",
  "remote_name",
  "remote_path",
  "sync_source",
  "backend_type",
  "vendor",
  "endpoint",
  "region",
  "bucket",
  "username",
  "verify_path",
  "guide_id",
  "guide_url",
  "verified_at",
  "notes",
];

const CLOUD_VERIFICATION_FIELDS = [
  "provider",
  "backend_type",
  "vendor",
  "remote_name",
  "remote_path",
  "endpoint",
  "region",
  "bucket",
  "username",
  "verify_path",
];

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

document.querySelectorAll(".nav").forEach((button) => {
  button.addEventListener("click", () => showPage(button.dataset.page));
});

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok && payload.error !== "confirmation_required") {
    const detail = typeof payload.error === "object" ? payload.error : null;
    const error = new Error(
      detail?.message || payload.error || payload.message || response.statusText
    );
    error.details = detail;
    throw error;
  }
  return payload;
}

async function init() {
  // 渲染语言切换器
  renderLangSwitcherUI();
  // 注册语言切换回调
  WorkOps.onLangChange(function () {
    renderLangSwitcherUI();
    updateStaticI18n();
    render();
  });
  // 应用静态 i18n
  updateStaticI18n();

  const payload = await api("/api/state");
  syncState(payload);
  if (!state.discovery && state.inventory?.storage) {
    state.discovery = normalizeInventoryStorage(state.inventory.storage);
  }
  await loadDevices();
  render();
}

function renderLangSwitcherUI() {
  var el = document.getElementById("langSwitcher");
  if (el) el.innerHTML = WorkOps.renderLangSwitcher();
}

function updateStaticI18n() {
  // 更新导航按钮文字（只更新纯文本节点，保护子元素）
  document.querySelectorAll("[data-i18n]").forEach(function (el) {
    var key = el.getAttribute("data-i18n");
    if (!key) return;
    // 跳过含有子元素的节点（如 <label> 内嵌 <input>）
    if (el.children.length > 0) return;
    el.textContent = WorkOps.t(key);
  });
  // 更新 placeholder
  document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
    var key = el.getAttribute("data-i18n-placeholder");
    if (key) el.placeholder = WorkOps.t(key);
  });
  // 更新页面标题
  document.title = WorkOps.t("brand.name");
}

function syncState(payload) {
  if (payload.config) state.config = payload.config;
  if (Array.isArray(payload.jobs)) state.jobs = payload.jobs;
  if (payload.workflow) state.workflow = payload.workflow;
  if (payload.profile) state.profile = payload.profile;
  if (payload.capabilities) state.capabilities = payload.capabilities;
  if (payload.inventory) {
    state.inventory = payload.inventory;
    state.discovery = normalizeInventoryStorage(payload.inventory.storage || {});
  } else if (looksLikeDiscoveryPayload(payload)) {
    state.discovery = normalizeInventoryStorage(payload);
  }
}

function looksLikeDiscoveryPayload(payload) {
  return Boolean(
    payload &&
      (Array.isArray(payload.pools) ||
        Array.isArray(payload.datasets) ||
        Array.isArray(payload.folders) ||
        Array.isArray(payload.storage_candidates) ||
        Array.isArray(payload.restore_root_candidates))
  );
}

function normalizeInventoryStorage(storage = {}) {
  return {
    pools: storage.pools || [],
    datasets: storage.datasets || [],
    mounts: storage.mounts || [],
    folders: storage.folders || [],
    storage_candidates: storage.storage_candidates || [],
    restore_root_candidates: storage.restore_root_candidates || [],
    restore_stage_entries: storage.restore_stage_entries || [],
    windows_drives: storage.windows_drives || [],
    schedules: storage.schedules || [],
    restic_snapshots: storage.restic_snapshots || [],
    pbs_backups: storage.pbs_backups || [],
    errors: storage.errors || [],
  };
}

function render() {
  if (!state.config) return;
  if (window.WorkspaceModule) WorkspaceModule.renderWorkspace();
  renderDevices();
  renderOverview();
  renderStorage();
  renderRestore();
  renderNas();
  renderMigration();
  renderWindows();
  renderCloud();
  renderPve();
  renderJobs();
  renderOperationStatusRegion();
}

function notify(tone, title, detail = "", timeoutMs = 0) {
  const notice = {
    id: `notice-${Date.now()}-${++noticeCounter}`,
    tone,
    title,
    detail,
  };
  state.notices = [notice, ...(state.notices || [])].slice(0, 5);
  renderOperationStatusRegion();
  if (timeoutMs > 0) {
    setTimeout(() => dismissNotice(notice.id), timeoutMs);
  }
  return notice.id;
}

function dismissNotice(id) {
  state.notices = (state.notices || []).filter((notice) => notice.id !== id);
  renderOperationStatusRegion();
}

function trackActiveJob(job) {
  if (!job?.id) return;
  state.activeJobs = {
    ...(state.activeJobs || {}),
    [job.id]: {
      ...job,
      last_seen_at: new Date().toISOString(),
    },
  };
  renderOperationStatusRegion();
}

function clearActiveJob(jobId) {
  if (!jobId || !state.activeJobs?.[jobId]) return;
  const next = { ...state.activeJobs };
  delete next[jobId];
  state.activeJobs = next;
  renderOperationStatusRegion();
}

function extractOperationProgress(job) {
  const metadataPercent = Number(job?.metadata?.progress?.percent);
  if (Number.isFinite(metadataPercent)) {
    return {
      percent: clampPercent(metadataPercent),
      label: `${clampPercent(metadataPercent)}%`,
      detail: job?.metadata?.progress?.detail || "命令已返回进度。",
      indeterminate: false,
    };
  }

  const output = [job?.stdout, job?.stderr].filter(Boolean).join("\n");
  const matches = Array.from(output.matchAll(/(^|[^\d])(\d{1,3}(?:\.\d+)?)%/g));
  const numericMatches = matches
    .map((match) => Number(match[2]))
    .filter((value) => Number.isFinite(value) && value >= 0 && value <= 100);
  if (numericMatches.length) {
    const percent = clampPercent(numericMatches[numericMatches.length - 1]);
    return {
      percent,
      label: `${percent}%`,
      detail: "从命令输出中读取到进度。",
      indeterminate: false,
    };
  }

  if (job?.status === "success") {
    return {
      percent: 100,
      label: "100%",
      detail: "命令已完成。",
      indeterminate: false,
    };
  }

  return {
    percent: null,
    label: "执行中",
    detail: "命令暂未返回可解析的百分比，正在等待输出。",
    indeterminate: job?.status === "running",
  };
}

function clampPercent(value) {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function formatJobDuration(job) {
  const started = Date.parse(job?.started_at || "");
  if (!Number.isFinite(started)) return "时间未知";
  const finished = Date.parse(job?.finished_at || "");
  const end = Number.isFinite(finished) ? finished : Date.now();
  const seconds = Math.max(0, Math.floor((end - started) / 1000));
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${minutes}分${String(rest).padStart(2, "0")}秒`;
}

function renderOperationStatusRegion() {
  const region = $("#operationStatusRegion");
  if (!region) return;
  const notices = state.notices || [];
  const activeJobs = Object.values(state.activeJobs || {});
  if (!notices.length && !activeJobs.length) {
    region.innerHTML = "";
    return;
  }
  region.innerHTML = `
    ${activeJobs.map(renderActiveJobCard).join("")}
    ${notices.map(renderNoticeCard).join("")}
  `;
}

function renderNoticeCard(notice) {
  return `
    <article class="operation-notice ${escapeAttr(notice.tone || "info")}">
      <div>
        <strong>${escapeHtml(notice.title || "状态更新")}</strong>
        ${notice.detail ? `<p>${escapeHtml(notice.detail)}</p>` : ""}
      </div>
      <button class="secondary compact" onclick="dismissNotice('${escapeAttr(
        notice.id
      )}')">关闭</button>
    </article>
  `;
}

function renderActiveJobCard(job) {
  const progress = extractOperationProgress(job);
  const width = progress.percent === null ? 100 : progress.percent;
  const progressClass = progress.indeterminate ? " indeterminate" : "";
  return `
    <article class="operation-job-card">
      <div class="operation-job-head">
        <div>
          <strong>${escapeHtml(job.title || job.operation_id || "正在执行")}</strong>
          <p>${escapeHtml(job.status || "running")} · 已用时 ${escapeHtml(
            formatJobDuration(job)
          )}</p>
        </div>
        <span class="pill">${escapeHtml(progress.label)}</span>
      </div>
      <div class="operation-progress${progressClass}" role="progressbar" ${
        progress.percent === null
          ? 'aria-valuetext="running"'
          : `aria-valuenow="${escapeAttr(String(progress.percent))}" aria-valuemin="0" aria-valuemax="100"`
      }>
        <span style="width: ${escapeAttr(String(width))}%"></span>
      </div>
      <p class="muted">${escapeHtml(progress.detail)}</p>
    </article>
  `;
}

function renderOverview() {
  const profile = state.profile || { label: "Unknown Host", kind: "unknown" };
  const tasks = state.inventory?.backup_tasks || [];
  const warnings = state.inventory?.warnings || [];
  const artifacts = state.inventory?.backup_artifacts || [];
  const restoreCenter = state.inventory?.restore_center || {
    app_managed: [],
    external: [],
  };
  const capabilityBadges = Object.entries(state.capabilities || {})
    .filter(([, enabled]) => enabled)
    .map(([name]) => `<span class="capability-badge">${escapeHtml(name)}</span>`)
    .join("");

  $("#overview").innerHTML = `
    ${BackupWorkflow.renderOverview(state.workflow)}
    <section class="summary-band grid" aria-label="${WorkOps.t("overview.capabilities")}">
      <div class="metric">${WorkOps.t("overview.currentHost")}<strong>${escapeHtml(profile.label || profile.kind)}</strong></div>
      <div class="metric">${WorkOps.t("overview.execMode")}<strong>${escapeHtml(state.config.executor_mode || "mock")}</strong></div>
      <div class="metric">${WorkOps.t("overview.activeStorage")}<strong>${escapeHtml(activeStorage()?.name || WorkOps.t("overview.notConfigured"))}</strong></div>
      <div class="metric">${WorkOps.t("overview.restoreRoot")}<strong>${escapeHtml(activeRestoreRoot()?.path || WorkOps.t("overview.notConfigured"))}</strong></div>
      <div class="metric">${WorkOps.t("overview.resticRepo")}<strong>${escapeHtml(state.config.restic?.repository || WorkOps.t("overview.notConfigured"))}</strong></div>
      <div class="metric">${WorkOps.t("overview.discoveredArtifacts")}<strong>${escapeHtml(String(artifacts.length))}</strong></div>
    </section>
    <section class="band">
      <h3>${WorkOps.t("overview.capabilities")}</h3>
      <div class="badge-row">${capabilityBadges || `<span class="muted">${WorkOps.t("overview.noCapabilities")}</span>`}</div>
    </section>
    <section class="band">
      <h3>${WorkOps.t("overview.discoveredTasks")}</h3>
      ${renderBackupTaskTable(tasks)}
    </section>
    <section class="band">
      <h3>${WorkOps.t("overview.discoveredArtifactsTitle")}</h3>
      ${renderArtifactOverview()}
    </section>
    <section class="band">
      <h3>${WorkOps.t("overview.restoreStaging")}</h3>
      <div class="grid">
        <div class="metric">${WorkOps.t("overview.appManaged")}<strong>${escapeHtml(String(restoreCenter.app_managed.length))}</strong></div>
        <div class="metric">${WorkOps.t("overview.external")}<strong>${escapeHtml(String(restoreCenter.external.length))}</strong></div>
      </div>
    </section>
    <section class="band">
      <h3>${WorkOps.t("overview.warnings")}</h3>
      ${
        warnings.length
          ? warnings
              .map(
                (item) =>
                  `<p class="warning-line"><strong>${escapeHtml(item.code)}</strong> ${escapeHtml(item.message || "")}</p>`
              )
              .join("")
          : `<p class="muted">${WorkOps.t("overview.noWarnings")}</p>`
      }
    </section>
  `;
}

function renderStorage() {
  const config = state.config;
  const targets = config.storage_targets || [];
  const stepId = currentStorageStepId();

  $("#storage").innerHTML = `
    ${BackupWorkflow.renderStepHeader(
      stepId,
      state.workflow,
      WorkOps.t("storage.stepDesc"),
      [
        WorkOps.t("storage.preCheck1"),
        WorkOps.t("storage.preCheck2"),
        WorkOps.t("storage.preCheck3")
      ]
    )}
    <div class="band">
      <h3>${WorkOps.t("storage.connSettings")}</h3>
      <div class="grid">
        <div>
          <label>${WorkOps.t("storage.execMode")}</label>
          <select id="executorMode">
            ${option("mock", "mock 演示", config.executor_mode)}
            ${option("local", "local 本机执行", config.executor_mode)}
            ${option("ssh", "ssh 远程执行", config.executor_mode)}
          </select>
          ${BackupWorkflow.renderFieldHelp({
            purpose: "决定命令在哪台系统上执行。",
            example: "ssh 远程执行",
            format: "管理 OMV / PVE 通常选择 ssh。",
          })}
        </div>
        <div>
          <label>SSH Host</label>
          <input id="sshHost" value="${escapeAttr(config.ssh_host || "")}" placeholder="10.0.0.10">
          ${BackupWorkflow.renderFieldHelp({
            purpose: "要管理的 Linux / OMV / PVE 主机地址。",
            example: "10.0.0.10",
            format: "可以是 IP、DNS 名称，或 SSH config 里的 Host 别名。",
          })}
        </div>
        <div>
          <label>SSH User</label>
          <input id="sshUser" value="${escapeAttr(config.ssh_user || "root")}">
          ${BackupWorkflow.renderFieldHelp({
            purpose: "远程登录账户。",
            example: "root",
            safety: "优先使用已经验证可以登录的账户。",
          })}
        </div>
        <div>
          <label>SSH Port</label>
          <input id="sshPort" type="number" min="1" max="65535" value="${escapeAttr(config.ssh_port || 22)}">
          ${BackupWorkflow.renderFieldHelp({
            purpose: "SSH 端口。",
            example: "22",
            format: "填写 1 到 65535 的整数。",
          })}
        </div>
        <div>
          <label>SSH 认证方式</label>
          <select id="sshAuthMode" onchange="renderSshAuthFields()">
            ${option("ssh_config", "已有 SSH 配置 / Agent", config.ssh_auth_mode || "ssh_config")}
            ${option("private_key", "SSH 私钥", config.ssh_auth_mode)}
            ${option("password", "SSH 密码", config.ssh_auth_mode)}
          </select>
          ${BackupWorkflow.renderFieldHelp({
            purpose: "使用目标系统原本的登录方式。",
            example: "SSH 密码",
            safety: "密码只保存在当前页面内存中，不会写入配置文件。",
          })}
        </div>
      </div>
      <div id="sshAuthFields">${sshAuthFields(config.ssh_auth_mode || "ssh_config")}</div>
      <div id="sshConnectionResult" role="status">${connectionResultHtml()}</div>
      <div class="actions">
        <button onclick="saveRuntimeConfig()">${WorkOps.t("btn.saveConn")}</button>
        <button class="secondary" onclick="testSshConnection()">${WorkOps.t("btn.testSsh")}</button>
        <button class="secondary" onclick="discover()">${WorkOps.t("btn.discover")}</button>
      </div>
    </div>
    <div class="card">
      <h3>${WorkOps.t("storage.profileResult")}</h3>
      ${renderProfileSummary()}
    </div>
    <div class="card">
      <h3>${WorkOps.t("storage.activeStorageTarget")}</h3>
      ${
        targets.length
          ? table(
              [WorkOps.t("storage.name"), WorkOps.t("storage.type"), "Pool", WorkOps.t("storage.mountpoint")],
              targets.map((target) => [
                target.name,
                target.kind,
                target.pool_name || "-",
                target.mountpoint,
              ])
            )
          : `<p class="muted">${WorkOps.t("storage.noStorage")}</p>`
      }
      <div class="grid">
        <div>
          <label>${WorkOps.t("storage.name")}</label>
          <input id="storageName" placeholder="NAS 数据池">
        </div>
        <div>
          <label>${WorkOps.t("storage.type")}</label>
          <select id="storageKind">
            <option value="zfs">zfs</option>
            <option value="local">local</option>
            <option value="smb">smb</option>
            <option value="other">other</option>
          </select>
        </div>
        <div>
          <label>${WorkOps.t("storage.poolName")}</label>
          <input id="storagePool" placeholder="${WorkOps.getLang() === 'en' ? 'Optional' : '可留空'}">
        </div>
        <div>
          <label>${WorkOps.t("storage.mountpoint")}</label>
          <input id="storageMount" placeholder="/Gensol">
        </div>
      </div>
      <p id="storageSuggestion" class="field-help" role="status"></p>
      <div class="actions">
        <button onclick="addStorageTarget()">${WorkOps.t("btn.add")}</button>
      </div>
    </div>
    <div class="card">
      <h3>${WorkOps.t("storage.discoveryResult")}</h3>
      <div id="discoverResult">${renderDiscovery()}</div>
    </div>
    ${BackupWorkflow.renderStepFooter(stepId, state.workflow)}
  `;

  queueMicrotask(() => {
    applyAutomaticStorageSuggestion();
  });
}

function renderRestore() {
  const restoreRoot = activeRestoreRoot();
  const restoreCenter = state.inventory?.restore_center || {
    app_managed: [],
    external: [],
  };
  const restoreTarget = state.restoreDraft.target || defaultRestoreTarget();
  const restorePaths = (state.restoreDraft.paths || []).join("\n");

  $("#restore").innerHTML = `
    ${BackupWorkflow.renderStepHeader(
      "restore_root",
      state.workflow,
      "先准备一个足够大的恢复暂存位置，后续所有恢复都先落到这里，而不是 /tmp 或系统盘。",
      [
        "优先选择数据池上的独立 ZFS dataset",
        "恢复暂存目录不要再纳入自身备份来源",
        "恢复目标必须有足够空间"
      ]
    )}
    <div class="band">
      <h3>恢复暂存根目录</h3>
      ${
        restoreRoot
          ? `<p class="muted">当前活动恢复根目录：<code>${escapeHtml(restoreRoot.path)}</code></p>`
          : `<p class="muted">当前还没有活动恢复根目录。</p>`
      }
      <div class="grid">
        <div>
          <label>标签</label>
          <input id="restoreRootLabel" value="${escapeAttr(restoreRoot?.label || "")}" placeholder="Primary Restore Root">
        </div>
        <div>
          <label>路径</label>
          <input id="restoreRootPath" value="${escapeAttr(restoreRoot?.path || "")}" placeholder="/Gensol/.backup-manager/restore">
        </div>
        <div>
          <label>类型</label>
          <select id="restoreRootKind">
            ${option("zfs_dataset", "zfs_dataset", restoreRoot?.kind || "zfs_dataset")}
            ${option("directory", "directory", restoreRoot?.kind || "zfs_dataset")}
          </select>
        </div>
      </div>
      <p id="restoreRootSuggestion" class="field-help" role="status"></p>
      <div class="actions">
        <button onclick="saveRestoreRoot()">保存恢复根目录</button>
        <button class="secondary" onclick="discover()">刷新候选项</button>
      </div>
      ${renderRestoreRootCandidates()}
    </div>
    ${BackupWorkflow.renderStepFooter("restore_root", state.workflow)}
    ${BackupWorkflow.renderStepHeader(
      "restore_center",
      state.workflow,
      "恢复时先恢复到暂存区，核对无误后再复制到正式目录。暂存目录不会自动删除。",
      [
        "不要恢复到 /tmp",
        "尽量先恢复一小部分重要目录做验证",
        "核对完成后再决定覆盖原目录或删除暂存"
      ]
    )}
    <div class="card">
      <h3>执行恢复</h3>
      <div class="grid">
        <div>
          <label>Snapshot</label>
          <input id="restoreSnapshot" value="${escapeAttr(state.restoreDraft.snapshot || "latest")}">
        </div>
        <div>
          <label>恢复目标</label>
          <input id="restoreTarget" value="${escapeAttr(restoreTarget)}" placeholder="/Gensol/.backup-manager/restore/restore-001">
        </div>
      </div>
      <label>只恢复指定路径，每行一个</label>
      <textarea id="restorePaths">${escapeHtml(restorePaths)}</textarea>
      ${BackupWorkflow.renderFieldHelp({
        purpose: "用于只恢复某几个目录。留空表示恢复整个快照。",
        example: "/Gensol/财务\n/Gensol/共享网盘",
        format: "每行一个绝对 Linux 路径。",
        safety: "恢复目标必须是大容量数据盘路径，不要使用 /tmp。",
      })}
      <div class="actions">
        <button class="danger" onclick="runOperation('restic-restore', restorePayload())">开始恢复</button>
      </div>
    </div>
    <div class="card">
      <h3>应用托管的暂存目录</h3>
      ${renderStagingTable(restoreCenter.app_managed, true)}
    </div>
    <div class="card">
      <h3>外部目录</h3>
      ${renderStagingTable(restoreCenter.external, false)}
    </div>
    ${BackupWorkflow.renderStepFooter("restore_center", state.workflow)}
  `;

  queueMicrotask(() => {
    applyAutomaticRestoreRootSuggestion();
  });
}

function renderNas() {
  const restic = state.config.restic || {};
  const backupSet = state.config.backup_sets?.[0] || {
    include_paths: [],
    exclude_patterns: [],
    tag: "important",
  };
  const stepId = currentNasStepId();

  $("#nas").innerHTML = `
    ${BackupWorkflow.renderStepHeader(
      stepId,
      state.workflow,
      "在这里配置 Restic 仓库、备份目录、排除规则，并查看已经发现的快照。",
      [
        "先确认活动存储目标已经选好",
        "如果要做 dataset 迁移，先迁移再做第一次备份",
        "第一次成功备份后，回到恢复中心做一次恢复验证"
      ]
    )}
    <div class="band">
      <h3>Restic 仓库</h3>
      <div class="grid">
        <div>
          <label>Repository</label>
          <input id="resticRepo" value="${escapeAttr(restic.repository || "")}" placeholder="/Gensol/_cloud_restic/restic-repo">
        </div>
        <div>
          <label>Password File</label>
          <input id="resticPassword" value="${escapeAttr(restic.password_file || "")}" placeholder="/root/.config/restic/repo.pass">
        </div>
      </div>
      ${BackupWorkflow.renderFieldHelp({
        purpose: "Repository 是 Restic 仓库目录，Password File 是仓库密码文件。",
        example: "/Gensol/_cloud_restic/restic-repo",
        safety: "不要把密码直接写在页面里，优先使用密码文件。",
      })}
      <div class="actions">
        <button onclick="saveRestic()">保存 Restic 配置</button>
      </div>
    </div>
    <div class="card">
      <h3>需要备份的目录</h3>
      <textarea id="includePaths">${escapeHtml((backupSet.include_paths || []).join("\n"))}</textarea>
      ${BackupWorkflow.renderFieldHelp({
        purpose: "这里只填写真正要保护的目录。",
        example: "/Gensol/财务\n/Gensol/共享网盘",
        format: "每行一个绝对 Linux 路径；路径里有中文或空格时不需要手动加引号。",
      })}
      <label>排除规则，每行一个</label>
      <textarea id="excludePatterns">${escapeHtml((backupSet.exclude_patterns || []).join("\n"))}</textarea>
      ${BackupWorkflow.renderFieldHelp({
        purpose: "排除缓存、临时文件或无需备份的内容。",
        example: "*.tmp\n**/cache/**",
        format: "每行一个 Restic exclude 规则。",
      })}
      <div class="actions">
        <button onclick="saveBackupSet()">保存备份集</button>
        <button class="secondary" onclick="runOperation('restic-snapshots', resticPayload())">查看快照</button>
        <button onclick="runOperation('restic-backup', resticBackupPayload())">执行备份</button>
        <button class="secondary" onclick="runOperation('restic-check', resticPayload())">检查仓库</button>
        <button class="danger" onclick="runOperation('restic-prune', prunePayload())">按策略清理</button>
      </div>
    </div>
    <div class="card">
      <h3>已发现的 Restic 快照</h3>
      ${renderResticSnapshotTable()}
    </div>
    <div class="card">
      <h3>计划与通知</h3>
      ${renderScheduleTable()}
      <div class="grid top-gap">
        <div>
          <label>通知邮箱，每行一个</label>
          <textarea id="notificationEmails">${escapeHtml((state.config.notification_emails || []).join("\n"))}</textarea>
        </div>
        <div>
          <label>发送人标识</label>
          <input id="notificationSender" value="${escapeAttr(state.config.notification_sender || "")}" placeholder="backup-manager@example.local">
        </div>
      </div>
      ${BackupWorkflow.renderFieldHelp({
        purpose: "先保存收件人和发件人标识，后续再接入真实邮件发送。",
        example: "ops@example.com",
        format: "每行一个邮箱地址。",
        safety: "邮件正文里不要包含密码或 token。",
      })}
      <div class="actions">
        <button onclick="saveNotifications()">保存通知设置</button>
      </div>
    </div>
    ${BackupWorkflow.renderStepFooter(stepId, state.workflow)}
  `;
}

function renderMigration() {
  const storage = activeStorage();
  const mountpoint = storage?.mountpoint || "";

  $("#migration").innerHTML = `
    ${BackupWorkflow.renderStepHeader(
      "dataset",
      state.workflow,
      "只有在你需要独立快照、配额、权限边界，或者想把大目录升级成独立 dataset 时，才使用这一页。",
      [
        "当前活动存储必须是 ZFS",
        "Pool 里要有足够的临时空间",
        "开始迁移前先暂停该目录的高频写入"
      ]
    )}
    <div class="band">
      <h3>第 1 步：创建临时迁移目录</h3>
      <div class="grid">
        <div>
          <label>挂载点</label>
          <input id="migrationMount" value="${escapeAttr(mountpoint)}" placeholder="/Gensol">
        </div>
        <div>
          <label>临时目录名</label>
          <input id="migrationName" value="_migration_${dateStamp()}">
        </div>
      </div>
      ${BackupWorkflow.renderFieldHelp({
        purpose: "这一步会在同一个 pool 里创建一个临时目录，用来先搬走旧目录。",
        example: "_migration_20260623",
        safety: "如果只有数据池空间足够，临时目录也应该放在同一个 pool 里。",
      })}
      <div class="actions">
        <button onclick="runOperation('migration-create-temp', migrationTempPayload())">创建临时目录</button>
      </div>
    </div>
    <div class="card danger-note">
      <h3>第 2 步：复制到新 dataset</h3>
      <div class="grid">
        <div>
          <label>源目录（通常是 .old）</label>
          <input id="migrationSource" placeholder="/Gensol/_migration_20260623/财务.old">
        </div>
        <div>
          <label>新 dataset 挂载点</label>
          <input id="migrationTarget" placeholder="/Gensol/财务">
        </div>
      </div>
      ${BackupWorkflow.renderFieldHelp({
        purpose: "先把旧目录挪开，再创建同名 dataset，最后用 rsync 复制回去。",
        example: "/Gensol/_migration_20260623/财务.old -> /Gensol/财务",
        safety: "确认无误前不要删除 .old 原目录。",
      })}
      <div class="actions">
        <button class="danger" onclick="runOperation('migration-rsync', migrationRsyncPayload())">执行 rsync</button>
      </div>
    </div>
    ${BackupWorkflow.renderStepFooter("dataset", state.workflow)}
  `;
}

function renderWindows() {
  const win = state.config.windows_backup || {};
  const sources = (win.source_drives || ["D", "E"]).map(windowsSourceDisplay);
  const discoveredDrives = state.discovery?.windows_drives || [];

  $("#windows").innerHTML = `
    ${BackupWorkflow.renderStepHeader(
      "windows",
      state.workflow,
      "把 Windows 的整个盘符或指定文件夹备份到 NAS。默认建议从 D: 和 E: 开始，而不是备份系统盘。",
      [
        "Windows 主机需要能访问 NAS 的 SMB 路径",
        "首次镜像前，目标目录最好是空目录",
        "确认是否真的要使用 /MIR 镜像模式"
      ]
    )}
    <div class="band">
      <h3>Windows 本机备份</h3>
      <div class="grid">
        <div>
          <label>SMB 目标</label>
          <input id="winTarget" value="${escapeAttr(win.smb_target || "")}" placeholder="\\\\10.0.0.10\\数据备份\\Windows-PC">
        </div>
        <div>
          <label>备份来源</label>
          <textarea id="winSources" placeholder="D:\\\nE:\\\nD:\\财务资料">${escapeHtml(sources.join("\n"))}</textarea>
        </div>
      </div>
      ${BackupWorkflow.renderFieldHelp({
        purpose: "可以填写整个盘符，也可以填写具体文件夹路径。",
        example: "D:\\\nE:\\\nD:\\财务资料",
        format: "多条路径时每行一条，不需要加引号。",
        safety: "robocopy 的 /MIR 可能删除目标端多余文件。",
      })}
      ${
        discoveredDrives.length
          ? `<p class="muted">当前检测到的本机盘符：</p>
             <div class="badge-row">
               ${discoveredDrives
                 .map(
                   (drive) =>
                     `<button class="secondary compact" onclick="appendWindowsSource('${escapeAttr(drive.path)}')">${escapeHtml(drive.path)}</button>`
                 )
                 .join("")}
             </div>`
          : ""
      }
      <div class="actions">
        <button onclick="saveWindows()">保存 Windows 备份配置</button>
        <button class="secondary" onclick="previewWindowsCommands()">生成命令</button>
      </div>
      <pre id="windowsPreview"></pre>
    </div>
    ${BackupWorkflow.renderStepFooter("windows", state.workflow)}
  `;
}

function renderCloud() {
  const cloud = state.config.cloud_remote || {};

  $("#cloud").innerHTML = `
    ${BackupWorkflow.renderStepHeader(
      "cloud",
      state.workflow,
      "把已经加密过的 Restic 仓库同步到云端，形成异地副本。不要直接上传明文业务目录。",
      [
        "先完成一次成功的 Restic 备份",
        "先确认云端服务和路径方向无误",
        "第一次正式同步前最好先手动 dry-run"
      ]
    )}
    <div class="band">
      <h3>云端副本</h3>
      <div class="grid">
        <div>
          <label>服务商</label>
          <select id="cloudProvider">
            ${option("baidu", "baidu", cloud.provider || "baidu")}
            ${option("webdav", "webdav", cloud.provider || "baidu")}
            ${option("s3", "s3", cloud.provider || "baidu")}
          </select>
        </div>
        <div>
          <label>rclone remote</label>
          <input id="cloudRemote" value="${escapeAttr(cloud.remote_name || "")}" placeholder="baidu:/NAS_Backup/restic-repo">
        </div>
        <div>
          <label>本地源</label>
          <input id="cloudSource" value="${escapeAttr(cloud.sync_source || state.config.restic?.repository || "")}" placeholder="/Gensol/_cloud_restic/restic-repo">
        </div>
      </div>
      ${BackupWorkflow.renderFieldHelp({
        purpose: "当前版本通过 rclone remote 管理服务商认证，本页保存 provider、remote 和同步源。",
        example: "baidu:/NAS_Backup/restic-repo",
        format: "remote名称:/目录",
        safety: "确认同步方向正确，避免把空目录反向覆盖到云端。",
      })}
      <div class="actions">
        <button onclick="saveCloud()">保存云端配置</button>
        <button class="secondary" onclick="runOperation('cloud-rclone-sync', cloudPayload())">执行同步</button>
      </div>
    </div>
    <div class="card">
      <h3>最近一次云端同步</h3>
      ${renderLatestOperationCard("cloud-rclone-sync", "还没有执行过云端同步。")}
    </div>
    ${BackupWorkflow.renderStepFooter("cloud", state.workflow)}
  `;
}

function renderPve() {
  const pve = state.config.pve_pbs || {};

  $("#pve").innerHTML = `
    ${BackupWorkflow.renderStepHeader(
      "pve_pbs",
      state.workflow,
      "这一页只用于连接 PVE 宿主机本身，调用 PVE / PBS 的原生命令去做 VM / CT 备份。",
      [
        "当前连接目标应当是 PVE 宿主机，而不是 OMV 虚拟机",
        "PBS storage 已经接入 PVE",
        "升级 PVE 前，建议至少做一次恢复演练"
      ]
    )}
    <div class="band">
      <h3>PVE / PBS 配置</h3>
      <div class="grid">
        <div>
          <label>PVE Host</label>
          <input id="pveHost" value="${escapeAttr(pve.pve_host || "")}" placeholder="10.0.0.3">
        </div>
        <div>
          <label>PBS Storage ID</label>
          <input id="pbsStorage" value="${escapeAttr(pve.pbs_storage || "")}" placeholder="pbs-backup">
        </div>
        <div>
          <label>目标 PVE 版本</label>
          <input id="targetVersion" value="${escapeAttr(pve.target_version || "")}" placeholder="PVE 9.x">
        </div>
      </div>
      ${BackupWorkflow.renderFieldHelp({
        purpose: "PBS Storage ID 填 PVE Datacenter -> Storage 里看到的 ID，不是磁盘路径。",
        example: "pbs-backup",
      })}
      <div class="actions">
        <button onclick="savePve()">保存 PVE / PBS 配置</button>
        <button class="secondary" onclick="runOperation('pve-list-guests', {})">读取 VM / CT</button>
      </div>
    </div>
    <div class="card">
      <h3>执行一次 PVE 备份</h3>
      <div class="grid">
        <div>
          <label>VM / CT ID</label>
          <input id="pveGuestId" placeholder="105">
        </div>
        <div>
          <label>模式</label>
          <select id="pveMode">
            ${option("snapshot", "snapshot", "snapshot")}
            ${option("suspend", "suspend", "snapshot")}
            ${option("stop", "stop", "snapshot")}
          </select>
        </div>
      </div>
      <div class="actions">
        <button onclick="runOperation('pve-vzdump', pveBackupPayload())">执行 vzdump</button>
      </div>
    </div>
    <div class="card">
      <h3>已发现的 PBS 备份</h3>
      ${renderPbsArtifactTable()}
    </div>
    <div class="card">
      <h3>最近一次 VM / CT 列表读取</h3>
      ${renderLatestOperationCard("pve-list-guests", "还没有读取过 VM / CT 列表。")}
    </div>
    ${BackupWorkflow.renderStepFooter("pve_pbs", state.workflow)}
  `;
}

function renderJobs() {
  $("#jobs").innerHTML = `
    <div class="band">
      <h2>${WorkOps.t("jobs.title")}</h2>
      <p class="muted">${WorkOps.t("jobs.desc")}</p>
    </div>
    <div class="card">
      ${state.jobs.length ? state.jobs.map(renderJob).join("") : `<p class="muted">${WorkOps.t("jobs.noJobs")}</p>`}
    </div>
  `;
}

function renderProfileSummary() {
  const profile = state.profile || { label: "Unknown", kind: "unknown" };
  const capabilityLines = Object.entries(state.capabilities || {})
    .map(
      ([name, enabled]) =>
        `<span class="pill ${enabled ? "ok-pill" : ""}">${escapeHtml(name)}: ${
          enabled ? "yes" : "no"
        }</span>`
    )
    .join(" ");

  return `
    <p><strong>${WorkOps.t("common.platform")}</strong>${escapeHtml(profile.label || profile.kind)}</p>
    <p><strong>${WorkOps.t("common.source")}</strong>${escapeHtml(profile.source || "-")}</p>
    <p><strong>${WorkOps.t("common.capabilities")}</strong>${capabilityLines || `<span class="muted">${WorkOps.t("common.notDetected")}</span>`}</p>
  `;
}

function renderDiscovery() {
  const discovery =
    state.discovery || normalizeInventoryStorage(state.inventory?.storage || {});
  const pools = discovery.pools || [];
  const datasets = discovery.datasets || [];
  const folders = discovery.folders || [];
  const candidates = discovery.storage_candidates || [];
  const restoreCandidates = discovery.restore_root_candidates || [];
  const drives = discovery.windows_drives || [];
  const errors = discovery.errors || [];

  return `
    ${errors
      .map(
        (error) =>
          `<div class="connection-result error"><strong>${escapeHtml(
            error.message || error.code
          )}</strong><span>${escapeHtml(
            error.recovery || "请检查远程命令和权限。"
          )}</span></div>`
      )
      .join("")}
    <h4>${WorkOps.t("discovery.suggestedStorage")}</h4>
    ${
      candidates.length
        ? table(
            ["Dataset", "Pool", WorkOps.t("storage.mountpoint"), WorkOps.t("staging.action")],
            candidates.map((candidate) => [
              candidate.name,
              candidate.pool_name,
              candidate.mountpoint,
              `<button class="secondary compact candidate-action" data-candidate="${escapeAttr(
                candidate.id
              )}">${WorkOps.t("discovery.setAsStorage")}</button>`,
            ]),
            true
          )
        : `<p class="muted">${WorkOps.t("discovery.noStorageCandidate")}</p>`
    }
    <h4>${WorkOps.t("discovery.suggestedRestore")}</h4>
    ${
      restoreCandidates.length
        ? table(
            [WorkOps.t("restore.label"), WorkOps.t("restore.path"), WorkOps.t("restore.kind"), WorkOps.t("staging.action")],
            restoreCandidates.map((candidate) => [
              candidate.label,
              candidate.path,
              candidate.kind,
              `<button class="secondary compact restore-candidate-action" data-candidate="${escapeAttr(
                candidate.id
              )}">${WorkOps.t("discovery.setAsRestore")}</button>`,
            ]),
            true
          )
        : `<p class="muted">${WorkOps.t("discovery.noRestoreCandidate")}</p>`
    }
    <h4>${WorkOps.t("discovery.pools")}</h4>
    ${
      pools.length
        ? table(
            [WorkOps.t("storage.name"), WorkOps.getLang() === "en" ? "Size" : "大小", WorkOps.getLang() === "en" ? "Used" : "已用", WorkOps.getLang() === "en" ? "Free" : "可用", WorkOps.getLang() === "en" ? "Health" : "健康"],
            pools.map((pool) => [
              pool.name,
              pool.size,
              pool.allocated,
              pool.free,
              pool.health,
            ])
          )
        : `<p class="muted">${WorkOps.t("discovery.noZpool")}</p>`
    }
    <h4>${WorkOps.t("discovery.datasets")}</h4>
    ${
      datasets.length
        ? table(
            [WorkOps.t("storage.name"), WorkOps.t("storage.mountpoint"), WorkOps.getLang() === "en" ? "Used" : "已用", WorkOps.getLang() === "en" ? "Available" : "可用"],
            datasets.map((dataset) => [
              dataset.name,
              dataset.mountpoint,
              dataset.used,
              dataset.avail,
            ])
          )
        : `<p class="muted">${WorkOps.t("discovery.noDataset")}</p>`
    }
    <h4>${WorkOps.t("discovery.firstLevelFolders")}</h4>
    ${
      folders.length
        ? table(
            [WorkOps.t("storage.name"), WorkOps.t("restore.path")],
            folders.map((folder) => [folder.name, folder.path])
          )
        : `<p class="muted">${WorkOps.t("discovery.noFolder")}</p>`
    }
    ${
      drives.length
        ? `<h4>${WorkOps.t("discovery.localDrives")}</h4>${table(
            [WorkOps.getLang() === "en" ? "Drive" : "盘符", WorkOps.t("restore.path")],
            drives.map((drive) => [drive.letter || "-", drive.path || "-"])
          )}`
        : ""
    }
  `;
}

function renderRestoreRootCandidates() {
  const candidates =
    state.discovery?.restore_root_candidates ||
    state.inventory?.storage?.restore_root_candidates ||
    [];
  if (!candidates.length) {
    return `<p class="muted">${WorkOps.t("discovery.noRestoreCandidates")}</p>`;
  }
  return `
    <h4>${WorkOps.getLang() === "en" ? "Candidates" : "候选项"}</h4>
    ${table(
      [WorkOps.t("restore.label"), WorkOps.t("restore.path"), WorkOps.t("restore.kind"), WorkOps.t("staging.action")],
      candidates.map((candidate) => [
        candidate.label,
        candidate.path,
        candidate.kind,
        `<button class="secondary compact restore-candidate-action" data-candidate="${escapeAttr(
          candidate.id
        )}">${WorkOps.t("discovery.fillForm")}</button>`,
      ]),
      true
    )}
  `;
}

function renderStagingTable(rows, appManaged) {
  if (!rows.length) {
    return `<p class="muted">${WorkOps.t("staging.noDir")}</p>`;
  }

  return `
    <table class="inventory-table">
      <thead>
        <tr>
          <th>${WorkOps.t("staging.dirExists")}</th>
          <th>${WorkOps.t("staging.hasFiles")}</th>
          <th>${WorkOps.t("staging.name")}</th>
          <th>${WorkOps.t("staging.path")}</th>
          <th>${WorkOps.t("staging.sourceSnapshot")}</th>
          <th>${WorkOps.t("staging.status")}</th>
          <th>${WorkOps.t("staging.action")}</th>
        </tr>
      </thead>
      <tbody>
        ${rows
          .map((row) => {
            const deleteAction =
              row.exists
                ? `<button class="danger compact" onclick="promptDeleteStaging('${escapeAttr(
                    row.path
                  )}', ${appManaged})">${WorkOps.t("btn.delete")}</button>`
                : `<span class="muted">${WorkOps.t("staging.cleaned")}</span>`;
            return `
              <tr>
                <td>${row.exists ? WorkOps.t("staging.yes") : WorkOps.t("staging.no")}</td>
                <td>${row.has_files ? WorkOps.t("staging.yes") : WorkOps.t("staging.no")}</td>
                <td>${escapeHtml(row.name)}</td>
                <td>${escapeHtml(row.path)}</td>
                <td>${escapeHtml(row.snapshot_id || WorkOps.t("staging.notLinked"))}</td>
                <td><span class="status-chip">${escapeHtml(row.status)}</span></td>
                <td>${deleteAction}</td>
              </tr>
            `;
          })
          .join("")}
      </tbody>
    </table>
  `;
}

function renderBackupTaskTable(tasks) {
  if (!tasks.length) {
    return `<p class="muted">${WorkOps.getLang() === "en" ? "No discovered backup tasks yet." : "当前还没有已发现的备份任务。"}</p>`;
  }
  return table(
    [WorkOps.t("storage.name"), WorkOps.t("restore.kind"), WorkOps.getLang() === "en" ? "Target" : "目标", WorkOps.getLang() === "en" ? "Latest Result" : "最近结果", WorkOps.getLang() === "en" ? "Latest Time" : "最近时间", WorkOps.getLang() === "en" ? "Next" : "下一步"],
    tasks.map((task) => [
      task.name,
      task.type,
      task.destination,
      task.latest_result,
      task.latest_execution_time || "-",
      `<button class="secondary compact" onclick="openWorkflowStep('${escapeAttr(
        task.next_step || "restic"
      )}')">打开</button>`,
    ]),
    true
  );
}

function renderArtifactOverview() {
  const resticSnapshots = resticSnapshotRows();
  const pbsBackups = pbsArtifactRows();
  return `
    <div class="artifact-section">
      <h4>Restic 快照</h4>
      ${renderResticSnapshotTable()}
    </div>
    <div class="artifact-section">
      <h4>PBS 备份</h4>
      ${pbsBackups.length ? renderPbsArtifactTable() : `<p class="muted">当前没有发现 PBS 备份。</p>`}
    </div>
  `;
}

function renderResticSnapshotTable() {
  const rows = resticSnapshotRows();
  if (!rows.length) {
    return `<p class="muted">${WorkOps.t("nas.noSnapshots")}</p>`;
  }
  return table(
    [WorkOps.getLang() === "en" ? "Snapshot" : "快照", WorkOps.getLang() === "en" ? "Time" : "时间", WorkOps.getLang() === "en" ? "Host" : "主机", WorkOps.getLang() === "en" ? "Tags" : "标签", WorkOps.t("restore.path"), WorkOps.t("staging.action")],
    rows.map((row) => [
      row.short_id || row.id || "-",
      row.time || "-",
      row.hostname || "-",
      renderInlineList(row.tags || []),
      renderInlineList(row.paths || []),
      `<button class="secondary compact" onclick="useSnapshotForRestore('${escapeAttr(
        row.short_id || row.id || "latest"
      )}')">用于恢复</button>`,
    ]),
    true
  );
}

function renderPbsArtifactTable() {
  const rows = pbsArtifactRows();
  if (!rows.length) {
    return `<p class="muted">${WorkOps.t("pve.noPbs")}</p>`;
  }
  return table(
    ["ID", WorkOps.getLang() === "en" ? "Time" : "时间", "VM/CT", "Storage", WorkOps.t("staging.status")],
    rows.map((row) => [
      row.id || "-",
      row.time || "-",
      row.guest_id || "-",
      row.storage || "-",
      row.status || row.kind || "-",
    ])
  );
}

function renderScheduleTable() {
  const rows = state.discovery?.schedules || [];
  if (!rows.length) {
    return `<p class="muted">${WorkOps.t("nas.noSchedule")}</p>`;
  }
  return table(
    ["ID", WorkOps.t("restore.kind"), WorkOps.getLang() === "en" ? "Command" : "命令", WorkOps.getLang() === "en" ? "Next Run" : "下次运行", WorkOps.getLang() === "en" ? "Last Run" : "上次运行"],
    rows.map((row) => [
      row.id || "-",
      row.type || "-",
      row.command || "-",
      row.next_run || "-",
      row.last_run || "-",
    ])
  );
}

function renderLatestOperationCard(operationId, emptyText) {
  const job = latestJob(operationId);
  if (!job) {
    return `<p class="muted">${escapeHtml(emptyText)}</p>`;
  }
  return `
    <p><strong>${WorkOps.t("common.status")}</strong><span class="pill ${job.status === "success" ? "ok-pill" : ""}">${escapeHtml(job.status)}</span></p>
    <p><strong>${WorkOps.t("common.completedAt")}</strong>${escapeHtml(job.finished_at || "-")}</p>
    <details>
      <summary>${WorkOps.t("jobs.viewOutputTitle")}</summary>
      <pre>${escapeHtml([job.stdout, job.stderr].filter(Boolean).join("\n"))}</pre>
    </details>
  `;
}

function renderJob(job) {
  const stepId = job.step_id || operationStep(job.operation_id);
  return `
    <div class="card">
      <h3>${escapeHtml(job.title)} <span class="pill ${job.status === "success" ? "ok-pill" : ""}">${escapeHtml(job.status)}</span></h3>
      <p class="muted">${WorkOps.t("jobs.stepLabel")}${escapeHtml(
        BackupWorkflow.stepById(state.workflow, stepId)?.title || WorkOps.t("jobs.other")
      )} | ${escapeHtml(job.finished_at || "-")} | ${WorkOps.t("jobs.returnCode")} ${escapeHtml(
        String(job.returncode)
      )}</p>
      <div class="actions">
        <button class="secondary compact" onclick="openWorkflowStep('${escapeAttr(stepId)}')">${WorkOps.t("jobs.backToStep")}</button>
      </div>
      <details>
        <summary>${WorkOps.t("jobs.viewOutput")}</summary>
        <pre>${escapeHtml([job.stdout, job.stderr].filter(Boolean).join("\n"))}</pre>
      </details>
    </div>
  `;
}

function operationStep(operationId) {
  const map = {
    "restic-backup": "first_backup",
    "restic-restore": "restore_center",
    "restic-snapshots": "restic",
    "restic-check": "schedule",
    "restic-prune": "schedule",
    "restore-staging-delete": "restore_center",
    "migration-create-temp": "dataset",
    "migration-rsync": "dataset",
    "cloud-rclone-check": "cloud",
    "cloud-rclone-list": "cloud",
    "cloud-rclone-pull": "cloud",
    "cloud-rclone-sync": "cloud",
    "pve-list-guests": "pve_pbs",
    "pve-vzdump": "pve_pbs",
    "windows-robocopy-preview": "windows",
  };
  return map[operationId] || "connect";
}

async function discover() {
  const password = sshPasswordForRequest();
  try {
    if ($("#executorMode")) await saveRuntimeConfig();
    const payload = await api("/api/discover", {
      method: "POST",
      body: JSON.stringify({ ssh_password: password }),
    });
    syncState(payload);
    state.discovery = normalizeInventoryStorage(payload);
    state.connectionResult = null;
    render();
    showPage("storage");
  } catch (error) {
    state.connectionResult = connectionFailure(error);
    render();
    showPage("storage");
  }
}

function applyAutomaticStorageSuggestion() {
  $$(".candidate-action").forEach((button) => {
    button.addEventListener("click", () => {
      populateStorageCandidateById(button.dataset.candidate);
    });
  });

  const candidates = state.discovery?.storage_candidates || [];
  const inputsEmpty = ["#storageName", "#storagePool", "#storageMount"].every(
    (selector) => !($(selector)?.value || "").trim()
  );
  if (!activeStorage() && candidates.length === 1 && inputsEmpty) {
    populateStorageCandidate(candidates[0]);
  }
}

function applyAutomaticRestoreRootSuggestion() {
  $$(".restore-candidate-action").forEach((button) => {
    button.addEventListener("click", () => {
      populateRestoreRootCandidateById(button.dataset.candidate);
    });
  });

  const candidates = state.discovery?.restore_root_candidates || [];
  const inputsEmpty = ["#restoreRootLabel", "#restoreRootPath"].every(
    (selector) => !($(selector)?.value || "").trim()
  );
  if (!activeRestoreRoot() && candidates.length === 1 && inputsEmpty) {
    populateRestoreRootCandidate(candidates[0]);
  }
}

function populateStorageCandidateById(candidateId) {
  const candidate = (state.discovery?.storage_candidates || []).find(
    (item) => item.id === candidateId
  );
  if (candidate) populateStorageCandidate(candidate);
}

function populateStorageCandidate(candidate) {
  if (!$("#storageName")) return;
  $("#storageName").value = candidate.name || "";
  $("#storageKind").value = candidate.kind || "zfs";
  $("#storagePool").value = candidate.pool_name || "";
  $("#storageMount").value = candidate.mountpoint || "";
  $("#storageSuggestion").textContent =
    WorkOps.t("storage.fillSuggestion");
}

function populateRestoreRootCandidateById(candidateId) {
  const candidate = (state.discovery?.restore_root_candidates || []).find(
    (item) => item.id === candidateId
  );
  if (candidate) populateRestoreRootCandidate(candidate);
}

function populateRestoreRootCandidate(candidate) {
  if (!$("#restoreRootLabel")) return;
  $("#restoreRootLabel").value = candidate.label || "";
  $("#restoreRootPath").value = candidate.path || "";
  $("#restoreRootKind").value = candidate.kind || "zfs_dataset";
  $("#restoreRootSuggestion").textContent =
    WorkOps.getLang() === "en" ? "Auto-filled from discovery. Please confirm before saving." : "已根据自动发现结果填写恢复根目录，请确认后再保存。";
}

async function saveRuntimeConfig() {
  const keyPathInput = $("#sshKeyPath");
  await saveConfig({
    executor_mode: $("#executorMode").value,
    ssh_host: $("#sshHost").value.trim(),
    ssh_user: $("#sshUser").value.trim() || "root",
    ssh_port: Number($("#sshPort").value) || 22,
    ssh_auth_mode: $("#sshAuthMode").value,
    ssh_key_path: keyPathInput
      ? keyPathInput.value.trim()
      : state.config.ssh_key_path || "",
  });
}

function sshAuthFields(mode) {
  if (mode === "private_key") {
    return `
      <div class="auth-panel">
        <label>私钥路径</label>
        <input id="sshKeyPath" value="${escapeAttr(state.config?.ssh_key_path || "")}" placeholder="/root/.ssh/id_ed25519">
        <p class="muted">Docker 部署时，请把私钥和 known_hosts 只读挂载进容器，并填写容器内路径。</p>
      </div>
    `;
  }
  if (mode === "password") {
    return `
      <div class="auth-panel">
        <label>SSH 密码</label>
        <input id="sshPassword" type="password" autocomplete="current-password" value="${escapeAttr(state.sshPassword)}" placeholder="仅保存在当前页面内存">
        <p class="muted">密码不会写入配置文件、任务日志或命令行。刷新页面后会自动清除。</p>
      </div>
    `;
  }
  return `
    <div class="auth-panel">
      <p class="muted">使用 OpenSSH 默认密钥、SSH Agent 或 ~/.ssh/config。SSH Host 也可以填写 SSH 配置中的 Host 别名。</p>
    </div>
  `;
}

function renderSshAuthFields() {
  const currentPassword = $("#sshPassword")?.value;
  if (currentPassword !== undefined) state.sshPassword = currentPassword;
  $("#sshAuthFields").innerHTML = sshAuthFields($("#sshAuthMode").value);
}

function sshPasswordForRequest() {
  const input = $("#sshPassword");
  if (input) state.sshPassword = input.value;
  const mode = $("#sshAuthMode")?.value || state.config?.ssh_auth_mode;
  return mode === "password" ? state.sshPassword : "";
}

async function testSshConnection() {
  const password = sshPasswordForRequest();
  try {
    await saveRuntimeConfig();
    const payload = await api("/api/test-ssh", {
      method: "POST",
      body: JSON.stringify({ ssh_password: password }),
    });
    syncState(payload);
    state.connectionResult = {
      ok: true,
      message: payload.message,
      recovery: "",
    };
  } catch (error) {
    state.connectionResult = connectionFailure(error);
  }
  render();
  showPage("storage");
}

function connectionFailure(error) {
  return {
    ok: false,
    message: error.details?.message || error.message || (WorkOps.getLang() === "en" ? "SSH connection failed." : "SSH 连接失败。"),
    recovery:
      error.details?.recovery ||
      (WorkOps.getLang() === "en" ? "Check host, port, auth method, and network connection." : "请检查主机、端口、认证方式和网络连接。"),
  };
}

function connectionResultHtml() {
  if (!state.connectionResult) return "";
  const kind = state.connectionResult.ok ? "success" : "error";
  return `
    <div class="connection-result ${kind}">
      <strong>${escapeHtml(state.connectionResult.message)}</strong>
      ${
        state.connectionResult.recovery
          ? `<span>${escapeHtml(state.connectionResult.recovery)}</span>`
          : ""
      }
    </div>
  `;
}

async function addStorageTarget() {
  const target = {
    id: `storage-${Date.now()}`,
    name: $("#storageName").value.trim(),
    kind: $("#storageKind").value,
    pool_name: $("#storagePool").value.trim(),
    mountpoint: $("#storageMount").value.trim(),
    notes: "",
  };
  if (!target.name || !target.mountpoint) {
    alert(WorkOps.t("storage.fillNameAndMount"));
    return;
  }
  await saveConfig({
    storage_targets: [...(state.config.storage_targets || []), target],
    active_storage_id: target.id,
  });
}

async function saveRestoreRoot() {
  const root = {
    id:
      activeRestoreRoot()?.id ||
      `restore-root-${Date.now()}`,
    label: $("#restoreRootLabel").value.trim(),
    path: $("#restoreRootPath").value.trim(),
    kind: $("#restoreRootKind").value,
    app_managed: true,
  };
  if (!root.label || !root.path) {
    alert(WorkOps.getLang() === "en" ? "Please fill in restore root label and path." : "请填写恢复根目录标签和路径。");
    return;
  }
  state.restoreDraft.target = `${root.path.replace(/\/$/, "")}/restore-${Date.now()}`;
  await saveConfig({
    restore_roots: [root],
    active_restore_root_id: root.id,
  });
}

async function saveRestic() {
  await saveConfig({
    restic: {
      ...state.config.restic,
      repository: $("#resticRepo").value.trim(),
      password_file: $("#resticPassword").value.trim(),
    },
  });
}

async function saveBackupSet() {
  await saveConfig({
    backup_sets: [
      {
        id: "primary",
        name: "主要备份集",
        include_paths: lines("#includePaths"),
        exclude_patterns: lines("#excludePatterns"),
        tag: "important",
      },
    ],
  });
}

async function saveNotifications() {
  await saveConfig({
    notification_emails: lines("#notificationEmails"),
    notification_sender: $("#notificationSender").value.trim(),
  });
}

async function saveWindows() {
  await saveConfig({
    windows_backup: {
      enabled: true,
      smb_target: $("#winTarget").value.trim(),
      source_drives: lines("#winSources"),
      log_path:
        state.config.windows_backup?.log_path ||
        "C:\\Logs\\windows-drive-backup.log",
    },
  });
}

async function saveCloud() {
  await saveConfig({
    cloud_remote: {
      enabled: true,
      provider: $("#cloudProvider").value,
      remote_name: $("#cloudRemote").value.trim(),
      remote_path: $("#cloudRemote").value.trim(),
      sync_source: $("#cloudSource").value.trim(),
      notes: "",
    },
  });
}

async function savePve() {
  await saveConfig({
    pve_pbs: {
      enabled: true,
      pve_host: $("#pveHost").value.trim(),
      pbs_storage: $("#pbsStorage").value.trim(),
      target_version: $("#targetVersion").value.trim(),
      selected_guests: state.config.pve_pbs?.selected_guests || [],
    },
  });
}

async function saveConfig(patch) {
  notify("info", WorkOps.t("notify.saving"), WorkOps.t("notify.savingDetail"), 2500);
  const payload = await api("/api/config", {
    method: "POST",
    body: JSON.stringify(patch),
  });
  syncState(payload);
  render();
  notify("success", WorkOps.t("notify.saved"), WorkOps.t("notify.savedDetail"), 4500);
}

async function runOperation(operationId, payload) {
  if (operationId === "restic-restore") {
    state.restoreDraft.snapshot = payload.snapshot || "latest";
    state.restoreDraft.target = payload.target || "";
    state.restoreDraft.paths = payload.paths || [];
  }

  notify("info", WorkOps.t("notify.preparing"), WorkOps.t("notify.preparingDetail"), 2500);
  try {
    const prepared = await api("/api/prepare", {
      method: "POST",
      body: JSON.stringify({ operation_id: operationId, payload }),
    });
    const command = prepared.command;
    let confirmation = "";
    if (command.confirm_text) {
      confirmation = await confirmDanger(command);
      if (!confirmation) {
        notify("warning", WorkOps.t("notify.cancelled"), WorkOps.t("notify.cancelledDetail"), 4500);
        return;
      }
    }

    notify("info", WorkOps.t("notify.executing"), WorkOps.t("notify.executingDetail"), 0);
    const result = await api("/api/run", {
      method: "POST",
      body: JSON.stringify({
        operation_id: operationId,
        payload,
        confirmation,
        ssh_password: sshPasswordForRequest(),
        async: true,
      }),
    });

    if (result.job?.status === "running") {
      trackActiveJob(result.job);
      notify("info", WorkOps.t("notify.taskStarted"), `${result.job.title || operationId} ${WorkOps.t("notify.taskRunning")}`, 3500);
      const completed = await pollOperationJob(result.job.id);
      applyOperationResult(completed, operationId);
      return;
    }

    applyOperationResult(result, operationId);
  } catch (error) {
    // HERMES_EDIT: 显示详细的错误面板，而不是简短的通知
    showErrorPanel(operationId, error, payload);
  }
}

// HERMES_EDIT: 新增 - 显示详细的错误面板
function showErrorPanel(operationId, error, payload) {
  // 移除旧面板和遮罩
  const existingPanel = document.querySelector("#operationResultPanel");
  if (existingPanel) {
    existingPanel.remove();
  }
  const existingOverlay = document.querySelector("#operationResultOverlay");
  if (existingOverlay) {
    existingOverlay.remove();
  }

  // 解析错误信息
  const errorMessage = error.message || WorkOps.t("error.unknown");
  const errorDetails = error.details || {};
  
  // 根据错误类型提供具体的解决建议
  let suggestion = "";
  let missingFields = [];
  
  if (errorMessage.includes("repository is required")) {
    suggestion = WorkOps.t("error.repoRequired");
    missingFields = [WorkOps.getLang() === "en" ? "Restic Repository Path" : "Restic 仓库路径"];
  } else if (errorMessage.includes("password file is required")) {
    suggestion = WorkOps.t("error.passRequired");
    missingFields = [WorkOps.getLang() === "en" ? "Restic Password File" : "Restic 密码文件"];
  } else if (errorMessage.includes("restore target is required")) {
    suggestion = WorkOps.t("error.targetRequired");
    missingFields = [WorkOps.getLang() === "en" ? "Restore Target Path" : "恢复目标路径"];
  } else if (errorMessage.includes("system or temporary path")) {
    suggestion = WorkOps.t("error.systemPath");
  } else if (errorMessage.includes("must contain at least one path")) {
    suggestion = WorkOps.t("error.needPath");
    missingFields = [WorkOps.getLang() === "en" ? "Backup Paths" : "备份路径"];
  } else if (errorMessage.includes("remote is required")) {
    suggestion = WorkOps.t("error.remoteRequired");
    missingFields = [WorkOps.getLang() === "en" ? "Remote Name" : "Remote 名称"];
  } else if (errorMessage.includes("source and remote are required")) {
    suggestion = WorkOps.t("error.syncRequired");
    missingFields = [WorkOps.getLang() === "en" ? "Sync Source" : "同步源路径", WorkOps.getLang() === "en" ? "Remote Name" : "Remote 名称"];
  } else if (errorMessage.includes("guest_id must be a VM/CT numeric id")) {
    suggestion = WorkOps.t("error.guestIdInvalid");
    missingFields = ["Guest ID"];
  } else if (errorMessage.includes("PBS storage id is required")) {
    suggestion = WorkOps.t("error.pbsRequired");
    missingFields = ["PBS Storage ID"];
  } else if (errorMessage.includes("mountpoint must be an absolute Linux path")) {
    suggestion = WorkOps.t("error.mountAbsolute");
  } else if (errorMessage.includes("source and target must be absolute Linux paths")) {
    suggestion = WorkOps.t("error.pathAbsolute");
  } else if (errorMessage.includes("source must be an absolute Windows drive")) {
    suggestion = WorkOps.t("error.winDriveFormat");
  } else if (errorMessage.includes("SMB target is required")) {
    suggestion = WorkOps.t("error.smbRequired");
    missingFields = [WorkOps.getLang() === "en" ? "SMB Target Path" : "SMB 目标路径"];
  } else if (errorMessage.includes("confirmation_required")) {
    suggestion = WorkOps.t("error.confirmRequired");
  } else if (errorMessage.includes("fetch") || errorMessage.includes("network")) {
    suggestion = WorkOps.t("error.networkFailed");
  } else {
    suggestion = WorkOps.t("error.checkConfig");
  }

  // 创建遮罩层
  const overlay = document.createElement("div");
  overlay.id = "operationResultOverlay";
  overlay.className = "operation-result-overlay";
  overlay.onclick = closeOperationResultPanel;
  document.body.appendChild(overlay);

  // 创建错误面板
  const panel = document.createElement("div");
  panel.id = "operationResultPanel";
  panel.className = "operation-result-panel error";
  panel.innerHTML = `
    <div class="operation-result-header">
      <div class="operation-result-title">
        <span class="operation-result-icon">⚠️</span>
        <div>
          <h3>${escapeHtml(getOperationTitle(operationId))}</h3>
          <p class="operation-result-status">${WorkOps.t("notify.cannotExecute")}</p>
        </div>
      </div>
      <button class="secondary compact" onclick="closeOperationResultPanel()">关闭</button>
    </div>
    <div class="operation-result-section error-highlight">
      <h4>❌ ${WorkOps.t("error.title")}</h4>
      <p class="error-message">${escapeHtml(errorMessage)}</p>
    </div>
    <div class="operation-result-section">
      <h4>💡 ${WorkOps.t("error.suggestion")}</h4>
      <p class="suggestion-message">${escapeHtml(suggestion)}</p>
      ${missingFields.length > 0 ? `
        <div class="missing-fields">
          <p>${WorkOps.t("error.missingFields")}</p>
          <ul>
            ${missingFields.map(field => `<li>${escapeHtml(field)}</li>`).join("")}
          </ul>
        </div>
      ` : ""}
    </div>
    <div class="operation-result-section">
      <h4>📋 ${WorkOps.t("error.currentParams")}</h4>
      <pre class="operation-result-output">${escapeHtml(JSON.stringify(payload, null, 2))}</pre>
    </div>
    <div class="operation-result-section">
      <p class="muted">${WorkOps.t("error.retryHint")}</p>
    </div>
  `;

  document.body.appendChild(panel);

  // 同时显示一个简短的通知
  notify("error", WorkOps.t("notify.cannotExecute"), errorMessage);
}

// HERMES_EDIT: 新增 - 获取操作标题
function getOperationTitle(operationId) {
  return WorkOps.t("op." + operationId) || operationId;
}

async function pollOperationJob(jobId) {
  const payload = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
  if (payload.job) {
    trackActiveJob(payload.job);
  }
  if (payload.job?.status === "running") {
    await delay(OPERATION_POLL_MS);
    return pollOperationJob(jobId);
  }
  return payload;
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function applyOperationResult(result, operationId) {
  syncState(result);
  if (result.inventory?.storage) {
    state.discovery = normalizeInventoryStorage(result.inventory.storage);
  }
  if (result.job) {
    state.jobs = [result.job, ...(state.jobs || []).filter((item) => item.id !== result.job.id)];
    clearActiveJob(result.job.id);
    const ok = result.job.status === "success";
    notify(
      ok ? "success" : "error",
      ok ? WorkOps.t("notify.taskSuccess") : WorkOps.t("notify.taskFailed"),
      `${result.job.title || operationId}：${result.job.status}`
    );
    // HERMES_EDIT: 显示详细的操作结果面板
    showOperationResultPanel(result.job, operationId);
  }
  render();
  showPage(operationPage(operationId));
}

// HERMES_EDIT: 新增 - 操作结果面板显示函数
function showOperationResultPanel(job, operationId) {
  // 移除旧面板和遮罩
  const existingPanel = document.querySelector("#operationResultPanel");
  if (existingPanel) {
    existingPanel.remove();
  }
  const existingOverlay = document.querySelector("#operationResultOverlay");
  if (existingOverlay) {
    existingOverlay.remove();
  }

  const isSuccess = job.status === "success";
  const statusIcon = isSuccess ? "✅" : "❌";
  const statusText = isSuccess ? WorkOps.t("error.success") : WorkOps.t("error.failed");
  const statusClass = isSuccess ? "success" : "error";

  // 截断过长的输出
  const maxOutputLength = 2000;
  let stdout = job.stdout || "";
  let stderr = job.stderr || "";
  if (stdout.length > maxOutputLength) {
    stdout = stdout.substring(0, maxOutputLength) + "\n" + WorkOps.t("error.outputTruncated");
  }
  if (stderr.length > maxOutputLength) {
    stderr = stderr.substring(0, maxOutputLength) + "\n" + WorkOps.t("error.outputTruncated");
  }

  // 创建遮罩层
  const overlay = document.createElement("div");
  overlay.id = "operationResultOverlay";
  overlay.className = "operation-result-overlay";
  overlay.onclick = closeOperationResultPanel;
  document.body.appendChild(overlay);

  // 创建面板
  const panel = document.createElement("div");
  panel.id = "operationResultPanel";
  panel.className = `operation-result-panel ${statusClass}`;
  panel.innerHTML = `
    <div class="operation-result-header">
      <div class="operation-result-title">
        <span class="operation-result-icon">${statusIcon}</span>
        <div>
          <h3>${escapeHtml(job.title || operationId)}</h3>
          <p class="operation-result-status">${escapeHtml(statusText)}</p>
        </div>
      </div>
      <button class="secondary compact" onclick="closeOperationResultPanel()">关闭</button>
    </div>
    <div class="operation-result-meta">
      <span>${WorkOps.t("error.status")}: <strong>${escapeHtml(job.status)}</strong></span>
      <span>${WorkOps.t("error.returnCode")}: <strong>${escapeHtml(String(job.returncode ?? "N/A"))}</strong></span>
      ${job.started_at ? `<span>${WorkOps.t("error.startTime")}: ${escapeHtml(formatTime(job.started_at))}</span>` : ""}
      ${job.finished_at ? `<span>${WorkOps.t("error.endTime")}: ${escapeHtml(formatTime(job.finished_at))}</span>` : ""}
    </div>
    ${stdout ? `
      <div class="operation-result-section">
        <h4>${WorkOps.t("error.stdout")}</h4>
        <pre class="operation-result-output">${escapeHtml(stdout)}</pre>
      </div>
    ` : ""}
    ${stderr ? `
      <div class="operation-result-section">
        <h4>${WorkOps.t("error.stderr")}</h4>
        <pre class="operation-result-output error">${escapeHtml(stderr)}</pre>
      </div>
    ` : ""}
    ${!stdout && !stderr ? `
      <div class="operation-result-section">
        <p class="muted">${WorkOps.t("error.noOutput")}</p>
      </div>
    ` : ""}
  `;

  document.body.appendChild(panel);

  // 8秒后自动关闭成功的结果（失败的结果保持显示）
  if (isSuccess) {
    setTimeout(() => {
      if (document.querySelector("#operationResultPanel") === panel) {
        closeOperationResultPanel();
      }
    }, 8000);
  }
}

// HERMES_EDIT: 新增 - 关闭操作结果面板
function closeOperationResultPanel() {
  const panel = document.querySelector("#operationResultPanel");
  if (panel) {
    panel.remove();
  }
  const overlay = document.querySelector("#operationResultOverlay");
  if (overlay) {
    overlay.remove();
  }
}

// HERMES_EDIT: 新增 - 格式化时间显示
function formatTime(isoString) {
  if (!isoString) return "";
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return isoString;
  }
}

function confirmDanger(command) {
  return new Promise((resolve) => {
    const dialog = $("#dangerDialog");
    $("#dangerTitle").textContent = command.title;
    $("#dangerBody").textContent = `${command.instructions} ${command.impact} 解决方法：${command.recovery}`;
    $("#dangerCommand").textContent = command.argv.join(" ");
    $("#dangerInput").value = "";
    dialog.showModal();
    dialog.addEventListener(
      "close",
      () => {
        if (
          dialog.returnValue === "confirm" &&
          $("#dangerInput").value === command.confirm_text
        ) {
          resolve(command.confirm_text);
        } else {
          resolve("");
        }
      },
      { once: true }
    );
  });
}

async function promptDeleteStaging(path, appManaged) {
  const restoreRoot = activeRestoreRoot();
  if (!restoreRoot) {
    alert(WorkOps.t("restore.fillRootFirst"));
    return;
  }
  const name = path.split("/").filter(Boolean).pop() || path;
  const confirmText = appManaged ? `DELETE ${name}` : `DELETE ${name}`;
  await runOperation("restore-staging-delete", {
    root_path: restoreRoot.path,
    target: path,
    confirm_text: confirmText,
  });
}

function resticPayload() {
  return {
    repository:
      $("#resticRepo")?.value.trim() || state.config.restic?.repository || "",
    password_file:
      $("#resticPassword")?.value.trim() ||
      state.config.restic?.password_file ||
      "",
  };
}

function resticBackupPayload() {
  return {
    ...resticPayload(),
    include_paths: lines("#includePaths"),
    exclude_patterns: lines("#excludePatterns"),
    exclude_file: "",
    tag: "important",
  };
}

function prunePayload() {
  return {
    ...resticPayload(),
    keep_daily: state.config.restic?.retention_daily || 30,
    keep_weekly: state.config.restic?.retention_weekly || 12,
    keep_monthly: state.config.restic?.retention_monthly || 24,
  };
}

function defaultRestoreTarget() {
  const root = activeRestoreRoot()?.path;
  if (!root) return "";
  return `${root.replace(/\/$/, "")}/restore-${Date.now()}`;
}

function restorePayload() {
  return {
    ...resticPayload(),
    snapshot: $("#restoreSnapshot").value.trim() || "latest",
    target: $("#restoreTarget").value.trim(),
    paths: lines("#restorePaths"),
  };
}

function migrationTempPayload() {
  return {
    mountpoint: $("#migrationMount").value.trim(),
    name: $("#migrationName").value.trim(),
  };
}

function migrationRsyncPayload() {
  return {
    source: $("#migrationSource").value.trim(),
    target: $("#migrationTarget").value.trim(),
  };
}

function cloudPayload() {
  return {
    source: $("#cloudSource").value.trim(),
    remote: $("#cloudRemote").value.trim(),
  };
}

function pveBackupPayload() {
  return {
    guest_id: $("#pveGuestId").value.trim(),
    storage: $("#pbsStorage").value.trim(),
    mode: $("#pveMode").value,
  };
}

async function previewWindowsCommands() {
  const target = $("#winTarget").value.trim();
  const sources = lines("#winSources");
  const commands = [];
  for (const source of sources) {
    const prepared = await api("/api/prepare", {
      method: "POST",
      body: JSON.stringify({
        operation_id: "windows-robocopy-preview",
        payload: { source, target },
      }),
    });
    commands.push(prepared.command.argv.join(" "));
  }
  $("#windowsPreview").textContent = commands.join("\n");
}

function useSnapshotForRestore(snapshotId) {
  state.restoreDraft.snapshot = snapshotId || "latest";
  state.restoreDraft.target = defaultRestoreTarget();
  state.restoreDraft.paths = [];
  renderRestore();
  showPage("restore");
}

function appendWindowsSource(path) {
  const textarea = $("#winSources");
  if (!textarea) return;
  const rows = lines("#winSources");
  if (!rows.includes(path)) rows.push(path);
  textarea.value = rows.join("\n");
}

function windowsSourceDisplay(source) {
  const value = String(source || "").trim();
  return /^[A-Za-z]$/.test(value) ? `${value.toUpperCase()}:\\` : value;
}

function activeStorage() {
  const targets = state.config?.storage_targets || [];
  return (
    targets.find((target) => target.id === state.config.active_storage_id) ||
    targets[0] ||
    null
  );
}

function activeRestoreRoot() {
  const roots = state.config?.restore_roots || [];
  return (
    roots.find((root) => root.id === state.config.active_restore_root_id) ||
    roots[0] ||
    null
  );
}

function currentStorageStepId() {
  const connectStep = BackupWorkflow.stepById(state.workflow, "connect");
  return connectStep?.status === "complete" ? "storage" : "connect";
}

function currentNasStepId() {
  const ids = ["restic", "first_backup", "schedule"];
  return (
    ids.find((id) => BackupWorkflow.stepById(state.workflow, id)?.status !== "complete") ||
    "restic"
  );
}

function latestJob(operationId) {
  return (state.jobs || []).find((job) => job.operation_id === operationId) || null;
}

function resticSnapshotRows() {
  return (state.inventory?.backup_artifacts || []).filter(
    (item) => Array.isArray(item.paths) || item.short_id || item.hostname
  );
}

function pbsArtifactRows() {
  return (state.inventory?.backup_artifacts || []).filter(
    (item) => item.kind === "pbs" || item.guest_id || item.storage
  );
}

function operationPage(operationId) {
  return BackupWorkflow.STEP_PAGES[operationStep(operationId)] || "jobs";
}

function openWorkflowStep(stepId) {
  const page = BackupWorkflow.STEP_PAGES[stepId] || "overview";
  showPage(page);
}

async function skipWorkflowStep(stepId) {
  const reason = await requestSkipReason(stepId);
  if (!reason) return;
  const payload = await api("/api/workflow/step", {
    method: "POST",
    body: JSON.stringify({ step_id: stepId, action: "skip", reason }),
  });
  syncState(payload);
  render();
  showPage("overview");
}

async function reopenWorkflowStep(stepId) {
  const payload = await api("/api/workflow/step", {
    method: "POST",
    body: JSON.stringify({ step_id: stepId, action: "reopen" }),
  });
  syncState(payload);
  render();
  openWorkflowStep(stepId);
}

function requestSkipReason(stepId) {
  return new Promise((resolve) => {
    const dialog = $("#skipDialog");
    const step = BackupWorkflow.stepById(state.workflow, stepId);
    $("#skipTitle").textContent = `暂时跳过：${step?.title || stepId}`;
    $("#skipReason").value = "";
    dialog.showModal();
    dialog.addEventListener(
      "close",
      () => {
        const reason = $("#skipReason").value.trim();
        resolve(dialog.returnValue === "confirm" && reason ? reason : "");
      },
      { once: true }
    );
  });
}

function showPage(page) {
  $$(".nav").forEach((item) => {
    item.classList.toggle("active", item.dataset.page === page);
  });
  $$(".page").forEach((item) => {
    item.classList.toggle("active", item.id === page);
  });
}

function lines(selector) {
  return ($(selector)?.value || "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function renderInlineList(values) {
  const rows = Array.isArray(values) ? values.filter(Boolean) : [];
  if (!rows.length) return "-";
  return rows.map((item) => `<div>${escapeHtml(String(item))}</div>`).join("");
}

function table(headers, rows, allowHtml = false) {
  const renderCell = (cell) =>
    allowHtml ? String(cell ?? "") : escapeHtml(String(cell ?? ""));
  return `
    <table class="table inventory-table">
      <thead>
        <tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) =>
              `<tr>${row
                .map((cell) => `<td>${renderCell(cell)}</td>`)
                .join("")}</tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function cloudGuideById(guideId) {
  return CLOUD_GUIDES.find((item) => item.id === guideId) || null;
}

function defaultCloudGuideId(cloud = {}) {
  if (cloud.guide_id && cloudGuideById(cloud.guide_id)) return cloud.guide_id;
  if (cloud.provider === "onedrive" || cloud.backend_type === "onedrive") return "microsoft-onedrive";
  if (cloud.provider === "drive" || cloud.backend_type === "drive") return "google-drive";
  if (cloud.provider === "baidu" && cloud.backend_type === "s3") return "baidu-s3-gateway";
  if (cloud.provider === "baidu") return "baidu-webdav-gateway";
  if (cloud.provider === "webdav" || cloud.backend_type === "webdav") return "generic-webdav";
  if ((cloud.vendor || "").toLowerCase() === "alibaba") return "alibaba-oss";
  if (cloud.provider === "s3" || cloud.backend_type === "s3") return "aws-s3";
  return CLOUD_GUIDES[0].id;
}

function suggestCloudVerifyPath(remotePath) {
  const normalized = String(remotePath || "").trim().replace(/^\/+/, "");
  if (!normalized) return "";
  const segments = normalized.split("/").filter(Boolean);
  if (segments.length <= 1) return normalized;
  return segments.slice(0, -1).join("/");
}

function normalizeCloudValue(field, value) {
  if (value === undefined || value === null) return "";
  if (CLOUD_SESSION_ONLY_KEYS.includes(field)) return String(value);
  return String(value).trim();
}

function ensureCloudSession() {
  const persisted = state.config?.cloud_remote || {};
  const current = state.cloudSession || {};
  const secrets = {};
  CLOUD_SESSION_ONLY_KEYS.forEach((key) => {
    if (current[key]) secrets[key] = current[key];
  });

  const guide = cloudGuideById(defaultCloudGuideId({ ...persisted, ...current })) || CLOUD_GUIDES[0];
  const merged = {
    ...persisted,
    ...current,
    ...secrets,
    enabled: Boolean(persisted.enabled || current.enabled),
    guide_id: guide.id,
    guide_url: current.guide_url || persisted.guide_url || guide.sources?.[0]?.url || "",
    provider: guide.provider,
    backend_type: guide.backendType,
    vendor: guide.vendor,
    sync_source:
      normalizeCloudValue(
        "sync_source",
        current.sync_source || persisted.sync_source || state.config?.restic?.repository || ""
      ),
    notes: normalizeCloudValue("notes", current.notes || persisted.notes || ""),
  };

  if (!merged.verify_path) {
    merged.verify_path = suggestCloudVerifyPath(merged.remote_path || "");
  }
  state.cloudSession = merged;
  return merged;
}

function selectedCloudGuide() {
  const cloud = ensureCloudSession();
  return cloudGuideById(cloud.guide_id) || CLOUD_GUIDES[0];
}

function cloudSavedConfig() {
  return state.config?.cloud_remote || {};
}

function cloudConfigsMatch(left, right) {
  return CLOUD_VERIFICATION_FIELDS.every(
    (field) => normalizeCloudValue(field, left[field] || "") === normalizeCloudValue(field, right[field] || "")
  );
}

function cloudVerificationState(cloud) {
  const saved = cloudSavedConfig();
  const latestCheck = latestJob("cloud-rclone-check");
  const latestSync = latestJob("cloud-rclone-sync");
  const hasConfig = Boolean(cloud.remote_name);
  const savedMatches = hasConfig && cloudConfigsMatch(saved, cloud);
  const verifiedAt = savedMatches ? normalizeCloudValue("verified_at", saved.verified_at || "") : "";

  if (!hasConfig) {
    return {
      tone: "muted",
      label: "未配置",
      detail: "先完成 remote 名称、目标路径和账号参数配置。",
    };
  }
  if (!savedMatches && normalizeCloudValue("verified_at", saved.verified_at || "")) {
    return {
      tone: "warning",
      label: "待重新验证",
      detail: "当前页面里的远端设置和上次已验证配置不一致，保存后请重新执行远端验证。",
    };
  }
  if (verifiedAt) {
    return {
      tone: "success",
      label: "已验证",
      detail: `上次验证时间：${verifiedAt}${latestSync?.status === "success" ? "；最近一次同步成功。" : ""}`,
    };
  }
  if (latestCheck?.status === "failed") {
    return {
      tone: "error",
      label: "验证失败",
      detail: `最近一次验证失败：${latestCheck.finished_at || "请查看任务日志"}`,
    };
  }
  return {
    tone: "warning",
    label: "未验证",
    detail: "请先执行远端验证，确认 remote、网关地址、账号和路径都可读。",
  };
}

function setCloudGuide(guideId) {
  const guide = cloudGuideById(guideId);
  if (!guide) return;
  const cloud = ensureCloudSession();
  state.cloudSession = {
    ...cloud,
    guide_id: guide.id,
    guide_url: guide.sources?.[0]?.url || "",
    provider: guide.provider,
    backend_type: guide.backendType,
    vendor: guide.vendor,
  };
  renderCloud();
}

function toggleCloudEnabled(enabled) {
  const cloud = ensureCloudSession();
  state.cloudSession = { ...cloud, enabled: Boolean(enabled) };
}

function updateCloudSessionField(field, value) {
  const cloud = ensureCloudSession();
  const next = { ...cloud, [field]: normalizeCloudValue(field, value) };
  if (field === "remote_path") {
    const previousSuggestion = suggestCloudVerifyPath(cloud.remote_path || "");
    if (!cloud.verify_path || cloud.verify_path === previousSuggestion) {
      next.verify_path = suggestCloudVerifyPath(value);
    }
  }
  state.cloudSession = next;
  renderCloud();
}

function renderCloudGuideFields(guide, cloud) {
  return guide.fields
    .map((field) => {
      const badge = field.persistent
        ? `<span class="field-badge">保存到配置</span>`
        : `<span class="field-badge session">仅当前页面</span>`;
      return `
        <div class="cloud-field">
          <label>${escapeHtml(field.label)}</label>
          <input
            type="${field.kind === "password" ? "password" : "text"}"
            value="${escapeAttr(cloud[field.key] || "")}"
            placeholder="${escapeAttr(field.placeholder || "")}"
            onchange="updateCloudSessionField('${escapeAttr(field.key)}', this.value)"
          >
          <div class="field-meta">${badge}</div>
        </div>
      `;
    })
    .join("");
}

function buildCloudPersistedConfig(cloud) {
  const guide = cloudGuideById(cloud.guide_id || defaultCloudGuideId(cloud)) || CLOUD_GUIDES[0];
  const saved = cloudSavedConfig();
  const patch = {};
  CLOUD_PERSISTED_KEYS.forEach((key) => {
    if (cloud[key] !== undefined) patch[key] = normalizeCloudValue(key, cloud[key]);
  });
  patch.enabled = Boolean(cloud.enabled);
  patch.provider = cloud.provider || guide.provider;
  patch.backend_type = cloud.backend_type || guide.backendType;
  patch.vendor = cloud.vendor || guide.vendor;
  patch.guide_id = guide.id;
  patch.guide_url = cloud.guide_url || guide.sources?.[0]?.url || "";
  patch.remote_name = normalizeCloudValue("remote_name", cloud.remote_name || "");
  patch.remote_path = normalizeCloudValue("remote_path", cloud.remote_path || "").replace(/^\/+/, "");
  patch.sync_source =
    normalizeCloudValue(
      "sync_source",
      cloud.sync_source || state.config?.restic?.repository || ""
    );
  patch.verify_path =
    normalizeCloudValue(
      "verify_path",
      cloud.verify_path || suggestCloudVerifyPath(patch.remote_path)
    );
  patch.verified_at = cloudConfigsMatch(saved, patch)
    ? normalizeCloudValue("verified_at", saved.verified_at || patch.verified_at || "")
    : "";
  return patch;
}

function cloudRemoteTarget(cloud) {
  const remoteName = normalizeCloudValue("remote_name", cloud.remote_name || "");
  const remotePath = normalizeCloudValue("remote_path", cloud.remote_path || "").replace(/^\/+/, "");
  if (!remoteName) return "";
  if (remoteName.includes(":") && !remotePath) return remoteName;
  if (remotePath) return `${remoteName}:${remotePath}`;
  return `${remoteName}:`;
}

function cloudVerifyTarget(cloud) {
  const remoteName = normalizeCloudValue("remote_name", cloud.remote_name || "");
  const verifyPath =
    normalizeCloudValue(
      "verify_path",
      cloud.verify_path || suggestCloudVerifyPath(cloud.remote_path || "")
    ).replace(/^\/+/, "");
  if (!remoteName) return "";
  if (!verifyPath) return `${remoteName}:`;
  return `${remoteName}:${verifyPath}`;
}

function cloudInstallCommand() {
  return state.profile?.kind === "windows-local"
    ? "winget install Rclone.Rclone"
    : "curl https://rclone.org/install.sh | sudo bash";
}

function cloudSecretPlaceholder(fieldKey) {
  const labels = {
    password: "<WEBDAV_PASSWORD>",
    access_key_id: "<ACCESS_KEY_ID>",
    secret_access_key: "<SECRET_ACCESS_KEY>",
    bearer_token: "<BEARER_TOKEN>",
    session_token: "<SESSION_TOKEN>",
  };
  return labels[fieldKey] || "<SESSION_SECRET>";
}

function cloudCreateCommand(guide, cloud) {
  if (guide.authType === "oauth") return "rclone config";
  const remoteName = normalizeCloudValue("remote_name", cloud.remote_name || "") || "<REMOTE_NAME>";
  const args = ["rclone", "config", "create", remoteName, guide.backendType];
  if (guide.backendType === "webdav") {
    args.push(
      "url",
      normalizeCloudValue("endpoint", cloud.endpoint || "") || "<WEBDAV_URL>",
      "vendor",
      guide.vendor || "other"
    );
    if (cloud.username) args.push("user", normalizeCloudValue("username", cloud.username));
    args.push("pass", cloudSecretPlaceholder("password"));
  } else if (guide.backendType === "s3") {
    args.push("provider", guide.vendor || "Other", "env_auth", "false");
    if (cloud.endpoint) args.push("endpoint", normalizeCloudValue("endpoint", cloud.endpoint));
    if (cloud.region) args.push("region", normalizeCloudValue("region", cloud.region));
    args.push("access_key_id", cloudSecretPlaceholder("access_key_id"));
    args.push("secret_access_key", cloudSecretPlaceholder("secret_access_key"));
  }
  return args.join(" ");
}

function cloudCheckCommand(_guide, cloud) {
  const target =
    cloudVerifyTarget(cloud) ||
    `${normalizeCloudValue("remote_name", cloud.remote_name || "") || "<REMOTE_NAME>"}:`;
  return `rclone lsd ${target}`;
}

function cloudListCommand(cloud) {
  const target =
    cloudRemoteTarget(cloud) ||
    `${normalizeCloudValue("remote_name", cloud.remote_name || "") || "<REMOTE_NAME>"}:`;
  return `rclone lsf ${target}`;
}

function cloudSyncPreviewCommand(cloud) {
  const source =
    normalizeCloudValue(
      "sync_source",
      cloud.sync_source || state.config?.restic?.repository || ""
    ) || "<LOCAL_REPOSITORY>";
  const target = cloudRemoteTarget(cloud) || "<REMOTE_NAME>:<REMOTE_PATH>";
  return `rclone sync ${source} ${target} --progress`;
}

function defaultCloudPullTarget() {
  const root = activeRestoreRoot()?.path;
  if (!root) return "";
  return `${root.replace(/\/$/, "")}/cloud-repo-${dateStamp()}`;
}

function cloudPullPreviewCommand(cloud, target) {
  const remote = cloudRemoteTarget(cloud) || "<REMOTE_NAME>:<REMOTE_PATH>";
  const localTarget = normalizeCloudValue("target", target || "") || "<LOCAL_RECOVERY_PATH>";
  return `rclone copy ${remote} ${localTarget} --progress`;
}

function cloudCheckPayload() {
  const cloud = ensureCloudSession();
  return {
    remote: cloudVerifyTarget(cloud),
  };
}

function cloudGuideReferenceCards(guide) {
  const cards = {
    "baidu-webdav-gateway": [
      {
        title: "1. 先找到网关里的 WebDAV 地址",
        where: "在你使用的 WebDAV 网关后台查看 DAV 终点地址、账号和密码。",
        detail: "这里填的是网关暴露出来的 DAV 地址，不是百度网盘网页地址。",
      },
      {
        title: "2. 远端目录建议单独留给 Restic",
        where: "在网关映射到的云盘目录里新建一个专门目录。",
        detail: "例如 `backup/restic-repo`，避免和手动上传的普通文件混在一起。",
      },
      {
        title: "3. 先列目录，再同步",
        where: "先执行本页的远端验证命令。",
        detail: "只有 `rclone lsd` 能看到目录后，再执行正式 `rclone sync`。",
      },
    ],
    "generic-webdav": [
      {
        title: "1. 确认 WebDAV 终点",
        where: "从服务商或 NAS 文档里找到标准 WebDAV URL。",
        detail: "不要填写网页登录地址；应填写 `remote.php/webdav/` 或服务商提供的 DAV 路径。",
      },
      {
        title: "2. 准备独立账号",
        where: "优先使用只给备份目录授权的账号。",
        detail: "这样即使密码泄露，影响范围也会被限制在备份目录。",
      },
      {
        title: "3. 用验证路径做首轮检查",
        where: "验证路径可填根目录，也可填上一级目录。",
        detail: "第一次建议只验证一个空目录，确认权限和路径没写反。",
      },
    ],
    "aws-s3": [
      {
        title: "1. 去 IAM 创建 Access Key",
        where: "AWS 官方文档建议在 IAM 用户的 Security credentials 页面创建访问密钥。",
        detail: "Secret Access Key 只会在创建当时显示一次，必须立刻保存到安全位置。",
      },
      {
        title: "2. 在 S3 确认 Bucket 和 Region",
        where: "从 S3 Bucket 详情页确认 bucket 名称与所在 region。",
        detail: "本页 `remote_path` 要写成 `bucket/目录` 的形式，而不是只写目录名。",
      },
      {
        title: "3. 先列 bucket",
        where: "验证路径建议先填 bucket 名称。",
        detail: "能正常列出 bucket 后，再继续同步 Restic 仓库目录。",
      },
    ],
    "alibaba-oss": [
      {
        title: "1. 去阿里云 AccessKey 管理页取 AK/SK",
        where: "从阿里云账号或 RAM 用户的 AccessKey 管理页面获取。",
        detail: "如果业务允许，更推荐使用权限收敛过的 RAM 子账号。",
      },
      {
        title: "2. 在 Bucket 页面确认 Region 和 Endpoint",
        where: "阿里云 OSS 官方文档把 Region 和 Endpoint 分开说明。",
        detail: "Bucket 详情页和 Region/Endpoint 文档都能对上这两个字段。",
      },
      {
        title: "3. 验证路径先写 bucket",
        where: "第一次验证先检查 bucket 是否可列出。",
        detail: "确认权限正常后，再把 `remote_path` 指向 bucket 下的 Restic 目录。",
      },
    ],
    "baidu-s3-gateway": [
      {
        title: "1. 先确认你拿到的是 S3 网关，不是 WebDAV",
        where: "在所用网关后台查看是否明确提供 S3 Endpoint。",
        detail: "如果只有 DAV 地址，就应切换到 WebDAV 方案，而不是硬填到 S3 字段里。",
      },
      {
        title: "2. 记录 Endpoint、AK、SK",
        where: "从网关后台复制 S3 兼容参数。",
        detail: "这些凭据通常由网关生成，不会直接来自百度网盘官方后台。",
      },
      {
        title: "3. 先验证上一级目录或 bucket",
        where: "先用本页验证命令检查目标是否能列出。",
        detail: "验证通过后，再同步加密后的 Restic 仓库。",
      },
    ],
  };
  return cards[guide.id] || [];
}

function cloudAuthLabel(authType) {
  const labels = {
    oauth: "浏览器 OAuth 授权",
    "gateway-password": "WebDAV 网关专用账号",
    "service-password": "服务商专用账号",
    "access-key": "Access Key",
    "gateway-access-key": "网关 Access Key",
  };
  return labels[authType] || "按服务商要求认证";
}

async function copyTextToClipboard(text, label) {
  try {
    await navigator.clipboard.writeText(text);
    alert(`${label}已复制。`);
  } catch (error) {
    if (window.prompt) {
      window.prompt(`请手动复制${label}`, text);
    } else {
      alert(`${label}复制失败，请手动复制。`);
    }
  }
}

function cloudCommandByType(kind) {
  const guide = selectedCloudGuide();
  const cloud = ensureCloudSession();
  const pullTarget = $("#cloudPullTarget")?.value.trim() || defaultCloudPullTarget();
  const commands = {
    install: cloudInstallCommand(),
    create: cloudCreateCommand(guide, cloud),
    check: cloudCheckCommand(guide, cloud),
    list: cloudListCommand(cloud),
    pull: cloudPullPreviewCommand(cloud, pullTarget),
    sync: cloudSyncPreviewCommand(cloud),
  };
  return commands[kind] || "";
}

async function copyCloudCommand(kind) {
  const labels = {
    install: "安装命令",
    create: "创建 remote 命令",
    check: "验证命令",
    sync: "同步命令",
  };
  const command = cloudCommandByType(kind);
  if (!command) {
    alert("当前命令还不完整，请先把必填字段补齐。");
    return;
  }
  await copyTextToClipboard(command, labels[kind] || "命令");
}

async function saveCloud() {
  const cloud = ensureCloudSession();
  await saveConfig({
    cloud_remote: buildCloudPersistedConfig(cloud),
  });
}

function cloudPayload() {
  const cloud = ensureCloudSession();
  return {
    source:
      normalizeCloudValue(
        "sync_source",
        cloud.sync_source || state.config?.restic?.repository || ""
      ),
    remote: cloudRemoteTarget(cloud),
  };
}

function renderCloud() {
  const cloud = ensureCloudSession();
  const guide = selectedCloudGuide();
  const remoteTarget = cloudRemoteTarget(cloud);
  const verifyTarget = cloudVerifyTarget(cloud);
  const verification = cloudVerificationState(cloud);
  const referenceCards = cloudGuideReferenceCards(guide);

  $("#cloud").innerHTML = `
    ${BackupWorkflow.renderStepHeader(
      "cloud",
      state.workflow,
      "把已经加密过的 Restic 仓库同步到云端，形成异地副本。不要直接上传明文业务目录。",
      [
        "先完成一次成功的 Restic 备份",
        "先确认云端服务和同步方向无误",
        "第一次正式同步前，建议先手动执行验证命令"
      ]
    )}
    <div class="band">
      <div class="section-heading">
        <div>
          <h3>云端接入向导</h3>
          <p class="muted">先选服务商接入方式，再按本页命令创建并验证 rclone remote。验证通过后，才执行异地同步。</p>
        </div>
        <label class="toggle-field">
          <span>启用云端副本</span>
          <input
            id="cloudEnabled"
            type="checkbox"
            ${cloud.enabled ? "checked" : ""}
            onchange="toggleCloudEnabled(this.checked)"
          >
        </label>
      </div>
      <div class="grid">
        <div>
          <label>服务商接入方式</label>
          <select id="cloudGuide" onchange="setCloudGuide(this.value)">
            ${CLOUD_GUIDES.map((item) => option(item.id, item.label, guide.id)).join("")}
          </select>
          ${BackupWorkflow.renderFieldHelp({
            purpose: "切换后会自动更新字段要求、操作说明和命令预览。",
            example: guide.label,
            format:
              guide.authType === "oauth"
                ? "OAuth 服务商通过 rclone config 在官方页面授权，本应用不接收网页登录密码。"
                : "WebDAV 或 S3 方案应使用服务专用凭据，不要填写网盘网页登录密码。",
          })}
        </div>
        <div>
          <label>本地同步源</label>
          <input
            id="cloudSource"
            value="${escapeAttr(cloud.sync_source || "")}"
            placeholder="/Gensol/_cloud_restic/restic-repo"
            onchange="updateCloudSessionField('sync_source', this.value)"
          >
          ${BackupWorkflow.renderFieldHelp({
            purpose: "这里应当填写 Restic 仓库目录，而不是原始共享目录。",
            example: "/Gensol/_cloud_restic/restic-repo",
            format: "建议直接使用你已经验证过的 Restic 仓库路径。",
            safety: "不要把 SMB 共享根目录直接同步到云端，否则会把明文文件暴露出去。",
          })}
        </div>
        <div>
          <label>目标 remote 预览</label>
          <input value="${escapeAttr(remoteTarget || "尚未形成 remote:path")}" readonly>
          <p class="muted">这是最终执行 rclone sync 时使用的远端目标。</p>
        </div>
      </div>
      <div class="guide-callout ${guide.warning ? "danger-note" : "warn"}">
        <div class="guide-callout-head">
          <strong>${escapeHtml(guide.label)}</strong>
          <span class="cloud-auth-badge">认证方式 · ${escapeHtml(cloudAuthLabel(guide.authType))}</span>
        </div>
        <p>${escapeHtml(guide.summary)}</p>
        ${
          guide.warning
            ? `<p class="field-safety">${escapeHtml(guide.warning)}</p>`
            : ""
        }
      </div>
      <div class="verification-status ${escapeAttr(verification.tone)}">
        <strong>${escapeHtml(verification.label)}</strong>
        <span>${escapeHtml(verification.detail)}</span>
      </div>
      <div class="guide-flow">
        ${guide.visual
          .map(
            (item, index) => `
              <div class="guide-step">
                <span class="guide-step-number">${index + 1}</span>
                <span>${escapeHtml(item)}</span>
              </div>
            `
          )
          .join("")}
      </div>
      <div class="grid top-gap">
        ${renderCloudGuideFields(guide, cloud)}
      </div>
      ${
        referenceCards.length
          ? `
            <div class="reference-card-grid top-gap">
              ${referenceCards
                .map(
                  (card) => `
                    <article class="reference-card">
                      <h4>${escapeHtml(card.title)}</h4>
                      <p><strong>去哪里看：</strong>${escapeHtml(card.where)}</p>
                      <p>${escapeHtml(card.detail)}</p>
                    </article>
                  `
                )
                .join("")}
            </div>
          `
          : ""
      }
      <div class="grid top-gap">
        <div>
          <label>说明备注</label>
          <textarea
            id="cloudNotes"
            placeholder="例如：这个 remote 对应哪个账号、哪个网关、是否只用于异地副本"
            onchange="updateCloudSessionField('notes', this.value)"
          >${escapeHtml(cloud.notes || "")}</textarea>
        </div>
        <div>
          <label>验证目标预览</label>
          <input value="${escapeAttr(verifyTarget || "尚未形成验证路径")}" readonly>
          <p class="muted">建议先对上一级目录或 bucket 做 rclone lsd 验证，再执行正式同步。</p>
        </div>
      </div>
      <div class="session-only-note">
        <strong>敏感字段只保留在当前页面内存中。</strong>
        <span>刷新页面后会自动清空，不会写入配置文件、任务日志或命令历史。命令预览只显示占位符。</span>
      </div>
      <div class="actions">
        <button onclick="saveCloud()">保存云端配置</button>
        <button class="secondary" onclick="copyCloudCommand('create')">复制创建 remote 命令</button>
        <button class="secondary" onclick="copyCloudCommand('check')">复制验证命令</button>
        <button class="secondary" onclick="runOperation('cloud-rclone-check', cloudCheckPayload())">执行远端验证</button>
        <button class="secondary" onclick="runOperation('cloud-rclone-sync', cloudPayload())">执行同步</button>
      </div>
    </div>
    <div class="band">
      <h3>当前这一步怎么做</h3>
      <ol class="instruction-list">
        ${guide.steps.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
      </ol>
      <div class="cloud-success-criteria">
        <strong>成功标准</strong>
        <span>${escapeHtml(guide.successCriteria)}</span>
      </div>
      <div class="cloud-troubleshooting">
        ${guide.troubleshooting
          .map(
            (item) => `
              <div class="cloud-troubleshooting-item">
                <strong>${escapeHtml(item.problem)}</strong>
                <span>${escapeHtml(item.fix)}</span>
              </div>
            `
          )
          .join("")}
      </div>
      <div class="guide-source-list">
        ${guide.sources
          .map(
            (item) =>
              `<a href="${escapeAttr(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.label)}</a>`
          )
          .join("")}
      </div>
    </div>
    <div class="band">
      <h3>命令预览</h3>
      <div class="cloud-command-grid">
        <div class="cloud-command-card">
          <div class="command-card-head">
            <strong>1. 安装 rclone</strong>
            <button class="secondary compact" onclick="copyCloudCommand('install')">复制</button>
          </div>
          <pre>${escapeHtml(cloudInstallCommand())}</pre>
        </div>
        <div class="cloud-command-card">
          <div class="command-card-head">
            <strong>2. 创建 remote</strong>
            <button class="secondary compact" onclick="copyCloudCommand('create')">复制</button>
          </div>
          <pre>${escapeHtml(cloudCreateCommand(guide, cloud))}</pre>
        </div>
        <div class="cloud-command-card">
          <div class="command-card-head">
            <strong>3. 验证远端</strong>
            <button class="secondary compact" onclick="copyCloudCommand('check')">复制</button>
          </div>
          <pre>${escapeHtml(cloudCheckCommand(guide, cloud))}</pre>
        </div>
        <div class="cloud-command-card">
          <div class="command-card-head">
            <strong>4. 同步 Restic 仓库</strong>
            <button class="secondary compact" onclick="copyCloudCommand('sync')">复制</button>
          </div>
          <pre>${escapeHtml(cloudSyncPreviewCommand(cloud))}</pre>
        </div>
      </div>
    </div>
    <div class="card">
      <h3>最近一次远端验证</h3>
      ${renderLatestOperationCard("cloud-rclone-check", "还没有执行过远端验证。")}
    </div>
    <div class="card">
      <h3>最近一次云端同步</h3>
      ${renderLatestOperationCard("cloud-rclone-sync", "还没有执行过云端同步。")}
    </div>
    ${BackupWorkflow.renderStepFooter("cloud", state.workflow)}
  `;
}

function cloudCommandByType(kind) {
  const guide = selectedCloudGuide();
  const cloud = ensureCloudSession();
  const pullTarget = $("#cloudPullTarget")?.value.trim() || defaultCloudPullTarget();
  const commands = {
    install: cloudInstallCommand(),
    create: cloudCreateCommand(guide, cloud),
    check: cloudCheckCommand(guide, cloud),
    list: cloudListCommand(cloud),
    pull: cloudPullPreviewCommand(cloud, pullTarget),
    sync: cloudSyncPreviewCommand(cloud),
  };
  return commands[kind] || "";
}

async function copyCloudCommand(kind) {
  const labels = {
    install: "安装命令",
    create: "创建 remote 命令",
    check: "验证命令",
    list: "列目录命令",
    pull: "拉回仓库命令",
    sync: "同步命令",
  };
  const command = cloudCommandByType(kind);
  if (!command) {
    alert("当前命令还不完整，请先把必填字段补齐。");
    return;
  }
  await copyTextToClipboard(command, labels[kind] || "命令");
}

function cloudListPayload() {
  const cloud = ensureCloudSession();
  return {
    remote: cloudRemoteTarget(cloud),
  };
}

function cloudPullPayload() {
  const cloud = ensureCloudSession();
  return {
    remote: cloudRemoteTarget(cloud),
    target: $("#cloudPullTarget")?.value.trim() || defaultCloudPullTarget(),
  };
}

function renderCloud() {
  const cloud = ensureCloudSession();
  const guide = selectedCloudGuide();
  const remoteTarget = cloudRemoteTarget(cloud);
  const verifyTarget = cloudVerifyTarget(cloud);
  const verification = cloudVerificationState(cloud);
  const referenceCards = cloudGuideReferenceCards(guide);
  const pullTarget = $("#cloudPullTarget")?.value.trim() || defaultCloudPullTarget();

  $("#cloud").innerHTML = `
    ${BackupWorkflow.renderStepHeader(
      "cloud",
      state.workflow,
      "把已经加密过的 Restic 仓库同步到云端，形成异地副本。不要直接上传明文业务目录。",
      [
        "先完成一次成功的 Restic 备份",
        "先确认云端服务和同步方向无误",
        "第一次正式同步前，建议先手动执行验证命令"
      ]
    )}
    <div class="band">
      <div class="section-heading">
        <div>
          <h3>云端接入向导</h3>
          <p class="muted">先选服务商接入方式，再按本页命令创建并验证 rclone remote。验证通过后，才执行异地同步。</p>
        </div>
        <label class="toggle-field">
          <span>启用云端副本</span>
          <input
            id="cloudEnabled"
            type="checkbox"
            ${cloud.enabled ? "checked" : ""}
            onchange="toggleCloudEnabled(this.checked)"
          >
        </label>
      </div>
      <div class="grid">
        <div>
          <label>服务商接入方式</label>
          <select id="cloudGuide" onchange="setCloudGuide(this.value)">
            ${CLOUD_GUIDES.map((item) => option(item.id, item.label, guide.id)).join("")}
          </select>
          ${BackupWorkflow.renderFieldHelp({
            purpose: "切换后会自动更新字段要求、操作说明和命令预览。",
            example: guide.label,
            format:
              guide.authType === "oauth"
                ? "OAuth 服务商通过 rclone config 在官方页面授权，本应用不接收网页登录密码。"
                : "WebDAV 或 S3 方案应使用服务专用凭据，不要填写网盘网页登录密码。",
          })}
        </div>
        <div>
          <label>本地同步源</label>
          <input
            id="cloudSource"
            value="${escapeAttr(cloud.sync_source || "")}"
            placeholder="/Gensol/_cloud_restic/restic-repo"
            onchange="updateCloudSessionField('sync_source', this.value)"
          >
          ${BackupWorkflow.renderFieldHelp({
            purpose: "这里应当填写 Restic 仓库目录，而不是原始共享目录。",
            example: "/Gensol/_cloud_restic/restic-repo",
            format: "建议直接使用你已经验证过的 Restic 仓库路径。",
            safety: "不要把 SMB 共享根目录直接同步到云端，否则会把明文文件暴露出去。",
          })}
        </div>
        <div>
          <label>目标 remote 预览</label>
          <input value="${escapeAttr(remoteTarget || "尚未形成 remote:path")}" readonly>
          <p class="muted">这是最终执行 rclone sync 时使用的远端目标。</p>
        </div>
      </div>
      <div class="guide-callout ${guide.warning ? "danger-note" : "warn"}">
        <div class="guide-callout-head">
          <strong>${escapeHtml(guide.label)}</strong>
          <span class="cloud-auth-badge">认证方式 · ${escapeHtml(cloudAuthLabel(guide.authType))}</span>
        </div>
        <p>${escapeHtml(guide.summary)}</p>
        ${
          guide.warning
            ? `<p class="field-safety">${escapeHtml(guide.warning)}</p>`
            : ""
        }
      </div>
      <div class="verification-status ${escapeAttr(verification.tone)}">
        <strong>${escapeHtml(verification.label)}</strong>
        <span>${escapeHtml(verification.detail)}</span>
      </div>
      <div class="guide-flow">
        ${guide.visual
          .map(
            (item, index) => `
              <div class="guide-step">
                <span class="guide-step-number">${index + 1}</span>
                <span>${escapeHtml(item)}</span>
              </div>
            `
          )
          .join("")}
      </div>
      <div class="grid top-gap">
        ${renderCloudGuideFields(guide, cloud)}
      </div>
      ${
        referenceCards.length
          ? `
            <div class="reference-card-grid top-gap">
              ${referenceCards
                .map(
                  (card) => `
                    <article class="reference-card">
                      <h4>${escapeHtml(card.title)}</h4>
                      <p><strong>去哪里看：</strong>${escapeHtml(card.where)}</p>
                      <p>${escapeHtml(card.detail)}</p>
                    </article>
                  `
                )
                .join("")}
            </div>
          `
          : ""
      }
      <div class="grid top-gap">
        <div>
          <label>说明备注</label>
          <textarea
            id="cloudNotes"
            placeholder="例如：这个 remote 对应哪个账号、哪个网关、是否只用于异地副本"
            onchange="updateCloudSessionField('notes', this.value)"
          >${escapeHtml(cloud.notes || "")}</textarea>
        </div>
        <div>
          <label>验证目标预览</label>
          <input value="${escapeAttr(verifyTarget || "尚未形成验证路径")}" readonly>
          <p class="muted">建议先对上一级目录或 bucket 做 rclone lsd 验证，再执行正式同步。</p>
        </div>
      </div>
      <div class="grid top-gap">
        <div>
          <label>云端恢复拉回路径</label>
          <input
            id="cloudPullTarget"
            value="${escapeAttr(pullTarget)}"
            placeholder="/ExamplePool/.backup-manager/restore/cloud-repo-20260624"
          >
          ${BackupWorkflow.renderFieldHelp({
            purpose: "把云端里的加密 Restic 仓库先拉回到本地数据盘，再交给恢复中心继续恢复文件。",
            example: "/ExamplePool/.backup-manager/restore/cloud-repo-20260624",
            format: "必须是 Linux 绝对路径，且不要填 /tmp、/var 这类系统盘路径。",
            safety: "拉回的只是加密仓库，不是最终业务文件；后续仍需用 Restic 恢复到目标目录。",
          })}
        </div>
        <div>
          <label>云端恢复怎么用</label>
          <div class="cloud-restore-guide">
            <p>1. 先执行远端验证。</p>
            <p>2. 再列一次远端目录，确认仓库文件确实存在。</p>
            <p>3. 用“拉回云端仓库”把加密仓库复制到本地恢复目录。</p>
            <p>4. 最后在恢复中心里把 Restic 仓库指向这份本地副本继续恢复。</p>
          </div>
        </div>
      </div>
      <div class="session-only-note">
        <strong>敏感字段只保留在当前页面内存中。</strong>
        <span>刷新页面后会自动清空，不会写入配置文件、任务日志或命令历史。命令预览只显示占位符。</span>
      </div>
      <div class="actions">
        <button onclick="saveCloud()">保存云端配置</button>
        <button class="secondary" onclick="copyCloudCommand('create')">复制创建 remote 命令</button>
        <button class="secondary" onclick="copyCloudCommand('check')">复制验证命令</button>
        <button class="secondary" onclick="runOperation('cloud-rclone-check', cloudCheckPayload())">执行远端验证</button>
        <button class="secondary" onclick="runOperation('cloud-rclone-list', cloudListPayload())">列出远端目录</button>
        <button class="secondary" onclick="runOperation('cloud-rclone-pull', cloudPullPayload())">拉回云端仓库</button>
        <button class="secondary" onclick="runOperation('cloud-rclone-sync', cloudPayload())">执行同步</button>
      </div>
    </div>
    <div class="band">
      <h3>当前这一步怎么做</h3>
      <ol class="instruction-list">
        ${guide.steps.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
      </ol>
      <div class="cloud-success-criteria">
        <strong>成功标准</strong>
        <span>${escapeHtml(guide.successCriteria)}</span>
      </div>
      <div class="cloud-troubleshooting">
        ${guide.troubleshooting
          .map(
            (item) => `
              <div class="cloud-troubleshooting-item">
                <strong>${escapeHtml(item.problem)}</strong>
                <span>${escapeHtml(item.fix)}</span>
              </div>
            `
          )
          .join("")}
      </div>
      <div class="guide-source-list">
        ${guide.sources
          .map(
            (item) =>
              `<a href="${escapeAttr(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.label)}</a>`
          )
          .join("")}
      </div>
    </div>
    <div class="band">
      <h3>命令预览</h3>
      <div class="cloud-command-grid">
        <div class="cloud-command-card">
          <div class="command-card-head">
            <strong>1. 安装 rclone</strong>
            <button class="secondary compact" onclick="copyCloudCommand('install')">复制</button>
          </div>
          <pre>${escapeHtml(cloudInstallCommand())}</pre>
        </div>
        <div class="cloud-command-card">
          <div class="command-card-head">
            <strong>2. 创建 remote</strong>
            <button class="secondary compact" onclick="copyCloudCommand('create')">复制</button>
          </div>
          <pre>${escapeHtml(cloudCreateCommand(guide, cloud))}</pre>
        </div>
        <div class="cloud-command-card">
          <div class="command-card-head">
            <strong>3. 验证远端</strong>
            <button class="secondary compact" onclick="copyCloudCommand('check')">复制</button>
          </div>
          <pre>${escapeHtml(cloudCheckCommand(guide, cloud))}</pre>
        </div>
        <div class="cloud-command-card">
          <div class="command-card-head">
            <strong>4. 同步 Restic 仓库</strong>
            <button class="secondary compact" onclick="copyCloudCommand('sync')">复制</button>
          </div>
          <pre>${escapeHtml(cloudSyncPreviewCommand(cloud))}</pre>
        </div>
        <div class="cloud-command-card">
          <div class="command-card-head">
            <strong>5. 列远端目录</strong>
            <button class="secondary compact" onclick="copyCloudCommand('list')">复制</button>
          </div>
          <pre>${escapeHtml(cloudListCommand(cloud))}</pre>
        </div>
        <div class="cloud-command-card">
          <div class="command-card-head">
            <strong>6. 拉回云端仓库</strong>
            <button class="secondary compact" onclick="copyCloudCommand('pull')">复制</button>
          </div>
          <pre>${escapeHtml(cloudPullPreviewCommand(cloud, pullTarget))}</pre>
        </div>
      </div>
    </div>
    <div class="card">
      <h3>最近一次远端验证</h3>
      ${renderLatestOperationCard("cloud-rclone-check", "还没有执行过远端验证。")}
    </div>
    <div class="card">
      <h3>最近一次远端列目录</h3>
      ${renderLatestOperationCard("cloud-rclone-list", "还没有执行过远端目录检测。")}
    </div>
    <div class="card">
      <h3>最近一次云端恢复拉回</h3>
      ${renderLatestOperationCard("cloud-rclone-pull", "还没有从云端拉回过加密仓库。")}
    </div>
    <div class="card">
      <h3>最近一次云端同步</h3>
      ${renderLatestOperationCard("cloud-rclone-sync", "还没有执行过云端同步。")}
    </div>
    ${BackupWorkflow.renderStepFooter("cloud", state.workflow)}
  `;
}

function option(value, label, current) {
  return `<option value="${escapeAttr(value)}" ${
    value === current ? "selected" : ""
  }>${escapeHtml(label)}</option>`;
}

function dateStamp() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}${month}${day}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}

// ─── Device Management (Sprint002) ───────────────────────
state.devices = [];
state.deviceEditing = null; // null = list view, object = editing

async function loadDevices() {
  try {
    const resp = await api("/api/devices");
    state.devices = resp.devices || [];
  } catch (e) {
    state.devices = [];
  }
}

function renderDevices() {
  const el = document.getElementById("devices");
  if (!el) return;

  if (state.deviceEditing) {
    renderDeviceForm(el);
    return;
  }

  const t = WorkOps.t;
  const devices = state.devices || [];

  const rows = devices.map(d => `
    <tr>
      <td>${escapeHtml(d.name)}</td>
      <td>${escapeHtml(t("devices.type." + d.type) || d.type)}</td>
      <td>${escapeHtml(d.ip || "-")}</td>
      <td><span class="status-chip status-${escapeAttr(d.status)}">${escapeHtml(t("devices.status." + d.status) || d.status)}</span></td>
      <td>
        <button class="secondary compact" onclick="editDevice('${escapeAttr(d.id)}')">${escapeHtml(t("btn.edit") || "编辑")}</button>
        <button class="danger compact" onclick="deleteDevice('${escapeAttr(d.id)}')">${escapeHtml(t("btn.delete") || "删除")}</button>
      </td>
    </tr>
  `).join("");

  el.innerHTML = `
    <div class="band">
      <div class="section-heading">
        <h2>${escapeHtml(t("devices.title"))}</h2>
        <button onclick="addDevice()">${escapeHtml(t("devices.add"))}</button>
      </div>
      ${devices.length ? `
        <table class="inventory-table">
          <thead>
            <tr>
              <th>${escapeHtml(t("devices.name"))}</th>
              <th>${escapeHtml(t("devices.type"))}</th>
              <th>${escapeHtml(t("devices.ip"))}</th>
              <th>${escapeHtml(t("devices.status"))}</th>
              <th>${escapeHtml(t("devices.actions"))}</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      ` : `<p class="muted">${escapeHtml(t("devices.empty"))}</p>`}
    </div>
  `;
}

function renderDeviceForm(el) {
  const t = WorkOps.t;
  const d = state.deviceEditing;
  const isNew = !d.id;
  const title = isNew ? t("devices.add") : t("devices.edit");

  const typeOptions = ["windows", "linux", "omv", "pve", "pbs", "nas", "router", "other"]
    .map(v => `<option value="${v}" ${d.type === v ? "selected" : ""}>${escapeHtml(t("devices.type." + v))}</option>`)
    .join("");

  const statusOptions = ["online", "offline", "unknown"]
    .map(v => `<option value="${v}" ${d.status === v ? "selected" : ""}>${escapeHtml(t("devices.status." + v))}</option>`)
    .join("");

  el.innerHTML = `
    <div class="band">
      <div class="section-heading">
        <h2>${escapeHtml(title)}</h2>
        <button class="secondary" onclick="cancelDeviceEdit()">${escapeHtml(t("btn.cancel"))}</button>
      </div>
      <div class="grid">
        <div>
          <label>${escapeHtml(t("devices.name"))}</label>
          <input id="deviceName" value="${escapeAttr(d.name || "")}" placeholder="Windows-PC">
        </div>
        <div>
          <label>${escapeHtml(t("devices.type"))}</label>
          <select id="deviceType">${typeOptions}</select>
        </div>
        <div>
          <label>${escapeHtml(t("devices.ip"))}</label>
          <input id="deviceIp" value="${escapeAttr(d.ip || "")}" placeholder="192.168.1.100">
        </div>
        <div>
          <label>${escapeHtml(t("devices.status"))}</label>
          <select id="deviceStatus">${statusOptions}</select>
        </div>
      </div>
      <label>${escapeHtml(t("devices.description"))}</label>
      <textarea id="deviceDesc">${escapeHtml(d.description || "")}</textarea>
      <div class="actions">
        <button onclick="saveDevice()">${escapeHtml(t("btn.save"))}</button>
      </div>
    </div>
  `;
}

function addDevice() {
  state.deviceEditing = { name: "", type: "windows", ip: "", status: "offline", description: "" };
  renderDevices();
}

function editDevice(id) {
  const d = state.devices.find(x => x.id === id);
  if (d) {
    state.deviceEditing = { ...d };
    renderDevices();
  }
}

function cancelDeviceEdit() {
  state.deviceEditing = null;
  renderDevices();
}

async function saveDevice() {
  const d = state.deviceEditing;
  if (!d) return;

  const data = {
    name: document.getElementById("deviceName").value.trim(),
    type: document.getElementById("deviceType").value,
    ip: document.getElementById("deviceIp").value.trim(),
    status: document.getElementById("deviceStatus").value,
    description: document.getElementById("deviceDesc").value.trim(),
  };

  if (!data.name) {
    alert(WorkOps.t("devices.name") + " is required");
    return;
  }

  try {
    if (d.id) {
      await api(`/api/devices/${d.id}`, { method: "PUT", body: JSON.stringify(data) });
    } else {
      await api("/api/devices", { method: "POST", body: JSON.stringify(data) });
    }
    state.deviceEditing = null;
    await loadDevices();
    renderDevices();
    notify("success", d.id ? "设备已更新" : "设备已添加");
  } catch (e) {
    notify("error", "保存失败", e.message);
  }
}

async function deleteDevice(id) {
  if (!confirm(WorkOps.t("devices.confirmDelete"))) return;
  try {
    await api(`/api/devices/${id}`, { method: "DELETE" });
    await loadDevices();
    renderDevices();
    notify("success", "设备已删除");
  } catch (e) {
    notify("error", "删除失败", e.message);
  }
}

init().catch((error) => {
  document.body.innerHTML = `<pre>${escapeHtml(error.stack || error.message)}</pre>`;
});
