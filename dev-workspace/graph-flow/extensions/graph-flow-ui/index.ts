import { GraphFlowControls } from "./controls.ts";
import { answerOpenRequest, answerPendingApproval } from "./dialogs.ts";
import { renderActionCenter, renderCockpit } from "./projection.ts";
import { GraphStateClient } from "./state-client.ts";
import type { CockpitSnapshot, CommandResult, DialogUI } from "./types.ts";

interface ExtensionUI extends DialogUI {
  setWidget(key: string, lines: string[] | undefined): void;
  setStatus(key: string, text: string | undefined): void;
  notify(message: string, type?: "info" | "warning" | "error"): void;
}

interface ExtensionContext {
  cwd: string;
  hasUI: boolean;
  ui: ExtensionUI;
}

interface ExtensionAPI {
  exec(command: string, args: string[], options?: { cwd?: string }): Promise<CommandResult>;
  on(event: "session_start" | "session_shutdown", handler: (event: unknown, context: ExtensionContext) => void | Promise<void>): void;
  registerCommand(name: string, options: { description: string; handler: (args: string | undefined, context: ExtensionContext) => Promise<void> }): void;
}

declare const console: { log(value: string): void };

export async function refreshCockpit(snapshot: CockpitSnapshot, context: Pick<ExtensionContext, "hasUI" | "ui">): Promise<string[] | undefined> {
  const lines = [...renderCockpit(snapshot), ...renderActionCenter(snapshot.open_request, snapshot.pending_approval)];
  if (!context.hasUI) return lines;
  context.ui.setWidget("graph-flow", lines);
  context.ui.setStatus("graph-flow", `Graph flow: ${snapshot.status}`);
  return undefined;
}

class CockpitController {
  private readonly context: ExtensionContext;
  private readonly client: GraphStateClient;
  private readonly controls: GraphFlowControls;
  private stopWatching: (() => void) | undefined;
  private active = true;

  constructor(pi: ExtensionAPI, context: ExtensionContext, runId: string) {
    this.context = context;
    this.client = new GraphStateClient({
      repo: context.cwd,
      runId,
      execute: (command, args) => pi.exec(command, args, { cwd: context.cwd }),
    });
    this.controls = new GraphFlowControls(this.client);
  }

  async refresh(): Promise<void> {
    const snapshot = await this.client.refresh();
    this.deliver(snapshot, true);
  }

  watch(): void {
    this.stopWatching?.();
    this.stopWatching = this.client.watch((snapshot) => this.deliver(snapshot, false), () => this.active, false);
  }

  async answer(): Promise<void> {
    const snapshot = await this.client.refresh();
    if (snapshot.open_request) await answerOpenRequest(snapshot.open_request, this.context.hasUI ? this.context.ui : undefined, (id, answer) => this.client.respond(id, answer));
    else if (snapshot.pending_approval) await answerPendingApproval(snapshot.pending_approval, this.context.hasUI ? this.context.ui : undefined, this.controls);
    await this.refresh();
  }

  async approve(): Promise<void> {
    const snapshot = await this.client.refresh();
    if (snapshot.pending_approval) await answerPendingApproval(snapshot.pending_approval, this.context.hasUI ? this.context.ui : undefined, this.controls);
    await this.refresh();
  }

  async control(action: string, values: string[]): Promise<void> {
    if (action === "pause") await this.controls.pause();
    else if (action === "resume") await this.controls.resume();
    else if (action === "stop") await this.controls.requestStop();
    else if (action === "confirm-stop") await this.controls.confirmStop({ handles: JSON.parse(values.join(" ")) as Record<string, string> });
    else if (action === "steer") {
      const [node, ...message] = values;
      if (!node || message.length === 0) throw new Error("steer requires a node and message");
      await this.controls.steer(node, message.join(" "));
    } else throw new Error(`unknown graph-flow action: ${action}`);
    await this.refresh();
  }

  dispose(): void {
    this.active = false;
    this.stopWatching?.();
    if (this.context.hasUI) {
      this.context.ui.setWidget("graph-flow", undefined);
      this.context.ui.setStatus("graph-flow", undefined);
    }
  }

  private deliver(snapshot: CockpitSnapshot, announce: boolean): void {
    if (!this.active) return;
    const lines = [...renderCockpit(snapshot), ...renderActionCenter(snapshot.open_request, snapshot.pending_approval)];
    if (this.context.hasUI) {
      this.context.ui.setWidget("graph-flow", lines);
      this.context.ui.setStatus("graph-flow", `Graph flow: ${snapshot.status}`);
      if (announce) this.context.ui.notify(`Graph flow ${snapshot.status}`, "info");
      return;
    }
    console.log(lines.join("\n"));
  }
}

export default function graphFlowExtension(pi: ExtensionAPI): void {
  let activeController: CockpitController | undefined;
  const replaceController = (context: ExtensionContext, runId: string): CockpitController => {
    activeController?.dispose();
    activeController = new CockpitController(pi, context, runId);
    return activeController;
  };
  pi.on("session_start", () => undefined);
  pi.on("session_shutdown", () => {
    activeController?.dispose();
    activeController = undefined;
  });
  pi.registerCommand("graph-flow", {
    description: "Show or control a portable graph-flow run: <run-id> [status|answer|approve|pause|resume|steer|stop|confirm-stop]",
    handler: async (args, context) => {
      const [runId, action = "status", ...values] = (args ?? "").trim().split(/\s+/u).filter(Boolean);
      if (!runId) {
        presentMessage(context, "Usage: /graph-flow <run-id> [status|answer|approve|pause|resume|steer|stop|confirm-stop]");
        return;
      }
      const controller = replaceController(context, runId);
      if (action === "status") await controller.refresh();
      else if (action === "answer") await controller.answer();
      else if (action === "approve") await controller.approve();
      else await controller.control(action, values);
      controller.watch();
    },
  });
  pi.registerCommand("graph-flow-status", {
    description: "Show a graph-flow run's public cockpit projection",
    handler: async (args, context) => {
      const runId = (args ?? "").trim();
      if (!runId) {
        presentMessage(context, "Usage: /graph-flow-status <run-id>");
        return;
      }
      const controller = replaceController(context, runId);
      await controller.refresh();
      controller.watch();
    },
  });
}

function presentMessage(context: ExtensionContext, message: string): void {
  if (context.hasUI) context.ui.notify(message, "warning");
  else console.log(message);
}
