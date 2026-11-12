
import { getSession } from "../auth";

const API_URL = "/api";

async function eventRequest(path, options = {}) {
  const session = getSession();

  if (!session) {
    throw new Error("Niste prijavljeni");
  }

  const tenantId = session.user.tenant_id;

  if (!tenantId) {
    throw new Error("Nedostaje tenant ID u sesiji");
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
      "X-Tenant-ID": String(tenantId),
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    let message = "Greška prilikom komunikacije sa događajima";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Odgovor nije JSON.
    }

    throw new Error(message);
  }

  return response.json();
}

export function getEvents() {
  return eventRequest("/events");
}

export function createEvent(eventData) {
  return eventRequest("/events", {
    method: "POST",
    body: JSON.stringify(eventData),
  });
}

export function updateEventEndTime(eventId, endsAt) {
  return eventRequest(`/events/${Number(eventId)}/end-time`, {
    method: "PATCH",
    body: JSON.stringify({ ends_at: endsAt }),
  });
}
