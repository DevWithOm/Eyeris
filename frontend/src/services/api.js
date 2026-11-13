const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
export async function apiRequest(path, options={}) {
  const response = await fetch(`${BASE}${path}`, options);
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return response.json();
}
