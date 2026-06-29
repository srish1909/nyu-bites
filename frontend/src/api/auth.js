import client from "./client";

export const login = (nyu_email, password) =>
  client.post("/auth/login", { nyu_email, password }).then((r) => r.data);

export const register = (nyu_email, password, display_name) =>
  client.post("/auth/register", { nyu_email, password, display_name }).then((r) => r.data);

export const getMe = () =>
  client.get("/users/me").then((r) => r.data);

export const logout = (refresh_token) =>
  client.post("/auth/logout", { refresh_token });
