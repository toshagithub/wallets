import { Link } from "react-router-dom";

import { useEffect, useState } from "react";

import { clearSession } from "../auth";
import { createEvent, getEvents, updateEventEndTime } from "../api/events";
import {
  createTicketType,
  getTicketTypes,
} from "../api/ticketTypes";
import {
  createGuest,
  getGuests,
  importGuests,
} from "../api/guests";
import { issuePasses } from "../api/passes";

function getCountNoun(count, forms) {
  const lastTwo = Math.abs(count) % 100;
  const lastOne = Math.abs(count) % 10;

  if (lastTwo >= 11 && lastTwo <= 14) {
    return forms.many;
  }

  if (lastOne === 1) {
    return forms.one;
  }

  if (lastOne >= 2 && lastOne <= 4) {
    return forms.few;
  }

  return forms.many;
}

function formatCount(count, forms) {
  return `${count} ${getCountNoun(count, forms)}`;
}

function formatTicketCount(count) {
  return formatCount(count, {
    one: "ulaznica",
    few: "ulaznice",
    many: "ulaznica",
  });
}

function formatIssuedTicketMessage(count) {
  const lastTwo = Math.abs(count) % 100;
  const lastOne = Math.abs(count) % 10;
  const noun = formatTicketCount(count);

  if (lastTwo >= 11 && lastTwo <= 14) {
    return `Uspešno je izdato ${noun}.`;
  }

  if (lastOne === 1) {
    return `Uspešno je izdata ${noun}.`;
  }

  if (lastOne >= 2 && lastOne <= 4) {
    return `Uspešno su izdate ${noun}.`;
  }

  return `Uspešno je izdato ${noun}.`;
}

