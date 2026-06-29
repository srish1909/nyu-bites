import axios from "axios";

// In production (Render static site), REACT_APP_API_URL is set at build time.
// In local dev, CRA's proxy (package.json "proxy") handles /api/v1 → http://api:8000.
const baseURL = process.env.REACT_APP_API_URL || "/api/v1";

const client = axios.create({ baseURL });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-logout on 401
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/";
    }
    return Promise.reject(err);
  }
);

export default client;
