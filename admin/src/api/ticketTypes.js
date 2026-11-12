import { getSession } from "../auth";

const API_URL = "/api";

async function ticketTypeRequest(path, options = {}) {
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
    let message = "Greška prilikom komunikacije sa tipovima karata";

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

export function getTicketTypes(programId) {
  const query = programId ? `?program_id=${encodeURIComponent(programId)}` : "";
  return ticketTypeRequest(`/ticket-types${query}`);
}

export function createTicketType(ticketTypeData) {
  return ticketTypeRequest("/ticket-types", {
    method: "POST",
    body: JSON.stringify(ticketTypeData),
  });
}
