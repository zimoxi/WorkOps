import json
import subprocess
import textwrap
import unittest
from pathlib import Path


class FrontendCloudTests(unittest.TestCase):
    def test_cloud_helpers_build_remote_target_and_strip_session_secrets(self):
        repo = Path(__file__).resolve().parents[1]
        script = textwrap.dedent(
            """
            const fs = require("fs");
            const vm = require("vm");
            const path = require("path");

            const source = fs
              .readFileSync(path.join(process.cwd(), "static", "app.js"), "utf8")
              .replace(/init\\(\\)\\.catch\\([\\s\\S]*?\\);\\s*$/, "");

            function makeElement() {
              return {
                innerHTML: "",
                value: "",
                textContent: "",
                returnValue: "",
                addEventListener() {},
                showModal() {},
                close() {},
                classList: { toggle() {} },
              };
            }

            const elements = new Map();
            const document = {
              querySelector(selector) {
                if (!elements.has(selector)) elements.set(selector, makeElement());
                return elements.get(selector);
              },
              querySelectorAll() {
                return [];
              },
              body: makeElement(),
            };

            const context = {
              console,
              document,
              window: {},
              alert() {},
              navigator: { clipboard: { writeText: async () => {} } },
              BackupWorkflow: {
                renderStepHeader: () => "",
                renderFieldHelp: (options) =>
                  `<div>示例： ${options.example || ""} 格式： ${options.format || ""}</div>`,
                renderStepFooter: () => "",
              },
              fetch: async () => ({
                ok: true,
                json: async () => ({
                  config: {},
                  jobs: [],
                  workflow: { steps: [] },
                  profile: {},
                  capabilities: {},
                  inventory: { storage: {} },
                }),
              }),
              setTimeout,
              clearTimeout,
              Date,
            };

            vm.createContext(context);
            vm.runInContext(
              source +
                "\\n;globalThis.__appExports = {" +
                "state," +
                "CLOUD_GUIDES," +
                "cloudGuideById," +
                "cloudRemoteTarget," +
                "buildCloudPersistedConfig," +
                "cloudCreateCommand," +
                "cloudCheckCommand," +
                "cloudVerificationState," +
                "cloudListCommand," +
                "cloudPullPreviewCommand," +
                "operationStep," +
                "setCloudGuide," +
                "renderCloud" +
                "};",
              context
            );

            const app = context.__appExports;
            const guide = app.cloudGuideById("baidu-webdav-gateway");
            const oneDriveGuide = app.cloudGuideById("microsoft-onedrive");
            const googleDriveGuide = app.cloudGuideById("google-drive");
            app.state.config = {
              restic: {
                repository: "/Gensol/_cloud_restic/repo",
              },
              cloud_remote: {
                guide_id: "baidu-webdav-gateway",
                provider: "baidu",
                backend_type: "webdav",
                vendor: "other",
                remote_name: "baidu-alist",
                remote_path: "backup/restic",
                endpoint: "https://alist.example.com/dav/",
                username: "demo-user",
                verify_path: "backup",
                verified_at: "2026-06-24T10:00:00",
                sync_source: "/Gensol/_cloud_restic/repo",
              },
            };
            const cloud = {
              guide_id: "baidu-webdav-gateway",
              provider: "baidu",
              backend_type: "webdav",
              vendor: "other",
              remote_name: "baidu-alist",
              remote_path: "backup/restic",
              endpoint: "https://alist.example.com/dav/",
              username: "demo-user",
              password: "session-secret",
              access_key_id: "AKIA-TRANSIENT",
              secret_access_key: "secret-transient",
              verify_path: "backup",
              sync_source: "/Gensol/_cloud_restic/repo",
            };
            const changedCloud = {
              ...cloud,
              remote_path: "backup/restic-v2",
            };
            app.state.cloudSession = { ...cloud, enabled: true };
            app.renderCloud();
            const cloudHtml = elements.get("#cloud").innerHTML;
            app.setCloudGuide("microsoft-onedrive");
            const oneDriveHtml = elements.get("#cloud").innerHTML;
            app.setCloudGuide("google-drive");
            const googleDriveHtml = elements.get("#cloud").innerHTML;

            console.log(
              JSON.stringify({
                hasGuide: Boolean(guide),
                target: app.cloudRemoteTarget(cloud),
                patch: app.buildCloudPersistedConfig(cloud),
                changedPatch: app.buildCloudPersistedConfig(changedCloud),
                create: app.cloudCreateCommand(guide, cloud),
                check: app.cloudCheckCommand(guide, cloud),
                verification: app.cloudVerificationState(changedCloud),
                list: app.cloudListCommand(cloud),
                pull: app.cloudPullPreviewCommand(cloud, "/restore/cloud-repo"),
                listStep: app.operationStep("cloud-rclone-list"),
                pullStep: app.operationStep("cloud-rclone-pull"),
                oneDrive: oneDriveGuide
                  ? {
                      authType: oneDriveGuide.authType,
                      passwordFields: oneDriveGuide.fields.filter(
                        (field) => field.kind === "password"
                      ).length,
                      create: app.cloudCreateCommand(oneDriveGuide, {
                        remote_name: "office-drive",
                      }),
                    }
                  : null,
                googleDrive: googleDriveGuide
                  ? {
                      authType: googleDriveGuide.authType,
                      passwordFields: googleDriveGuide.fields.filter(
                        (field) => field.kind === "password"
                      ).length,
                      create: app.cloudCreateCommand(googleDriveGuide, {
                        remote_name: "google-drive",
                      }),
                    }
                  : null,
                guideQuality: app.CLOUD_GUIDES.map((item) => ({
                  id: item.id,
                  successCriteria: item.successCriteria || "",
                  troubleshootingCount: Array.isArray(item.troubleshooting)
                    ? item.troubleshooting.length
                    : 0,
                })),
                cloudHtml,
                oneDriveHtml,
                googleDriveHtml,
              })
            );
            """
        )

        result = subprocess.run(
            ["node", "-e", script],
            cwd=repo,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["hasGuide"])
        self.assertEqual(payload["target"], "baidu-alist:backup/restic")
        self.assertEqual(payload["patch"]["guide_id"], "baidu-webdav-gateway")
        self.assertEqual(payload["patch"]["endpoint"], "https://alist.example.com/dav/")
        self.assertNotIn("password", payload["patch"])
        self.assertNotIn("access_key_id", payload["patch"])
        self.assertNotIn("secret_access_key", payload["patch"])
        self.assertIn("rclone config create baidu-alist webdav", payload["create"])
        self.assertIn("rclone lsd baidu-alist:backup", payload["check"])
        self.assertEqual(payload["patch"]["verified_at"], "2026-06-24T10:00:00")
        self.assertEqual(payload["changedPatch"]["verified_at"], "")
        self.assertEqual(payload["verification"]["tone"], "warning")
        self.assertIn("rclone lsf baidu-alist:backup/restic", payload["list"])
        self.assertIn(
            "rclone copy baidu-alist:backup/restic /restore/cloud-repo --progress",
            payload["pull"],
        )
        self.assertEqual(payload["listStep"], "cloud")
        self.assertEqual(payload["pullStep"], "cloud")
        self.assertIsNotNone(payload["oneDrive"], "缺少 Microsoft OneDrive 接入向导")
        self.assertIsNotNone(payload["googleDrive"], "缺少 Google Drive 接入向导")
        self.assertEqual(payload["oneDrive"]["authType"], "oauth")
        self.assertEqual(payload["oneDrive"]["passwordFields"], 0)
        self.assertEqual(payload["oneDrive"]["create"], "rclone config")
        self.assertEqual(payload["googleDrive"]["authType"], "oauth")
        self.assertEqual(payload["googleDrive"]["passwordFields"], 0)
        self.assertEqual(payload["googleDrive"]["create"], "rclone config")
        for guide in payload["guideQuality"]:
            self.assertTrue(
                guide["successCriteria"],
                f"{guide['id']} 缺少完成标准",
            )
            self.assertGreaterEqual(
                guide["troubleshootingCount"],
                2,
                f"{guide['id']} 至少需要两条常见错误处理说明",
            )
        self.assertIn("认证方式", payload["cloudHtml"])
        self.assertIn("WebDAV 网关专用账号", payload["cloudHtml"])
        self.assertIn("成功标准", payload["cloudHtml"])
        self.assertIn("401 或用户名密码错误", payload["cloudHtml"])
        self.assertIn("浏览器 OAuth 授权", payload["oneDriveHtml"])
        self.assertIn("rclone config", payload["oneDriveHtml"])
        self.assertIn("示例： Microsoft OneDrive", payload["oneDriveHtml"])
        self.assertNotIn("示例： 百度网盘（WebDAV 网关）", payload["oneDriveHtml"])
        self.assertNotIn('type="password"', payload["oneDriveHtml"])
        self.assertIn("浏览器 OAuth 授权", payload["googleDriveHtml"])
        self.assertIn("rclone config", payload["googleDriveHtml"])
        self.assertNotIn('type="password"', payload["googleDriveHtml"])


if __name__ == "__main__":
    unittest.main()
