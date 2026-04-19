import axios from "axios";
import { API_BASE_URL } from "../constants";

const client = axios.create({ baseURL: API_BASE_URL });

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const method = err.config?.method?.toUpperCase() ?? "";
    const url = err.config?.url ?? "";
    const status = err.response?.status;
    const serverMessage = err.response?.data?.error;

    console.error(`[API] ${method} ${url} → ${status ?? "network error"}`, err.response?.data ?? err.message);

    let message: string;
    if (serverMessage) {
      const details = err.response?.data?.details as Record<string, string> | undefined;
      message = details
        ? `${serverMessage}\n${Object.entries(details).map(([k, v]) => `・${k}: ${v}`).join("\n")}`
        : serverMessage;
    } else if (status) {
      message = `通信エラーが発生しました (HTTP ${status}: ${method} ${url})`;
    } else {
      message = `サーバーに接続できません (${method} ${url})`;
    }
    return Promise.reject(new Error(message));
  }
);

export default client;
