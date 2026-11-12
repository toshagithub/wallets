import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Html5Qrcode } from "html5-qrcode";
import { scanQr } from "../api/scanner";
import "../scanner.css";

function Scanner() {
  const scannerRef = useRef(null);
  const scanInProgressRef = useRef(false);

  const [isStarting, setIsStarting] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState("");
  const [qrContent, setQrContent] = useState("");
  const [deviceRegistrationId, setDeviceRegistrationId] = useState("");
  const [scanResult, setScanResult] = useState(null);

  useEffect(() => {
    return () => {
      const scanner = scannerRef.current;

      if (scanner?.isScanning) {
        scanner.stop().catch(() => {});
      }
    };
  }, []);

  async function startScanner() {
    setError("");
    setQrContent("");
    setScanResult(null);
    setIsStarting(true);

    try {
      const scanner = new Html5Qrcode("qr-reader");
      scannerRef.current = scanner;

      await scanner.start(
        { facingMode: "environment" },
        {
          fps: 10,
          qrbox: { width: 250, height: 250 },
        },
        async (decodedText) => {
          if (scanInProgressRef.current) return;

          scanInProgressRef.current = true;
          setQrContent(decodedText);
          setError("");
          setScanResult(null);
          setIsChecking(true);

          try {
            if (scanner.isScanning) {
              await scanner.stop();
            }
            setIsScanning(false);

            const result = await scanQr({
              qrContent: decodedText,
              deviceRegistrationId,
            });

            setScanResult(result);
          } catch (err) {
            setError(
              err?.message || "Greška prilikom provere ulaznice.",
            );
          } finally {
            setIsChecking(false);
          }
        },
        () => {},
      );

      setIsScanning(true);
    } catch (err) {
      setError(
        err?.message ||
          "Kameru nije moguće pokrenuti. Proveri dozvolu za kameru i HTTPS pristup.",
      );
    } finally {
      setIsStarting(false);
    }
  }

  async function stopScanner() {
    const scanner = scannerRef.current;

    if (scanner?.isScanning) {
      try {
        await scanner.stop();
      } catch {
        setError("Kameru nije bilo moguće pravilno zaustaviti.");
      }
    }

    setIsScanning(false);
  }

  function resetScan() {
    scanInProgressRef.current = false;
    setQrContent("");
    setScanResult(null);
    setError("");
  }

  return (
    <main className="scanner-page">
      <header className="scanner-header">
        <div>
          <h1>QR skener</h1>
          <p>Skeniraj QR kod ulaznice i proveri njen status.</p>
        </div>
        <Link to="/" className="scanner-back-link">
          Nazad na kontrolnu tablu
        </Link>
      </header>

      <section className="scanner-card">
        <h2>Skeniranje ulaznice</h2>
        <p>Unesi ID aktivno registrovanog uređaja, pa usmeri kameru ka QR kodu.</p>

        <label className="scanner-device-field">
          ID registrovanog uređaja
          <input
            type="number"
            min="1"
            step="1"
            value={deviceRegistrationId}
            onChange={(event) => setDeviceRegistrationId(event.target.value)}
            disabled={isScanning || isStarting || isChecking}
            placeholder="Unesi ID uređaja"
          />
        </label>

        <div id="qr-reader" className="scanner-camera" />

        {scanResult || error ? (
          <button type="button" onClick={resetScan} disabled={isChecking}>
            Spremno za novo skeniranje
          </button>
        ) : !isScanning ? (
          <button
            type="button"
            onClick={startScanner}
            disabled={
              isStarting ||
              isChecking ||
              !Number.isInteger(Number(deviceRegistrationId)) ||
              Number(deviceRegistrationId) <= 0
            }
          >
            {isStarting
              ? "Pokretanje kamere..."
              : isChecking
                ? "Provera ulaznice..."
                : "Pokreni kameru"}
          </button>
        ) : (
          <button type="button" onClick={stopScanner}>
            Zaustavi kameru
          </button>
        )}

        {error && (
          <p className="scanner-error" role="alert">
            {error}
          </p>
        )}

        {isChecking && (
          <p className="scanner-hint" role="status">
            Proveravam ulaznicu na serveru...
          </p>
        )}

        {scanResult && (
          <div
            className={`scanner-result scanner-result-${scanResult.result === "VAŽI" ? "valid" : "invalid"}`}
            role="status"
          >
            <h3>{scanResult.result}</h3>
            <p>{scanResult.message}</p>
            <p className="scanner-hint">
              Vreme skeniranja:{" "}
              {new Date(scanResult.scanned_at).toLocaleString("sr-RS")}
            </p>
          </div>
        )}

        {qrContent && (
          <details className="scanner-qr-details">
            <summary>Prikaži očitani sadržaj QR koda</summary>
            <code>{qrContent}</code>
          </details>
        )}


        <p className="scanner-hint">
          Status ulaznice određuje server, ne sam skener.
        </p>
      </section>
    </main>
  );
}

export default Scanner;
