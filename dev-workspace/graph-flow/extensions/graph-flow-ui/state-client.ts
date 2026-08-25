import type { CockpitSnapshot, CommandResult, CommandRunner } from "./types.ts";
import { fileURLToPath as nodeFileURLToPath } from "node:url";

declare function setInterval(callback: () => void, delay: number): number;
declare function clearInterval(id: number): void;
declare const URL: { new(url: string, base?: string): { protocol: string; hostname: string; pathname: string } };
declare global {
  interface ImportMeta { url: string }
}

function safeFallbackFileURLToPath(value: string): string {
  const location = new URL(value);
  if (location.protocol !== "file:") throw new Error("bundled reducer URL must use file:");
  if (/%2f|%5c/iu.test(location.pathname)) throw new Error("bundled reducer URL contains an encoded path separator");
  const pathname = decodeURIComponent(location.pathname);
  if (location.hostname && location.hostname !== "localhost") return `//${location.hostname}${pathname}`;
  return pathname;
}

export function fileUrlToPath(value: string): string {
  try {
    return nodeFileURLToPath(value);
  } catch {
    return safeFallbackFileURLToPath(value);
  }
}

export function bundledReducerPath(): string {
  return fileUrlToPath(new URL("../../scripts/graph_state.py", import.meta.url).toString());
}

function commandError(result: CommandResult, name: string): string {
  const stderr = result.stderr.trim();
  if (stderr) return stderr;
  const stdout = result.stdout.trim();
  if (stdout) {
    try {
      const payload = JSON.parse(stdout) as { error?: unknown };
      if (typeof payload.error === "string" && payload.error.trim()) return payload.error;
    } catch {
      return stdout;
    }
    return stdout;
  }
  return `graph_state ${name} failed`;
}

export interface GraphStateClientOptions extends CommandRunner {
  repo: string;
  runId: string;
  scriptPath?: string;
}

export class GraphStateClient {
  readonly repo: string;
  readonly runId: string;
  readonly scriptPath: string;
  private readonly executeCommand: CommandRunner["execute"];

  constructor(options: GraphStateClientOptions) {
    this.repo = options.repo;
    this.runId = options.runId;
    this.scriptPath = options.scriptPath ?? bundledReducerPath();
    this.executeCommand = options.execute;
  }

  async command(name: "runs" | "status" | "respond" | "approve" | "pause" | "resume" | "steer-request" | "stop-request" | "stop-confirm", extra: string[] = []): Promise<CommandResult> {
    const args = [this.scriptPath, name, "--repo", this.repo];
    if (name !== "runs") args.push("--run-id", this.runId);
    args.push(...extra);
    const result = await this.executeCommand("python3", args);
    if (result.code !== 0) throw new Error(commandError(result, name));
    return result;
  }

  async refresh(onSnapshot?: (snapshot: CockpitSnapshot) => void): Promise<CockpitSnapshot> {
    const result = await this.command("status", ["--format", "json"]);
    const snapshot = JSON.parse(result.stdout) as CockpitSnapshot;
    onSnapshot?.(snapshot);
    return snapshot;
  }

  async text(): Promise<string> {
    return (await this.command("status", ["--format", "text"])).stdout;
  }

  async respond(requestId: string, answer: unknown): Promise<void> {
    await this.command("respond", ["--request-id", requestId, "--answer", JSON.stringify(answer)]);
  }

  watch(onSnapshot: (snapshot: CockpitSnapshot) => void, sessionActive: () => boolean, refreshImmediately = true): () => void {
    let timer: number | undefined;
    let disposed = false;
    const refresh = async () => {
      if (!sessionActive()) {
        if (timer !== undefined) clearInterval(timer);
        timer = undefined;
        return;
      }
      try {
        const snapshot = await this.refresh();
        if (!disposed && sessionActive()) onSnapshot(snapshot);
      } catch {
        // Polling is best-effort; explicit commands surface CLI failures.
      }
    };
    if (refreshImmediately) void refresh();
    timer = setInterval(() => { void refresh(); }, 1_000);
    return () => {
      disposed = true;
      if (timer !== undefined) clearInterval(timer);
      timer = undefined;
    };
  }
}
