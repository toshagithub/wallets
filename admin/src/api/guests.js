
import { getSession } from "../auth";

const API_URL = "/api";

async function guestRequest(path, options = {}) {
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
    let message = "Greška prilikom komunikacije sa gostima";

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

export function getGuests(programId) {
  const query = `?program_id=${encodeURIComponent(programId)}`;
  return guestRequest(`/guests${query}`);
}

export function createGuest(guestData) {
  return guestRequest("/guests", {
    method: "POST",
    body: JSON.stringify(guestData),
  });
}

export async function importGuests(programId, file) {
  const session = getSession();

  if (!session) {
    throw new Error("Niste prijavljeni");
  }

  const tenantId = session.user.tenant_id;

  if (!tenantId) {
    throw new Error("Nedostaje tenant ID u sesiji");
  }

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${API_URL}/guests/import?program_id=${encodeURIComponent(programId)}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.accessToken}`,
        "X-Tenant-ID": String(tenantId),
      },
      body: formData,
    }
  );

  if (!response.ok) {
    let message = "Greška prilikom uvoza gostiju";

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
