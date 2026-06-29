import client from "./client";

export const getRestaurants = (params) =>
  client.get("/restaurants/", { params }).then((r) => r.data);

export const getRestaurant = (id) =>
  client.get(`/restaurants/${id}`).then((r) => r.data);

export const saveRestaurant = (id) =>
  client.post(`/users/me/saved/${id}`).then((r) => r.data);

export const unsaveRestaurant = (id) =>
  client.delete(`/users/me/saved/${id}`).then((r) => r.data);

export const getSaved = () =>
  client.get("/users/me/saved").then((r) => r.data);

export const askAgent = (query, lat, lng) =>
  client.post("/agent/query", { query, lat, lng }).then((r) => r.data);