function Dashboard({ onLogout }) {
  const [eventError, setEventError] = useState("");
  const [eventMessage, setEventMessage] = useState("");
  const [events, setEvents] = useState([]);
  const [isLoadingEvents, setIsLoadingEvents] = useState(true);
  const [isSavingEvent, setIsSavingEvent] = useState(false);
  const [selectedEventId, setSelectedEventId] = useState("");
  const [eventEndForm, setEventEndForm] = useState("");
  const [isSavingEventEnd, setIsSavingEventEnd] = useState(false);
  const [eventEndError, setEventEndError] = useState("");
  const [eventEndMessage, setEventEndMessage] = useState("");
  const [ticketTypes, setTicketTypes] = useState([]);
  const [isLoadingTicketTypes, setIsLoadingTicketTypes] = useState(false);
  const [isSavingTicketType, setIsSavingTicketType] = useState(false);
  const [ticketTypeError, setTicketTypeError] = useState("");
  const [ticketTypeMessage, setTicketTypeMessage] = useState("");
  const [guests, setGuests] = useState([]);
  const [isLoadingGuests, setIsLoadingGuests] = useState(false);
  const [isSavingGuest, setIsSavingGuest] = useState(false);
  const [guestError, setGuestError] = useState("");
  const [guestMessage, setGuestMessage] = useState("");
  const [isImportingGuests, setIsImportingGuests] = useState(false);
  const [guestImportResult, setGuestImportResult] = useState(null);

  const [selectedGuestIds, setSelectedGuestIds] = useState([]);
  const [selectedTicketTypeId, setSelectedTicketTypeId] = useState("");
  const [issuePlatform, setIssuePlatform] = useState("apple");
  const [isIssuing, setIsIssuing] = useState(false);
  const [issueError, setIssueError] = useState("");
  const [issueMessage, setIssueMessage] = useState("");
  const [issueEmailResults, setIssueEmailResults] = useState(null);

  const [guestForm, setGuestForm] = useState({
    name: "",
    email: "",
    phone: "",
  });

  const [ticketTypeForm, setTicketTypeForm] = useState({
    name: "",
    price: "",
    currency: "",
    quantity_limit: "",
    sale_start: "",
    sale_end: "",
  });

  const [eventForm, setEventForm] = useState({
    name: "",
    starts_at: "",
    ends_at: "",
    location: "",
    capacity: "",
    description: "",
    image_url: "",
  });

  function handleLogout() {
    clearSession();
    onLogout();
  }

  async function loadEvents() {
    setIsLoadingEvents(true);
    setEventError("");

    try {
      const data = await getEvents();
      setEvents(data);
    } catch (err) {
      setEventError(err.message || "Greška pri učitavanju događaja");
    } finally {
      setIsLoadingEvents(false);
    }
  }

  useEffect(() => {
    loadEvents();
  }, []);

  function handleEventChange(event) {
    const { name, value } = event.target;

    setEventForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function handleCreateEvent(event) {
    event.preventDefault();
    setIsSavingEvent(true);
    setEventError("");
    setEventMessage("");

    try {
      const payload = {
        name: eventForm.name.trim(),
        event_date: eventForm.starts_at
          ? eventForm.starts_at.split("T")[0]
          : null,
        event_time: eventForm.starts_at
          ? `${eventForm.starts_at.split("T")[1]}:00`
          : null,
        ends_at: eventForm.ends_at || null,
        location: eventForm.location.trim() || null,
        capacity: eventForm.capacity
          ? Number(eventForm.capacity)
          : null,
        description: eventForm.description.trim() || null,
        image_url: eventForm.image_url.trim() || null,
      };

      const createdEvent = await createEvent(payload);

      setEventForm({
        name: "",
        starts_at: "",
        ends_at: "",
        location: "",
        capacity: "",
        description: "",
        image_url: "",
      });

      setEventMessage(
        `Događaj „${createdEvent.name}” je uspešno kreiran.`
      );

      await loadEvents();
    } catch (err) {
      setEventError(err.message || "Greška pri kreiranju događaja");
    } finally {
      setIsSavingEvent(false);
    }
  }

  async function handleUpdateEventEndTime(event) {
    event.preventDefault();
    setIsSavingEventEnd(true);
    setEventEndError("");
    setEventEndMessage("");

    try {
      if (!selectedEventId) {
        throw new Error("Prvo izaberite događaj.");
      }

      if (!eventEndForm) {
        throw new Error("Unesite datum i vreme završetka.");
      }

      await updateEventEndTime(selectedEventId, eventEndForm);
      setEventEndMessage("Završetak događaja je uspešno sačuvan.");
      await loadEvents();
    } catch (err) {
      setEventEndError(err.message || "Greška pri izmeni završetka događaja.");
    } finally {
      setIsSavingEventEnd(false);
    }
  }

  async function loadTicketTypes(programId) {
    if (!programId) {
      setTicketTypes([]);
      return;
    }

    setIsLoadingTicketTypes(true);
    setTicketTypeError("");

    try {
      const data = await getTicketTypes(programId);
      setTicketTypes(data);
    } catch (err) {
      setTicketTypeError(
        err.message || "Greška pri učitavanju tipova karata"
      );
    } finally {
      setIsLoadingTicketTypes(false);
    }
  }

  function handleTicketTypeChange(event) {
    const { name, value } = event.target;

    setTicketTypeForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function handleCreateTicketType(event) {
    event.preventDefault();

    if (!selectedEventId) {
      setTicketTypeError("Prvo izaberite događaj.");
      return;
    }

    setIsSavingTicketType(true);
    setTicketTypeError("");
    setTicketTypeMessage("");

    try {
      const payload = {
        program_id: Number(selectedEventId),
        name: ticketTypeForm.name.trim(),
        price: ticketTypeForm.price.trim() || "0",
        currency: ticketTypeForm.currency.trim().toUpperCase() || "RSD",
        quantity_limit: ticketTypeForm.quantity_limit
          ? Number(ticketTypeForm.quantity_limit)
          : null,
        sale_start: ticketTypeForm.sale_start
          ? new Date(ticketTypeForm.sale_start).toISOString()
          : null,
        sale_end: ticketTypeForm.sale_end
          ? new Date(ticketTypeForm.sale_end).toISOString()
          : null,
      };

      const created = await createTicketType(payload);

      setTicketTypeMessage(
        `Karta „${created.name}” je uspešno kreirana.`
      );

      setTicketTypeForm({
        name: "",
        price: "",
        currency: "",
        quantity_limit: "",
        sale_start: "",
        sale_end: "",
      });

      await loadTicketTypes(selectedEventId);
    } catch (err) {
      setTicketTypeError(
        err.message || "Greška pri kreiranju tipa karte"
      );
    } finally {
      setIsSavingTicketType(false);
    }
  }


  async function loadGuests(programId) {
    if (!programId) {
      setGuests([]);
      return;
    }

    setIsLoadingGuests(true);
    setGuestError("");

    try {
      const data = await getGuests(programId);
      setGuests(data);
    } catch (err) {
      setGuestError(err.message || "Greška pri učitavanju gostiju");
    } finally {
      setIsLoadingGuests(false);
    }
  }

  function handleGuestChange(event) {
    const { name, value } = event.target;

    setGuestForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function handleCreateGuest(event) {
    event.preventDefault();

    if (!selectedEventId) {
      setGuestError("Prvo izaberite događaj.");
      return;
    }

    setIsSavingGuest(true);
    setGuestError("");
    setGuestMessage("");

    try {
      const created = await createGuest({
        program_id: Number(selectedEventId),
        name: guestForm.name.trim(),
        email: guestForm.email.trim() || null,
        phone: guestForm.phone.trim() || null,
      });

      setGuestMessage(`Gost „${created.name}” je uspešno dodat.`);
      setGuestForm({ name: "", email: "", phone: "" });

      await loadGuests(selectedEventId);
    } catch (err) {
      setGuestError(err.message || "Greška pri dodavanju gosta");
    } finally {
      setIsSavingGuest(false);
    }
  }

  async function handleImportGuests(event) {
    event.preventDefault();

    if (!selectedEventId) {
      setGuestError("Prvo izaberite događaj.");
      return;
    }

    const file = event.target.elements.guestFile.files[0];

    if (!file) {
      setGuestError("Izaberite CSV ili XLSX fajl.");
      return;
    }

    setIsImportingGuests(true);
    setGuestError("");
    setGuestMessage("");
    setGuestImportResult(null);

    try {
      const result = await importGuests(selectedEventId, file);

      setGuestImportResult(result);
      setGuestMessage("Uvoz fajla je završen.");
      await loadGuests(selectedEventId);
      event.target.reset();
    } catch (err) {
      setGuestError(err.message || "Greška pri uvozu gostiju");
    } finally {
      setIsImportingGuests(false);
    }
  }

  async function handleIssuePasses(event) {
    event.preventDefault();
    setIsIssuing(true);
    setIssueError("");
    setIssueMessage("");
    setIssueEmailResults(null);

    try {
      if (!selectedEventId) {
        throw new Error("Prvo izaberite događaj.");
      }

      if (!selectedTicketTypeId) {
        throw new Error("Izaberite tip ulaznice.");
      }

      if (selectedGuestIds.length === 0) {
        throw new Error("Izaberite najmanje jednog gosta.");
      }

      const result = await issuePasses({
        programId: selectedEventId,
        ticketTypeId: selectedTicketTypeId,
        guestIds: selectedGuestIds,
        platform: issuePlatform,
      });

      if (issuePlatform === "apple") {
        const url = URL.createObjectURL(result.blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "wallets-tickets.zip";
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);

        setIssueEmailResults(result.emailResults);
        setIssueMessage(
          `${formatIssuedTicketMessage(selectedGuestIds.length)} ZIP fajl je preuzet.`
        );
      } else {
        const issued = result.data.issued || [];

        issued.forEach((item) => {
          if (item.save_url) {
            window.open(item.save_url, "_blank", "noopener,noreferrer");
          }
        });

        setIssueEmailResults(result.emailResults);
        setIssueMessage(
          issuePlatform === "both"
            ? `${formatIssuedTicketMessage(result.data.count ?? issued.length)} Opcije za dodavanje u Apple Wallet i Google Wallet poslate su putem emaila.`
            : `${formatIssuedTicketMessage(result.data.count ?? issued.length)} Google Wallet linkovi su otvoreni.`
        );
      }

      setSelectedGuestIds([]);
    } catch (err) {
      setIssueError(err.message || "Greška pri izdavanju ulaznica.");
    } finally {
      setIsIssuing(false);
    }
  }





  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <h1>Wallets Admin</h1>
        <div className="dashboard-header-actions">
          <Link to="/scanner" className="scanner-open-button">
            Otvori QR skener
          </Link>
          <button
            type="button"
            className="logout-button"
            onClick={handleLogout}
          >
            Odjavi se
          </button>
        </div>
      </header>
      <p>Dobrodošli u administratorski panel.</p>

      <section>
        <h2>Kreiranje događaja</h2>

        <form onSubmit={handleCreateEvent} className="event-form">
          <div className="form-group">
            <label htmlFor="event-name">Naziv događaja (obavezno)</label>
            <input
              id="event-name"
              name="name"
              value={eventForm.name}
              onChange={handleEventChange}
              maxLength={200}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="event-starts-at">Datum i vreme početka (obavezno)</label>
            <input
              id="event-starts-at"
              name="starts_at"
              type="datetime-local"
              required
              value={eventForm.starts_at}
              onChange={handleEventChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="event-ends-at">Datum i vreme završetka</label>
            <input
              id="event-ends-at"
              name="ends_at"
              type="datetime-local"
              value={eventForm.ends_at}
              onChange={handleEventChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="event-location">Mesto održavanja</label>
            <input
              id="event-location"
              name="location"
              value={eventForm.location}
              onChange={handleEventChange}
              maxLength={500}
            />
          </div>

          <div className="form-group">
            <label htmlFor="event-capacity">Kapacitet gostiju</label>
            <input
              id="event-capacity"
              name="capacity"
              type="number"
              min="1"
              value={eventForm.capacity}
              onChange={handleEventChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="event-image">URL slike</label>
            <input
              id="event-image"
              name="image_url"
              type="url"
              value={eventForm.image_url}
              onChange={handleEventChange}
              maxLength={2000}
            />
          </div>

          <div className="form-group event-description">
            <label htmlFor="event-description">Opis</label>
            <textarea
              id="event-description"
              name="description"
              value={eventForm.description}
              onChange={handleEventChange}
              rows={3}
            />
          </div>

          <button type="submit" disabled={isSavingEvent}>
            {isSavingEvent ? "Čuvanje..." : "Kreiraj događaj"}
          </button>
        </form>

        {eventMessage && <p role="status">{eventMessage}</p>}
        {eventError && <p className="error-message" role="alert">{eventError}</p>}
      </section>

      <section>
        <h2>Događaji</h2>

        <button
          type="button"
          onClick={loadEvents}
          disabled={isLoadingEvents}
        >
          {isLoadingEvents ? "Učitavanje..." : "Osveži listu"}
        </button>

        {isLoadingEvents ? (
          <p>Učitavanje događaja...</p>
        ) : events.length === 0 ? (
          <p>Nema kreiranih događaja.</p>
        ) : (
          <ul>
            {events.map((item) => (
              <li key={item.id}>
                <strong>{item.name}</strong>
                {" — "}
                {item.event_date || "Datum nije unet"}
                {item.event_time
                  ? `, ${item.event_time.slice(0, 5)}`
                  : ""}
                {item.location ? ` — ${item.location}` : ""}
                {item.capacity != null
                  ? ` — Kapacitet: ${item.capacity}`
                  : ""}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Izmena završetka događaja</h2>
        <p>Izaberite događaj i podesite datum i vreme završetka.</p>

        <form onSubmit={handleUpdateEventEndTime}>
          <div className="form-group">
            <label htmlFor="event-end-select">Događaj</label>
            <select
              id="event-end-select"
              value={selectedEventId}
              onChange={(event) => {
                const value = event.target.value;
                setSelectedEventId(value);
                setEventEndError("");
                setEventEndMessage("");

                const selectedEvent = events.find(
                  (item) => String(item.id) === value
                );

                if (selectedEvent?.ends_at) {
                  const parts = new Intl.DateTimeFormat("sv-SE", {
                    timeZone: "Europe/Belgrade",
                    year: "numeric",
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                    hourCycle: "h23",
                  }).formatToParts(new Date(selectedEvent.ends_at));

                  const values = Object.fromEntries(
                    parts.map(({ type, value }) => [type, value])
                  );

                  setEventEndForm(
                    `${values.year}-${values.month}-${values.day}T${values.hour}:${values.minute}`
                  );
                } else {
                  setEventEndForm("");
                }

                loadTicketTypes(value);
                loadGuests(value);
              }}
              required
            >
              <option value="">Izaberite događaj</option>
              {events.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="event-end-edit">Datum i vreme završetka</label>
            <input
              id="event-end-edit"
              type="datetime-local"
              value={eventEndForm}
              onChange={(event) => setEventEndForm(event.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            disabled={isSavingEventEnd || !selectedEventId || !eventEndForm}
          >
            {isSavingEventEnd ? "Čuvanje..." : "Sačuvaj završetak"}
          </button>
        </form>

        {eventEndError && (
          <p className="error-message" role="alert">{eventEndError}</p>
        )}
        {eventEndMessage && <p role="status">{eventEndMessage}</p>}
      </section>

      <section>
        <h2>Tipovi karata</h2>

        <label htmlFor="ticket-event">Događaj</label>
        <select
          id="ticket-event"
          value={selectedEventId}
          onChange={(event) => {
            const value = event.target.value;
            setSelectedEventId(value);
            setTicketTypeError("");
            setTicketTypeMessage("");
            loadTicketTypes(value);
          }}
        >
          <option value="">Izaberite događaj</option>
          {events.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>

        {ticketTypeError && <p style={{ color: "red" }}>{ticketTypeError}</p>}
        {ticketTypeMessage && (
          <p style={{ color: "green" }}>{ticketTypeMessage}</p>
        )}

        {selectedEventId && (
          <>
            <form onSubmit={handleCreateTicketType}>
              <label>
                Naziv karte (obavezno)
                <input
                  name="name"
                  value={ticketTypeForm.name}
                  onChange={handleTicketTypeChange}
                  required
                />
              </label>

              <label>
                Cena
                <input
                  name="price"
                  type="number"
                  min="0"
                  step="0.01"
                  value={ticketTypeForm.price}
                  onChange={handleTicketTypeChange}
                />
              </label>

              <label>
                Valuta
                <input
                  name="currency"
                  value={ticketTypeForm.currency}
                  onChange={handleTicketTypeChange}
                  minLength="3"
                  maxLength="3"
                />
              </label>

              <label>
                Broj karata
                <input
                  name="quantity_limit"
                  type="number"
                  min="1"
                  value={ticketTypeForm.quantity_limit}
                  onChange={handleTicketTypeChange}
                />
              </label>

              <label>
                Početak prodaje
                <input
                  name="sale_start"
                  type="datetime-local"
                  value={ticketTypeForm.sale_start}
                  onChange={handleTicketTypeChange}
                />
              </label>

              <label>
                Kraj prodaje
                <input
                  name="sale_end"
                  type="datetime-local"
                  value={ticketTypeForm.sale_end}
                  onChange={handleTicketTypeChange}
                />
              </label>

              <button type="submit" disabled={isSavingTicketType}>
                {isSavingTicketType ? "Čuvanje..." : "Kreiraj tip karte"}
              </button>
            </form>

            <h3>Postojeći tipovi karata</h3>

            {isLoadingTicketTypes ? (
              <p>Učitavanje...</p>
            ) : ticketTypes.length === 0 ? (
              <p>Još nema tipova karata za ovaj događaj.</p>
            ) : (
              <ul>
                {ticketTypes.map((ticket) => (
                  <li key={ticket.id}>
                    {ticket.name} — {ticket.price} {ticket.currency}
                    {ticket.quantity_limit
                      ? ` · ${formatTicketCount(ticket.quantity_limit)}`
                      : ""}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </section>


      <section>
        <h2>Gosti</h2>
        <p>Dodajte gosta i pregledajte listu za izabrani događaj.</p>

        <label htmlFor="guest-event">Događaj</label>
        <select
          id="guest-event"
          value={selectedEventId}
          onChange={(event) => {
            const value = event.target.value;
            setSelectedEventId(value);
            setGuestError("");
            setGuestMessage("");
            setGuestForm({ name: "", email: "", phone: "" });
            loadGuests(value);
          }}
        >
          <option value="">Izaberite događaj</option>
          {events.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>

        {guestError && (
          <p style={{ color: "#d92d20" }}>{guestError}</p>
        )}

        {guestMessage && (
          <p style={{ color: "#067647" }}>{guestMessage}</p>
        )}

        {selectedEventId && (
          <>
            <form onSubmit={handleCreateGuest}>
              <label>
                Ime i prezime (obavezno)
                <input
                  name="name"
                  value={guestForm.name}
                  onChange={handleGuestChange}
                  maxLength={200}
                  required
                  placeholder="Unesite ime i prezime"
                />
              </label>

              <label>
                E-mail
                <input
                  name="email"
                  type="email"
                  value={guestForm.email}
                  onChange={handleGuestChange}
                  placeholder="emailadresa@email.com"
                />
              </label>

              <label>
                Telefon
                <input
                  name="phone"
                  type="tel"
                  value={guestForm.phone}
                  onChange={handleGuestChange}
                  maxLength={50}
                  placeholder="+381..."
                />
              </label>

              <button type="submit" disabled={isSavingGuest}>
                {isSavingGuest ? "Čuvanje..." : "Dodaj gosta"}
              </button>
            </form>


            <h3>Uvoz gostiju iz fajla</h3>

            <form onSubmit={handleImportGuests}>
              <label>
                CSV ili Excel fajl (.csv, .xlsx)
                <input
                  type="file"
                  name="guestFile"
                  accept=".csv,.xlsx"
                  required
                />
              </label>

              <button type="submit" disabled={isImportingGuests}>
                {isImportingGuests ? "Uvoz u toku..." : "Uvezi goste"}
              </button>
            </form>

            {guestImportResult && (
              <div>
                <p>Uvoz je završen.</p>
                <p>Uvezeno: {formatCount(guestImportResult.imported, {
                  one: "gost",
                  few: "gosta",
                  many: "gostiju",
                })}</p>
                <p>Preskočeno: {formatCount(guestImportResult.duplicates, {
                  one: "duplikat",
                  few: "duplikata",
                  many: "duplikata",
                })}</p>
                <p>Neispravno: {formatCount(guestImportResult.invalid, {
                  one: "red",
                  few: "reda",
                  many: "redova",
                })}</p>
                <p>Ukupno obrađeno: {formatCount(guestImportResult.total, {
                  one: "red",
                  few: "reda",
                  many: "redova",
                })}</p>
              </div>
            )}

            <h3>Lista gostiju ({guests.length})</h3>

            {isLoadingGuests ? (
              <p>Učitavanje gostiju...</p>
            ) : guests.length === 0 ? (
              <p>Još nema gostiju za ovaj događaj.</p>
            ) : (
              <ul className="guest-list">
                {guests.map((guest) => (
                  <li key={guest.id} className="guest-list-item">
                    <strong>{guest.name}</strong>
                    <span>E-mail: {guest.email || "Nije uneto"}</span>
                    <span>Telefon: {guest.phone || "Nije uneto"}</span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </section>


      <section>
        <h2>Izdavanje ulaznica</h2>
        <p>Izaberite događaj, tip karte, goste i platformu za izdavanje.</p>

        <label htmlFor="issue-event">Događaj</label>
        <select
          id="issue-event"
          value={selectedEventId}
          onChange={(event) => {
            const value = event.target.value;
            setSelectedEventId(value);
            setSelectedGuestIds([]);
            setSelectedTicketTypeId("");
            setIssueError("");
            setIssueMessage("");
            loadTicketTypes(value);
            loadGuests(value);
          }}
        >
          <option value="">Izaberite događaj</option>
          {events.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>

        <form onSubmit={handleIssuePasses}>
          <div className="form-group">
            <label htmlFor="issue-ticket-type">Tip ulaznice (obavezno)</label>
            <select
              id="issue-ticket-type"
              value={selectedTicketTypeId}
              onChange={(event) => setSelectedTicketTypeId(event.target.value)}
              required
              disabled={!selectedEventId || isLoadingTicketTypes}
            >
              <option value="">Izaberite tip ulaznice</option>
              {ticketTypes.map((ticket) => (
                <option key={ticket.id} value={ticket.id}>
                  {ticket.name} — {ticket.price} {ticket.currency}
                </option>
              ))}
            </select>
          </div>

          <fieldset>
            <legend>Gosti</legend>
            {isLoadingGuests ? (
              <p>Učitavanje gostiju...</p>
            ) : guests.length === 0 ? (
              <p>Nema gostiju za izabrani događaj.</p>
            ) : (
              <>
                <div className="guest-selection-actions">
                  <button
                    type="button"
                    onClick={() => setSelectedGuestIds(guests.map((guest) => guest.id))}
                  >
                    Izaberi sve
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedGuestIds([])}
                  >
                    Poništi izbor
                  </button>
                </div>
                <ul>
                  {guests.map((guest) => (
                    <li key={guest.id} className="guest-selection-item">
                      <label className="guest-selection-label">
                        <input
                          type="checkbox"
                          checked={selectedGuestIds.includes(guest.id)}
                          onChange={(event) => {
                            setSelectedGuestIds((previous) =>
                              event.target.checked
                                ? [...previous, guest.id]
                                : previous.filter((id) => id !== guest.id)
                            );
                          }}
                        />
                        {" "}
                        {guest.name}
                        {guest.email ? ` — ${guest.email}` : ""}
                      </label>
                    </li>
                  ))}
                </ul>
                <p>Izabrano: {formatCount(selectedGuestIds.length, {
                  one: "gost",
                  few: "gosta",
                  many: "gostiju",
                })}</p>
              </>
            )}
          </fieldset>

          <fieldset>
            <legend>Platforma</legend>
            <label className="issue-platform-label">
              <input
                type="radio"
                name="issue-platform"
                value="apple"
                checked={issuePlatform === "apple"}
                onChange={(event) => setIssuePlatform(event.target.value)}
              />
              {" "}Apple Wallet
            </label>
            <label className="issue-platform-label">
              <input
                type="radio"
                name="issue-platform"
                value="google"
                checked={issuePlatform === "google"}
                onChange={(event) => setIssuePlatform(event.target.value)}
              />
              {" "}Google Wallet
            </label>
            <label className="issue-platform-label">
              <input
                type="radio"
                name="issue-platform"
                value="both"
                checked={issuePlatform === "both"}
                onChange={(event) => setIssuePlatform(event.target.value)}
              />
              {" "}Oba Walleta
            </label>
          </fieldset>

          <button
            type="submit"
            disabled={
              isIssuing ||
              isLoadingGuests ||
              isLoadingTicketTypes
            }
          >
            {isIssuing ? "Izdavanje u toku..." : "Izdaj ulaznice"}
          </button>
        </form>

        {issueError && <p className="error-message" role="alert">{issueError}</p>}
        {issueMessage && <p role="status">{issueMessage}</p>}

        {issueEmailResults && (
          <div role="status">
            <h3>Rezultati slanja emailova</h3>
            <p>Broj uspešno poslatih email poruka: {issueEmailResults.sent ?? 0}</p>
            <p>Broj neuspešnih slanja: {issueEmailResults.failed ?? 0}</p>
            <p>Broj preskočenih slanja: {issueEmailResults.skipped ?? 0}</p>
          </div>
        )}
      </section>

    </main>
  );
}

export default Dashboard;
