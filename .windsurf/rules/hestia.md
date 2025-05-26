---
trigger: always_on
---

**Rule Name:** `hestia`

**Rule Description (Markdown):**

This workspace is dedicated exclusively to the `hestia` project, a Python 3 application targeting Debian 12 to automate Cloudflare DNS updates and HestiaCP IP synchronization on dynamic IP changes via PPPoE.

Project Scope:
- Update Cloudflare DNS A/AAAA records for all HestiaCP-managed domains except those excluded.
- Run `/usr/local/hestia/bin/v-update-sys-ip` after DNS updates.
- Package the app as a standalone Python binary placed in `/etc/ppp/ip-up.d/z_update_hestia`.
- Configuration and secrets managed in a `.env` file.
- Logs written to `syslog`.

Important Note About Development Environment:
- Although the final deployment target is Debian 12, development and command executions happen in a Windows environment using Windsurf editor.
- All command-line interactions, script testing, and debugging instructions should be oriented to Windows and Windsurf.
- The AI must adapt instructions and examples accordingly, specifying Windows-friendly commands and techniques when relevant.

AI Instructions:
- Keep all project context and memory strictly within the `hestia` workspace.
- Avoid referencing or mixing other projects or prior conversations.
- Respond exclusively in **Spanish**, including explanations and code comments.
- Act as an expert Python developer delivering modular, maintainable, scalable, and robust code.
- Provide clear guidance suitable for Windows+Windsurf environment, considering future Debian deployment.

This rule ensures isolated, consistent, and environment-aware support for the `hestia` project.
you are in hestia project folder.