# Cloud Provider Guides Design

## Goal

Make the cloud page explain the correct connection flow for each provider before the user runs `rclone`, while keeping credentials out of persistent application configuration.

## Scope

- Keep the existing Baidu WebDAV gateway, generic WebDAV, AWS S3, Alibaba OSS, and Baidu S3 gateway guides.
- Add Microsoft OneDrive and Google Drive guides using rclone's interactive OAuth flow.
- Show provider-specific preparation, authorization, verification, upload, and restore guidance.
- Show a clear success criterion and provider-specific troubleshooting notes.
- Continue using the existing backend operations for validation, listing, sync, and pull.

## Authentication Boundaries

WebDAV and S3 guides may accept service-specific credentials in page memory. They must never persist password, access key, secret key, or token fields. OAuth guides must not request the user's Microsoft or Google password. They instruct the user to run `rclone config` and finish authorization in the provider's browser page.

## Interface

The selected guide controls all visible fields and instructions. A compact provider header identifies the authentication type. A four-stage visual flow shows Prepare, Connect, Verify, and Protect/Restore. Below it, reference cards answer where to obtain required values, what success looks like, and how to recover from common errors. Official documentation links remain visible.

## Commands

WebDAV and S3 retain generated `rclone config create` previews. OAuth providers show `rclone config` because an interactive browser/device authorization cannot be represented safely as an account/password command. All providers use the existing `rclone lsd`, `rclone lsf`, `rclone sync`, and `rclone copy` operations after a remote exists.

## Verification

Automated frontend tests must prove that OneDrive and Google Drive guides exist, do not expose password fields, generate interactive configuration commands, and retain the existing session-secret stripping behavior. The full Python test suite and JavaScript syntax check must pass. The cloud page must also be visually checked at desktop and mobile widths.
