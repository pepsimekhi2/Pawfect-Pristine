import axios from "axios";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";
export const API_BASE = `${BACKEND}/api`;

const api = axios.create({ baseURL: BACKEND });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("pp_token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
