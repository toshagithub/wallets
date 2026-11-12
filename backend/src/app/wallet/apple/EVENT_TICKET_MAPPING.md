# Apple eventTicket — mapiranje kanonskog JSON-a

## 1. Svrha

Ovaj dokument opisuje mapiranje kanonskog JSON-a iz INF-12
na Apple Wallet `eventTicket` strukturu u okviru ENG-03.

Trenutni obim obuhvata samo tip ulaznice (`eventTicket`).
Ostali tipovi passa i Google Wallet mapiranje ostavljeni su za kasnije.

## 2. Izvor podataka

Ulazni podaci prolaze kroz `validate_ticket()` iz
`app.wallet.canonical.validator`.

Primer kanonskih podataka nalazi se u
`src/app/wallet/canonical/example.json`.

Mapiranje implementira funkcija:

`map_canonical_ticket_to_apple(canonical_data)`

u fajlu `event_ticket.py`.

## 3. Raspored polja na Apple ulaznici

| Apple polje | Kanonski izvor | Namena |
|---|---|---|
| `headerFields` | `ticket_type.name` | Tip karte |
| `primaryFields` | `event.name` | Naziv događaja |
| `secondaryFields[0]` | `event.starts_at` | Datum i vreme početka |
| `secondaryFields[1]` | `event.location` | Lokacija događaja |
| `auxiliaryFields` | `holder.name` | Ime nosioca |
| `backFields[0]` | `ticket_type.description` | Opis karte |
| `backFields[1]` | `tenant.name` | Organizator |
| `backFields[2]` | `event.ends_at` | Datum i vreme završetka |

Datum i vreme prikazuju se u formatu `DD.MM.YYYY. HH:MM`.

## 4. Vizuelna svojstva i identifikacija

| Apple polje | Izvor ili pravilo |
|---|---|
| `formatVersion` | Fiksna tehnička vrednost iz šablona |
| `passTypeIdentifier` | Konfiguracija Apple Pass Type ID-ja |
| `teamIdentifier` | Apple Developer Team ID |
| `serialNumber` | `pass.serial_number` iz kanonskog JSON-a |
| `organizationName` | `tenant.name` |
| `logoText` | `visual.logo_text` |
| `foregroundColor` | `visual.foreground_color`, konvertovan u Apple RGB format |
| `backgroundColor` | `visual.background_color`, konvertovan u Apple RGB format |
| `description` | Trenutno fiksni tekst iz šablona |

Tehnički identifikatori ne menjaju se proizvoljno po ulaznici.
Njihova konkretna konfiguracija proverava se pri integraciji sa
stvarnim izdavanjem passa.

## 5. Polja koja se popunjavaju pri izdavanju

Šablon sadrži mesta za sledeće vrednosti:

- `authenticationToken`
- `barcodes[0].message`
- `webServiceURL`

Trenutna funkcija mapiranja ne generiše ove vrednosti.
One ostaju za integraciju u narednom koraku generisanja Apple
passa (ENG-01). Vrednosti iz šablona koje su označene kao
zamene nisu spremne za stvarno izdavanje.

## 6. Konfigurabilnost

Kanonski podaci trenutno određuju naziv organizatora, naziv
događaja, datum i vreme, lokaciju, nosioca, tip karte i boje.

Raspored polja i tehnička struktura `eventTicket` definisani su
u kodu. Promena rasporeda polja nije deo trenutne konfiguracije
tenanta.

Logotipi, kontakt podaci i dodatna pravila brendiranja nisu
implementirani ovim mapiranjem i ostaju predmet odgovarajućih
koraka projekta.

## 7. Google Wallet

Mapiranje na `EventTicketClass` i `EventTicketObject`, kao i
funkcije za njihovo generisanje, namerno su odloženi za Google
Wallet fazu. Ovaj dokument ne predstavlja završetak tog dela
ENG-03.

## 8. Provere

Testovi mapiranja nalaze se u `tests/test_apple_event_ticket.py`.

Proveravaju se:
- izbor Apple tipa `eventTicket`;
- mapiranje podataka događaja i karte;
- mapiranje polja na poleđini;
- vizuelna svojstva;
- odbacivanje neispravnih kanonskih podataka.

Poslednja poznata provera: 5/5 testova prolazi.
