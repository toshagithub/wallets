# INF-12 — Kanonski JSON za ulaznicu

## 1. Svrha

Kanonski JSON predstavlja platformno nezavisan izvor poslovnih podataka za generisanje ulaznica za Apple Wallet i Google Wallet.

Šema definiše zajednički format podataka, dok su generisanje, potpisivanje i platformsko mapiranje odgovornost narednih komponenti.

## 2. Struktura podataka

Kanonski JSON sadrži sledeće blokove:

| Blok | Namena |
|---|---|
| `pass` | Identifikacija ulaznice i njen serijski broj |
| `tenant` | Identifikacija organizacije koja izdaje ulaznicu |
| `event` | Naziv događaja, početak, kraj i mesto održavanja |
| `holder` | Identifikacija i podaci nosioca ulaznice |
| `ticket_type` | Identifikacija i naziv tipa ulaznice |
| `visual` | Tekst logotipa i boje za vizuelni prikaz |
| `meta` | Verzija kanonske šeme |

Detaljna pravila tipova, obaveznih polja i dozvoljenih vrednosti definisana su u `schema.json`.

## 3. Obavezna i opciona polja

Obaveznost polja određena je nizovima `required` u `schema.json`. Nepoznata polja nisu dozvoljena na nivoima na kojima je definisano `additionalProperties: false`.

- **`pass`**: obavezni su identifikator i serijski broj.
- **`tenant`**: obavezni su identifikator i naziv organizacije.
- **`event`**: obavezni su identifikator, naziv, vreme početka, vreme završetka i mesto održavanja.
- **`holder`**: obavezni su identifikator i ime nosioca; email i telefon su opcioni.
- **`ticket_type`**: obavezni su identifikator i naziv tipa ulaznice; opis je opcioni.
- **`visual`**: obavezni su tekst logotipa i definisane boje.
- **`meta`**: obavezna je podržana verzija šeme.

Validator dodatno proverava da vreme završetka događaja bude nakon vremena početka.

## 4. Poreklo podataka

- `pass`: podaci o konkretnoj ulaznici; serijski broj mora biti dodeljen kroz odgovarajući proces izdavanja.
- `tenant`: podaci o organizaciji izdavaocu.
- `event`: podaci o događaju, koji će se preuzimati iz evidencije događaja kada bude implementiran ADM-05.
- `holder`: podaci o primaocu, koji će se preuzimati iz odgovarajuće evidencije kada bude implementiran ADM-14.
- `ticket_type`: podaci o definisanom tipu ulaznice.
- `visual`: podaci o vizuelnom identitetu organizacije.
- `meta`: verzija formata kanonskih podataka.

`example.json` sadrži testne podatke za događaj i nosioca. Oni nisu zamena za buduće poslovne evidencije. Kanonski JSON standardizuje podatke za dalje generisanje passa, ali nije zamena za izvorne evidencije.

## 5. Prikaz na Wallet kartici

Predloženi sadržaj prikaza:

**Prednja strana**
- naziv događaja (`event.name`)
- ime nosioca (`holder.name`)
- naziv tipa ulaznice (`ticket_type.name`)
- QR/bar-kod koji će se generisati u okviru odgovarajuće komponente

**Poleđina**
- mesto održavanja (`event.location`)
- početak i završetak događaja (`event.starts_at`, `event.ends_at`)
- opis tipa ulaznice (`ticket_type.description`), ako postoji
- dodatne informacije koje budu definisane zahtevima proizvoda

Ovo je logička podela prikaza. Konačno raspoređivanje polja u Apple i Google formatima pripada zadatku ENG-03.

## 6. Privatnost podataka

Email i telefon nisu obavezni za kanonski model. Treba uključivati samo podatke koji su potrebni za konkretan slučaj upotrebe.

Lični podaci ne treba da budu deo QR sadržaja. Format i potpis QR koda pripadaju zasebnoj komponenti ENG-05.

## 7. Granice zadatka

INF-12 obuhvata:
- definisanje kanonske JSON šeme;
- validaciju podataka prema šemi;
- testni primer popunjene ulaznice;
- dokumentovanje obaveznih i opcionih polja i predviđenog prikaza.

Apple `eventTicket` i Google `EventTicket` mapiranje, potpisivanje i generisanje gotovih Wallet fajlova nisu deo ove implementacije. To se obrađuje u narednim zadacima.

## 8. Validacija i testiranje

- Šema: `schema.json`
- Testni primer: `example.json`
- Validator: `validator.py`
- Testovi: `backend/tests/test_canonical_ticket.py`

Testovi proveravaju validan primer, obavezna polja, tipove i format vrednosti, nedozvoljena polja i vremenski redosled događaja.
