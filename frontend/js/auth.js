import { api } from "./main.js";

export async function register(email, password, name) {
  const { data } = await api("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name }),
  });
  return data;
}

export async function login(idToken) {
  const { data } = await api("/auth/login", {
    method: "POST",
    body: JSON.stringify({ id_token: idToken }),
  });
  localStorage.setItem("id_token", idToken);
  return data;
}

export async function getProfile() {
  const { data } = await api("/auth/profile");
  return data;
}

export async function updateProfile(name) {
  const { data } = await api("/auth/profile", {
    method: "PUT",
    body: JSON.stringify({ name }),
  });
  return data;
}

export function logout() {
  localStorage.removeItem("id_token");
}
