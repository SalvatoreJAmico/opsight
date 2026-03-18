import { API_BASE_URL } from "../config/env";
import { ENDPOINTS } from "./endpoints";

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;

  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    const contentType = response.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");

    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        error:
          typeof data === "string"
            ? data
            : data?.detail || data?.message || "Request failed",
        data: null,
      };
    }

    return {
      ok: true,
      status: response.status,
      error: null,
      data,
    };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      error: error?.message || "Network error",
      data: null,
    };
  }
}

export async function getHealth() {
  return request("/health", {
    method: "GET",
  });
}

// Add more endpoint helpers here as Phase 11 continues
export async function runPipeline(payload) {
  return request("/pipeline/run", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}