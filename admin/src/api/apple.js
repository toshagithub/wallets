
import { getSession } from "../auth";

const API_URL = "/api";

export async function generateApplePass() {
  const session = getSession();

  if (!session) {
    throw new Error("Niste prijavljeni");
  }

  const tenantId = session.user.tenant_id;

  if (!tenantId) {
    throw new Error("Nedostaje tenant ID u sesiji");
  }

  const response = await fetch(`${API_URL}/wallet/apple/pass`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
      "X-Tenant-ID": String(tenantId),
    },
  });

  if (!response.ok) {
    let message = "Greška prilikom generisanja passa";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Backend nije vratio JSON grešku.
    }

    throw new Error(message);
  }

  return response.blob();
}

export async function generateAppleEventPass() {
  const session = getSession();

  if (!session) {
    throw new Error("Niste prijavljeni");
  }

  const response = await fetch(`${API_URL}/wallet/apple/event-pass`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
    },
  });

  if (!response.ok) {
    let message = "Greška prilikom generisanja Event passa";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Backend nije vratio JSON grešku.
    }

    throw new Error(message);
  }

  return response.blob();
}
