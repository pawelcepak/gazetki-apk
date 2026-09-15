# Moje Gazetki — v0.1

Własna aplikacja webowa/PWA do przeglądania aktualnych i nadchodzących gazetek promocyjnych.

## Dlaczego web/PWA?

Jedna baza kodu działa na:
- Linuxie,
- Windowsie,
- Androidzie,
- innych urządzeniach z nowoczesną przeglądarką.

Po wdrożeniu przez HTTPS aplikację można zainstalować z przeglądarki jako PWA i uruchamiać podobnie jak zwykłą aplikację.

## v0.1

- responsywny interfejs,
- wybór własnych sklepów,
- własna kolejność sklepów,
- filtrowanie: aktualne / nadchodzące / wszystkie,
- sortowanie,
- wyszukiwarka,
- zapis ustawień w localStorage,
- przygotowany manifest PWA i service worker,
- dane demonstracyjne do czasu podłączenia rzeczywistych źródeł.

## Plan

### v0.2
- warstwa adapterów źródeł danych,
- pobieranie rzeczywistych aktualnych i nadchodzących gazetek,
- odnośnik do oryginalnej gazetki,
- cache i obsługa błędów źródeł.

### v0.3
- wyszukiwanie produktów/promocji,
- obserwowane produkty,
- reguły cenowe.

### v0.4
- powiadomienia,
- harmonogram sprawdzania,
- lista zakupów.

### v0.5
- porównywanie cen/koszyka pomiędzy sklepami.

## Uruchomienie lokalne

Najprościej uruchomić statyczny serwer HTTP w katalogu repozytorium.

Python:

```bash
python -m http.server 8080
```

Następnie otwórz:

```text
http://localhost:8080
```

Niektóre funkcje PWA wymagają localhost albo HTTPS.

## Struktura

- `index.html` — interfejs,
- `styles.css` — wygląd responsywny,
- `app.js` — logika aplikacji,
- `manifest.webmanifest` — instalacja PWA,
- `sw.js` — cache/offline.

## Ważne

v0.1 nie udaje, że pobiera prawdziwe gazetki. Dane w kartach są demonstracyjne. Prawdziwe źródła zostaną podłączone w kolejnej wersji przez adaptery, aby można było dodawać i zmieniać dostawców bez przebudowy UI.
