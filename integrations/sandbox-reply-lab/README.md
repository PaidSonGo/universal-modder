# Sandbox Reply Lab ↔ REA ↔ Termux

Integracja do analizy **własnych lub autoryzowanych** APK/XAPK. Lokalny silnik REA pochodzi z istniejącego repozytorium [PaidSonGo/rea](https://github.com/PaidSonGo/rea) (wersja 6.4.0). Nie przechowujemy drugiej kopii silnika ani żadnych danych aplikacji.

## Stan dostarczenia

- W tym katalogu znajdują się instalator oraz lokalny serwer do komunikacji z Androidem.
- Androidowy projekt **Sandbox Reply Lab v0.5** nie znajduje się jeszcze w tej gałęzi. Nie traktuj tego katalogu jako kompletnej aplikacji ani potwierdzonego APK.
- Głęboka analiza APK na Android/ARM wymaga kompatybilnego JADX/JVM. REA może obsługiwać tylko wybrane operacje.
- Shizuku nie zapewnia dostępu do pamięci cudzych aplikacji ani do oryginalnych kluczy podpisujących.
- Lokalny skaner edycji wartości działa tylko z aplikacjami, które jawnie udostępniają interfejs debugowania.

## Instalacja w Termux

**Przed instalacją podłącz telefon do zasilania.** Kompilacja REA pobiera zależności i może obciążyć CPU oraz pamięć.

```bash
pkg install -y git python
git clone --depth=1 --branch feature/sandbox-reply-lab-termux \
  https://github.com/PaidSonGo/universal-modder.git "$HOME/srl-integration"
bash "$HOME/srl-integration/integrations/sandbox-reply-lab/setup_termux.sh"
```

Instalator nie usuwa istniejącego REA, nie nadpisuje repozytorium i przerywa instalację przy wykrytym niskim poziomie baterii.

Po pomyślnym zbudowaniu:

```bash
python "$HOME/srl-integration/integrations/sandbox-reply-lab/rea_local_server.py" \
  --rea-dir "$HOME/srl-upstream/rea"
```

Serwer wyświetli losowy token. Wklej go do panelu REA w Sandbox Reply Lab. Endpoint **127.0.0.1:18767** jest dostępny wyłącznie lokalnie.

## API lokalne

- `GET /health` — weryfikacja z nagłówkiem `X-Sandbox-Token`.
- `POST /analyze` — plik APK lub XAPK w body, nagłówki `X-Sandbox-Token`, `X-Rea-Mode: inventory|deep`, `X-Package-Type: apk|xapk`.
- Limit rozmiaru 128 MiB, limit czasu REA 120 s.
- Wyniki to raporty, nie modyfikacje plików APK.

## Sprawdzenie gotowości

```bash
python -m py_compile "$HOME/srl-integration/integrations/sandbox-reply-lab/rea_local_server.py"
test -f "$HOME/srl-upstream/rea/dist/cli-runtime/cli.js" && echo "REA runtime OK"
```

## Brak automatycznej aktualizacji aplikacji

Ten moduł **nie podpisuje APK innych autorów** ani nie omija płatności, reklam czy kontroli integralności. Własną aplikację można przebudować i podpisać posiadanym kluczem zgodnie z Android SDK.
