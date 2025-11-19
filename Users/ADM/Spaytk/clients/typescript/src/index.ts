// Minimal TypeScript axios-style client scaffold for the Orquestador API

export interface OrquestadorClientOptions {
  baseUrl?: string;
}

export class OrquestadorClient {
  baseUrl: string;
  constructor(options?: OrquestadorClientOptions) {
    this.baseUrl = options?.baseUrl ?? "http://localhost";
  }
}

export default OrquestadorClient;
