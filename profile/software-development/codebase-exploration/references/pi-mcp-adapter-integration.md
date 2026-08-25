# pi-mcp-adapter integration — CodeGraph-verified notes (2026-08-13)

## What this project is
`pi-mcp-adapter` is the MCP (Model Context Protocol) adapter **extension for the Pi coding agent** (`@earendil-works/pi-*`). Verified via `package.json`.

- `package.json:56` — `pi.extensions: ["./index.ts"]`, `pi.skills: ["./skills"]`
- `peerDependencies`: `@earendil-works/pi-ai`, `@earendil-works/pi-tui`
- `bin`: `pi-mcp-adapter → cli.js`
- `keywords`: `pi-package`, `pi`, `mcp`, `model-context-protocol`

Two surfaces: **extension entry point** (`index.ts`) loaded inside Pi process, and **CLI helper** (`cli.js` bin) for config bootstrapping.

## CLI helper (`cli.js`) — discoverable via `mcp__codegraph__codegraph_explore` query "cli.js main entry point" and "PI_CONFIG_PATH …"

Commands (verified `cli.js:176 main()`):
```
pi install npm:pi-mcp-adapter
pi-mcp-adapter init
pi-mcp-adapter init --dry-run
pi-mcp-adapter init --discover-host-configs
```
Retired `install` command prints: "Use `pi install npm:pi-mcp-adapter` instead."

Config paths merged into `~/.pi/agent/mcp.json` (`AGENT_DIR = $PI_CODING_AGENT_DIR ?? ~/.pi/agent`):
- Pi global override: `~/.pi/agent/mcp.json` (`PI_CONFIG_PATH`)
- User-global standard: `~/.config/mcp/mcp.json`
- User-global .agents: `~/.agents/mcp.json` + `~/.agents/mcp/mcp.json`
- Project standard: `./.mcp.json`, Project Pi override: `./.pi/mcp.json`
- Host imports (compatibility): `cursor`, `claude-code`, `claude-desktop`, `codex`, `opencode`, `windsurf`, `vscode` (verified `cli.js:27 IMPORT_PATHS` and `config.ts` discovery)

## Runtime extension (`index.ts:68 installMcpAdapter` → `init.ts:91 initializeMcp`)

Verified call path via CodeGraph:
```
installMcpAdapter (index.ts:68)
  → startInitialization (index.ts:288)
    → initializeMcp (init.ts:91)
      → connect (server-manager.ts:225)
        → createConnection (server-manager.ts:328)
          → connectHttpClient (server-manager.ts:707)
```

- `installMcpAdapter` loads config (`loadMcpConfig` config.ts:293), loads metadata cache, resolves direct tools (`resolveDirectTools` direct-tools.ts:114), registers via `pi.registerTool()`, hooks `pi.on("session_start")` / `session_shutdown` with `McpRuntimeOwner` + `McpOAuthRuntime`.
- `initializeMcp` bootstraps `ServerManager`; lifecycle `eager`/`keep-alive` connects immediately, `lazy` defers to first tool call (verified `init.ts` startupServers filter).
- `ServerManager` handles 3 transports: `command` → `StdioClientTransport` (with `resolveNpxBinary` for npx), `url` → `StreamableHTTPClientTransport` with SSE fallback, `socket` → `UnixSocketClientTransport`.

## Tool dispatch — two surfaces (verified direct-tools.ts:114/300 + proxy-modes.ts)

- **Direct tools** (`direct-tools.ts:114 resolveDirectTools`, `:300 createDirectToolExecutor`): prefixed `server__toolName`, registered as native Pi tools. LLM calls directly. Requires `directTools` setting.
- **Proxy tool** (`proxy-modes.ts` `executeCall`/`executeSearch` etc.): single gateway `mcp({tool,args,server})` multiplexes all servers. Prompt-cheap.

Both converge at `ensureToolCallApproved` (tool-approval.ts) → `ServerManager.getConnection()` → `withSessionRecovery` → `client.callTool()` / `readResource()` → `guardMcpOutput` (50 KiB / 2000 lines) → `renderMcpToolResult` (tool-result-renderer.ts:269) → `toolErrorOverride` → LLM synthesis → `updateStatusBar`.

## Auth (verified mcp-oauth-provider.ts, mcp-callback-server.ts, mcp-auth-flow.ts)

- OAuth `authorization_code` + `client_credentials`, dynamic registration, secure storage via `@napi-rs/keyring`.
- `attemptDirectAutoAuth` (direct-tools.ts:50) retries on `needs-auth` if `settings.autoAuth=true`.
- Failure returns `auth_required` with message `Run mcp({ action: "auth-start"... }) or /mcp-auth <server>`.

## Mermaid artifact produced

- `pi-mcp-adapter-flow.mmd` (69 lines, 3.9K) + rendered `pi-mcp-adapter-flow.svg` (65K) at repo root.
- Rendering required `npx puppeteer browsers install chrome-headless-shell@151.0.7922.77` before `mermaid-cli` (puppeteer cache at `~/.cache/puppeteer`).

## CodeGraph usage pattern that worked

Queries that returned clean verbatim source:
- `index.ts lifecycle.ts init.ts how pi extension boots`
- `proxy-modes direct-tools tool-registrar Tool execution path …`
- `PI_CONFIG_PATH GENERIC_GLOBAL_CONFIG_PATH PROJECT_CONFIG_PATH …`
- Full lifecycle: `installMcpAdapter initializeMcp ServerManager createConnection connectHttpClient proxy-modes direct-tools …`

Pass `projectPath: /…/pi-mcp-adapter` explicitly; CodeGraph index at `.codegraph/` (182 files · 3615 nodes · 15586 edges, v1.5.0).
