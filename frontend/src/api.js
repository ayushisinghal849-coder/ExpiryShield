import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 12000,
});

export async function loadDashboard() {
  const [analytics, inventory, stores] = await Promise.all([
    api.get("/analytics"),
    api.get("/inventory"),
    api.get("/stores"),
  ]);
  return { analytics: analytics.data, inventory: inventory.data, stores: stores.data };
}
export async function loadRecommendations() {
  const { data } = await api.get("/recommend");
  return data;
}
export async function runAnalysis() {
  const { data } = await api.post("/analyze");
  return data;
}
export async function approveRecommendation(id, approvedBy = "Store Manager") {
  return (await api.post("/approve", { recommendation_id: id, approved_by: approvedBy })).data;
}
export async function rejectRecommendation(id) {
  return (await api.post("/reject", { recommendation_id: id, reason: "Rejected from dashboard" })).data;
}
export async function completeRecommendation(id) {
  return (await api.post("/complete", { recommendation_id: id })).data;
}
export async function uploadInventory(file) {
  const form = new FormData();
  form.append("file", file);
  return (await api.post("/inventory/upload-csv", form, { headers: { "Content-Type": "multipart/form-data" } })).data;
}
export default api;
export async function loadAnalysis(storeId) {
  const { data } = await api.post("/analyze", null, { params: storeId ? { store_id: storeId } : {} });
  return data;
}
export async function loadDemoScenarios() {
  return (await api.get("/demo-scenarios")).data;
}
export async function applyDemoScenario(id) {
  return (await api.post(`/demo-scenarios/${id}/load`)).data;
}
