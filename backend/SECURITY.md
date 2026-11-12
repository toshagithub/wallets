# Bezbednost

## Čuvanje tajni

Tajne i privatni ključevi ne smeju biti čuvani u izvornom kodu niti
commitovani u repozitorijum.

Backend učitava konfiguraciju tajni preko environment promenljivih,
kroz centralnu `Settings` konfiguraciju.

Apple privatni ključ za potpisivanje passova čuva se van izvornog koda
kao šifrovani fajl. Lozinka za dešifrovanje ključa čuva se kroz
backend environment konfiguraciju.

Tajne ne smeju biti ispisivane u logovima niti u porukama o greškama.

## Rotacija Apple privatnog ključa

Kada je potrebno zameniti Apple privatni ključ:

1. Generisati ili pribaviti novi Apple privatni ključ.
2. Šifrovati novi privatni ključ novom jakom lozinkom.
3. Postaviti šifrovani ključ u direktorijum predviđen za tajne.
4. Ažurirati `APPLE_PRIVATE_KEY_PASSWORD` u backend environment konfiguraciji.
5. Restartovati backend.
6. Generisati testni Apple Wallet pass.
7. Proveriti da generisanje i potpisivanje passa uspešno rade.
8. Nakon uspešne provere povući stari privatni ključ.
9. Zabeležiti datum i izvršenu promenu.

Privatni ključ se nikada ne sme commitovati u repozitorijum niti
ispisivati u logovima ili porukama o greškama.

## Rotacija JWT tajne

Kada je potrebno zameniti `JWT_SECRET`:

1. Generisati novu jaku nasumičnu tajnu.
2. Zameniti vrednost `JWT_SECRET` u backend environment konfiguraciji.
3. Restartovati backend.
4. Proveriti da prijava korisnika i generisanje novih tokena rade.
5. Tokeni potpisani prethodnom tajnom više se ne smatraju važećim nakon rotacije.

Rotaciju treba izvršiti pre isteka tajne ili odmah ukoliko postoji sumnja
da je tajna kompromitovana.
