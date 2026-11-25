const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export async function apiRequest(path, options = {}) {
  const url = `${BASE}${path}`;
  let response;

  try {
    response = await fetch(url, options);
  } catch (err) {
    throw new ApiError(
      "Unable to connect to EYERIS backend API. Ensure the backend server is running on http://localhost:8000.",
      0,
      err
    );
  }

  if (!response.ok) {
    let errorDetail = `API request failed with HTTP ${response.status}`;
    let data = null;
    try {
      data = await response.json();
      if (data && data.detail) {
        errorDetail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Non-JSON error payload
    }
    throw new ApiError(errorDetail, response.status, data);
  }

  return response.json();
}

// Service Methods
export async function checkHealth() {
  return apiRequest("/health");
}

export async function submitScreening(file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest("/screenings", {
    method: "POST",
    body: formData,
  });
}

export async function getScreening(caseId) {
  return apiRequest(`/screenings/${encodeURIComponent(caseId)}`);
}

export async function listScreenings(limit = 50, offset = 0) {
  return apiRequest(`/screenings?limit=${limit}&offset=${offset}`);
}

export async function getReport(caseId) {
  return apiRequest(`/screenings/${encodeURIComponent(caseId)}/report`);
}

export async function getExplanation(caseId) {
  return apiRequest(`/screenings/${encodeURIComponent(caseId)}/explanation`);
}
