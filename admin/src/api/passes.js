
import { getSession } from "../auth";

const API_URL = "/api";

export async function issuePasses({ programId, ticketTypeId, guestIds, platform }) {
  const session = getSession();

  if (!session) {
    throw new Error("Niste prijavljeni");
  }

  const tenantId = session.user.tenant_id;

  if (!tenantId) {
    throw new Error("Nedostaje tenant ID u sesiji");
  }

  const response = await fetch(`${API_URL}/passes/issue`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
      "X-Tenant-ID": String(tenantId),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      program_id: Number(programId),
      ticket_type_id: Number(ticketTypeId),
      guest_ids: guestIds.map(Number),
      platform,
    }),
  });

  if (!response.ok) {
    let message = "Greška prilikom izdavanja ulaznica";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Odgovor nije JSON.
    }

    throw new Error(message);
  }

  if (platform === "apple") {
    const blob = await response.blob();
    let emailResults = null;

    const header = response.headers.get("X-Email-Results");

    if (header) {
      try {
        emailResults = JSON.parse(header);
      } catch {
        // Rezultati email slanja nisu mogli biti parsirani.
      }
    }

    return { blob, emailResults };
  }

  const data = await response.json();

  return {
    data,
    emailResults: data.email_results || null,
  };
}
