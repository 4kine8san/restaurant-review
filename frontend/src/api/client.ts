import axios from "axios";
import { API_BASE_URL } from "../constants";

const client = axios.create({ baseURL: API_BASE_URL });

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.error ?? "通信エラーが発生しました";
    return Promise.reject(new Error(message));
  }
);

export default client;
