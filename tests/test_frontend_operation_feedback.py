import json
import subprocess
import textwrap
import unittest
from pathlib import Path


class FrontendOperationFeedbackTests(unittest.TestCase):
    def run_node(self, script):
        repo = Path(__file__).resolve().parents[1]
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
        return json.loads(result.stdout)

    def base_script(self, extra_js):
        return textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const path = require("path");

            const source = fs
              .readFileSync(path.join(process.cwd(), "static", "app.js"), "utf8")
              .replace(/init\\(\\)\\.catch\\([\\s\\S]*?\\);\\s*$/, "");

            function makeElement() {{
              return {{
                innerHTML: "",
                value: "",
                textContent: "",
                returnValue: "",
                dataset: {{}},
                addEventListener() {{}},
                showModal() {{}},
                close() {{}},
                remove() {{}},
                appendChild() {{}},
                classList: {{
                  add() {{}},
                  remove() {{}},
                  toggle() {{}},
                }},
              }};
            }}

            const elements = new Map();
            elements.set("#operationStatusRegion", makeElement());

            const document = {{
              querySelector(selector) {{
                if (!elements.has(selector)) elements.set(selector, makeElement());
                return elements.get(selector);
              }},
              querySelectorAll() {{
                return [];
              }},
              createElement() {{
                return makeElement();
              }},
              body: makeElement(),
            }};

            const context = {{
              console,
              elements,
              document,
              window: {{}},
              alert() {{}},
              navigator: {{ clipboard: {{ writeText: async () => {{}} }} }},
              BackupWorkflow: {{
                STEP_PAGES: {{ pve_pbs: "pve", connect: "storage" }},
                stepById: () => ({{ title: "PVE / PBS" }}),
                renderOverview: () => "",
                renderStepHeader: () => "",
                renderFieldHelp: () => "",
                renderStepFooter: () => "",
              }},
              setTimeout: (fn) => {{
                fn();
                return 1;
              }},
              clearTimeout() {{}},
              Date,
            }};

            vm.createContext(context);
            vm.runInContext(source + `\\n{extra_js}`, context);
            """
        )

    def test_feedback_region_renders_notifications_and_progress(self):
        payload = self.run_node(
            self.base_script(
                """
                globalThis.__appExports = {
                  state,
                  notify,
                  renderOperationStatusRegion,
                  extractOperationProgress,
                  trackActiveJob,
                };
                const app = globalThis.__appExports;
                app.notify("info", "Saved", "Config written");
                app.trackActiveJob({
                  id: "job-running",
                  operation_id: "pve-list-guests",
                  title: "List PVE guests",
                  started_at: "2026-06-25T10:00:00",
                  finished_at: "",
                  status: "running",
                  returncode: null,
                  stdout: "",
                  stderr: "",
                  step_id: "pve_pbs",
                });
                const progress = app.extractOperationProgress({
                  id: "job-done",
                  status: "success",
                  stdout: "Transferred: 128 MiB / 256 MiB, 50%, 4 MiB/s",
                  stderr: "",
                  metadata: {},
                });
                app.renderOperationStatusRegion();
                console.log(JSON.stringify({
                  html: elements.get("#operationStatusRegion").innerHTML,
                  progress,
                }));
                """
            )
        )

        self.assertEqual(payload["progress"]["percent"], 50)
        self.assertIn("Saved", payload["html"])
        self.assertIn("Config written", payload["html"])
        self.assertIn("List PVE guests", payload["html"])
        self.assertIn("running", payload["html"])

    def test_run_operation_submits_async_and_tracks_completion(self):
        payload = self.run_node(
            self.base_script(
                """
                const calls = [];
                globalThis.fetch = async (requestPath, options = {}) => {
                  calls.push({
                    path: requestPath,
                    body: options.body ? JSON.parse(options.body) : null,
                  });
                  if (requestPath === "/api/prepare") {
                    return {
                      ok: true,
                      json: async () => ({
                        command: {
                          id: "pve-list-guests",
                          title: "List PVE guests",
                          argv: ["sh", "-lc", "qm list"],
                          confirm_text: "",
                        },
                      }),
                    };
                  }
                  if (requestPath === "/api/run") {
                    return {
                      ok: true,
                      status: 202,
                      json: async () => ({
                        async: true,
                        job: {
                          id: "job-test",
                          operation_id: "pve-list-guests",
                          title: "List PVE guests",
                          started_at: "2026-06-25T10:00:00",
                          finished_at: "",
                          status: "running",
                          returncode: null,
                          stdout: "",
                          stderr: "",
                          step_id: "pve_pbs",
                        },
                      }),
                    };
                  }
                  if (requestPath === "/api/jobs/job-test") {
                    return {
                      ok: true,
                      json: async () => ({
                        job: {
                          id: "job-test",
                          operation_id: "pve-list-guests",
                          title: "List PVE guests",
                          started_at: "2026-06-25T10:00:00",
                          finished_at: "2026-06-25T10:00:05",
                          status: "success",
                          returncode: 0,
                          stdout: "Transferred: 50%",
                          stderr: "",
                          step_id: "pve_pbs",
                        },
                        config: { executor_mode: "mock" },
                        jobs: [],
                        workflow: { steps: [] },
                        profile: {},
                        capabilities: {},
                        inventory: { storage: {} },
                      }),
                    };
                  }
                  throw new Error("unexpected path " + requestPath);
                };

                render = () => {};
                showPage = (page) => { globalThis.lastPage = page; };
                globalThis.__appExports = { state, runOperation };
                state.config = { executor_mode: "mock" };
                state.workflow = { steps: [] };
                state.inventory = { storage: {} };

                (async () => {
                  await runOperation("pve-list-guests", {});
                  console.log(JSON.stringify({
                    runBody: calls.find((call) => call.path === "/api/run").body,
                    polled: calls.some((call) => call.path === "/api/jobs/job-test"),
                    jobs: state.jobs,
                    activeJobs: state.activeJobs,
                    notices: state.notices,
                    lastPage: globalThis.lastPage,
                  }));
                })();
                """
            )
        )

        self.assertTrue(payload["runBody"]["async"])
        self.assertTrue(payload["polled"])
        self.assertEqual(payload["jobs"][0]["status"], "success")
        self.assertEqual(payload["activeJobs"], {})
        self.assertEqual(payload["lastPage"], "pve")
        self.assertTrue(
            any(notice["tone"] == "success" for notice in payload["notices"])
        )


if __name__ == "__main__":
    unittest.main()
