import { GraphStateClient } from "./state-client.ts";

export class GraphFlowControls {
  private readonly client: GraphStateClient;

  constructor(client: GraphStateClient) {
    this.client = client;
  }

  async pause(): Promise<void> { await this.mutate("pause"); }
  async resume(): Promise<void> { await this.mutate("resume"); }
  async approveGraph(): Promise<void> { await this.mutate("approve"); }
  async approveNode(node: string, outcome: string): Promise<void> {
    await this.mutate("approve", ["--node", node, "--result-json", JSON.stringify({ outcome, evidence: { source: "graph-flow-ui", answer: outcome } })]);
  }
  async steer(node: string, message: string): Promise<void> { await this.mutate("steer-request", ["--node", node, "--message", message]); }
  async requestStop(): Promise<void> { await this.mutate("stop-request"); }
  async confirmStop(evidence: { handles: Record<string, string> }): Promise<void> { await this.mutate("stop-confirm", ["--evidence", JSON.stringify(evidence)]); }

  private async mutate(name: "approve" | "pause" | "resume" | "steer-request" | "stop-request" | "stop-confirm", extra: string[] = []): Promise<void> {
    await this.client.command(name, extra);
  }
}
