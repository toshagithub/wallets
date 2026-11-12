import { getSession } from "../auth";

const API_URL = "/api";

export async function generateGooglePass() {
  const session = getSession();

  if (!session) {
    throw new Error("Niste prijavljeni");
  }

  const tenantId = session.user.tenant_id;

  if (!tenantId) {
    throw new Error("Nedostaje tenant ID u sesiji");
  }

  const response = await fetch(`${API_URL}/wallet/google/pass`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
      "X-Tenant-ID": String(tenantId),
    },
  });

  if (!response.ok) {
    let message = "Greška prilikom generisanja Google Wallet passa";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Backend nije vratio JSON grešku.
    }

    throw new Error(message);
  }

  const data = await response.json();

  if (!data.save_url) {
    throw new Error("Backend nije vratio Google Wallet link");
  }

  return data.save_url;
}

export async function generateGoogleEventPass() {
  const session = getSession();

  if (!session) {
    throw new Error("Niste prijavljeni");
  }

  const response = await fetch(`${API_URL}/wallet/google/event-pass`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
    },
  });

  if (!response.ok) {
    let message = "Greška prilikom generisanja Google Wallet EventTicket passa";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Backend nije vratio JSON grešku.
    }

    throw new Error(message);
  }

  const data = await response.json();

  if (!data.save_url) {
    throw new Error("Backend nije vratio Google Wallet link");
  }

  return data.save_url;
}
