# Google Wallet EventTicket — mapiranje kanonskog JSON-a

## 1. Svrha

Ovaj dokument opisuje mapiranje kanonskog JSON-a iz INF-12
na Google Wallet strukture `EventTicketClass` i
`EventTicketObject` u okviru ENG-03.

Trenutni obim obuhvata samo tip ulaznice. Ostali tipovi passa
nisu deo ove implementacije.

## 2. Izvor podataka

Ulazni podaci prolaze kroz `validate_ticket()` iz
`app.wallet.canonical.validator`.

Primer kanonskih podataka nalazi se u
`src/app/wallet/canonical/example.json`.

Mapiranje implementira funkcija:

`map_canonical_ticket_to_google(canonical_data, issuer_id)`

u fajlu `event_ticket.py`.

Funkcija vraća dve strukture:
- `EventTicketClass` — podatke zajedničke za događaj;
- `EventTicketObject` — podatke konkretne ulaznice.

Ova funkcija priprema strukture, ali sama ne poziva Google
Wallet API i ne izdaje pass.

## 3. Mapiranje EventTicketClass

| Google polje | Kanonski izvor ili pravilo | Namena |
|---|---|---|
| `id` | `issuer_id`, `tenant.id`, `event.id` | Jedinstveni ID klase |
| `issuerName` | `tenant.name` | Naziv izdavaoca |
| `eventId` | `tenant.id` i `event.id` | Identifikator događaja |
| `eventName` | `event.name` | Naziv događaja |
| `venue.name` | `event.location` | Naziv mesta; trenutno koristi lokaciju |
| `venue.address` | `event.location` | Adresa; trenutno koristi isto polje lokacije |
| `dateTime.start` | `event.starts_at` | Početak događaja |
| `dateTime.end` | `event.ends_at` | Završetak događaja |
| `hexBackgroundColor` | `visual.background_color` | Boja pozadine |
| `reviewStatus` | Fiksno `UNDER_REVIEW` u mapperu | Status pregleda klase |

Google klasa predstavlja zajedničke podatke o događaju.
Vrednost `reviewStatus` ne znači da je klasa odobrena.
Stvarni status i mogućnost korišćenja klase zavise od Google
Wallet procesa pregleda.

## 4. Mapiranje EventTicketObject

| Google polje | Kanonski izvor ili pravilo | Namena |
|---|---|---|
| `id` | `issuer_id`, `tenant.id`, `pass.serial_number` | Jedinstveni ID objekta ulaznice |
| `classId` | ID odgovarajuće Google klase | Povezivanje sa događajem |
| `state` | Fiksno `ACTIVE` u mapperu | Stanje ulaznice |
| `ticketHolderName` | `holder.name` | Ime nosioca |
| `ticketNumber` | `pass.serial_number` | Serijski broj ulaznice |
| `ticketType` | `ticket_type.name` | Tip ulaznice |
| `barcode.type` | Fiksno `QR_CODE` | Tip barkoda |
| `barcode.value` | HMAC QR generisan iz `tenant.id` i serijskog broja | Potpisani QR sadržaj |
| `barcode.alternateText` | `pass.serial_number` | Tekstualni prikaz QR sadržaja |
| `hexBackgroundColor` | `visual.background_color` | Boja pozadine objekta |
| `textModulesData` | `ticket_type.description` | Opis ulaznice |

QR sadržaj generiše `generate_signed_qr_content()` iz
`app.wallet.qr`. Lični podaci nosioca ne stavljaju se u QR.

## 5. Identifikatori i tehnička pravila

- `issuer_id` prosleđuje se mapperu i mora biti numerički.
- ID klase izvodi se iz izdavaoca, tenant-a i događaja.
- ID objekta izvodi se iz izdavaoca, tenant-a i serijskog broja.
- `classId` objekta mora odgovarati ID-ju njegove klase.
- QR format, način potpisivanja, struktura ID-jeva i raspored
  polja definisani su implementacijom.
- Jezik lokalizovanih vrednosti trenutno je fiksiran na `sr`.
- Mapper ne proverava postojanje klase na Google Wallet API-ju
  niti potvrđuje da je klasa odobrena.

## 6. Konfigurabilnost

Kanonski podaci određuju:
- naziv izdavaoca;
- naziv, vreme i lokaciju događaja;
- ime nosioca;
- tip i opis ulaznice;
- boju pozadine.

Tehnička struktura Google klase i objekta, format QR-a,
pravila za ID-jeve, jezik i status klase definisani su kodom.

Kanonski model trenutno sadrži samo jedno polje `event.location`.
Zbog toga se ista vrednost koristi i za `venue.name` i za
`venue.address`. Odvojeni naziv mesta i adresa nisu podržani
postojećim mapiranjem.

`visual.logo_text` i `visual.foreground_color` trenutno se ne
mapiraju u Google strukture. Njihovo buduće korišćenje zahteva
odgovarajuću odluku o Google prikazu i konfiguraciji.

## 7. Granice ENG-03

ENG-03 obuhvata pripremu Google `EventTicketClass` i
`EventTicketObject` struktura iz kanonskog JSON-a.

Sledeće aktivnosti nisu deo samog mapiranja:
- kreiranje i ažuriranje klase putem Google Wallet API-ja;
- kreiranje objekta i izdavanje Save to Google Wallet linka;
- stvarno dodavanje passa u Wallet;
- integracija novog EventTicket toka sa React admin panelom.

Ove aktivnosti obrađuju se u odgovarajućim narednim zadacima.

## 8. Provere

Testovi mapiranja nalaze se u `tests/test_google_event_ticket.py`.

Trenutni testovi proveravaju:
- mapiranje osnovnih podataka događaja i ulaznice;
- ID klase i objekta i njihovu međusobnu vezu;
- serijski broj, tip karte i nosioca;
- generisanje i verifikaciju HMAC QR sadržaja;
- odbacivanje neispravnog `issuer_id`.

Poslednja poznata provera: 2/2 testa prolaze.

Ovi testovi proveravaju lokalni rezultat mapiranja. Ne potvrđuju
da je klasa ili objekat uspešno kreiran na Google Wallet API-ju.
