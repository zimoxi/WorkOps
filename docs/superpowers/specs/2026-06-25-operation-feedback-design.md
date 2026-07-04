# Operation Feedback Design

## Goal

Every user-triggered action should show visible state immediately. Short actions show a toast-style status message; long command actions create a running job card with elapsed time, progress when available, and a final success or failure message.

## Approach

Keep the existing synchronous `/api/run` behavior for compatibility, and add an optional async mode for the web UI. When `async: true` is sent, the server returns a `running` job immediately and executes the command in a background thread. The UI polls `/api/jobs/<id>` until the job reaches `success` or `failed`.

## User Experience

The page gets a fixed status region that is visible on every menu. It contains recent notifications and active operation cards. Operation cards show title, current state, elapsed time, step, progress bar, and a compact output preview when complete. Commands that do not expose exact progress use an indeterminate progress bar and a clear "waiting for command output" style message.

## Safety

Danger confirmation remains unchanged. Async execution starts only after the existing confirmation text is accepted. SSH passwords are still request-only and are not stored in job records.

## Testing

Add backend tests for async job start and polling. Add frontend tests for notification rendering, progress parsing, active job rendering, and the async run request shape.
