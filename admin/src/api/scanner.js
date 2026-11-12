import { getSession } from "../auth";

const API_URL = "/api";

export async function scanQr({ qrContent, deviceRegistrationId }) {
  const session = getSession();

  if (!session) {
    throw new Error("Niste prijavljeni");
  }

  const tenantId = session.user.tenant_id;

  if (!tenantId) {
    throw new Error("Nedostaje tenant ID u sesiji");
  }

  if (!qrContent?.trim()) {
    throw new Error("QR kod nema sadržaj");
  }

  if (!Number.isInteger(Number(deviceRegistrationId)) || Number(deviceRegistrationId) <= 0) {
    throw new Error("Nedostaje validan ID registrovanog uređaja");
  }

  const response = await fetch(`${API_URL}/scanner/scan`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
      "X-Tenant-ID": String(tenantId),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      qr_content: qrContent,
      device_registration_id: Number(deviceRegistrationId),
    }),
  });

  if (!response.ok) {
    let message = "Greška prilikom provere ulaznice";

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
