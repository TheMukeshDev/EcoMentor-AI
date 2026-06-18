import { api } from "./main.js";

export async function listActivities() {
  const { data } = await api("/activities");
  return data;
}

export async function logActivity(entry) {
  const { data } = await api("/activities", {
    method: "POST",
    body: JSON.stringify(entry),
  });
  return data;
}

export async function getActivity(id) {
  const { data } = await api(`/activities/${id}`);
  return data;
}

export async function deleteActivity(id) {
  await api(`/activities/${id}`, { method: "DELETE" });
}
