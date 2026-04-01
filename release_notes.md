# World Time Specialist 1.0.2

## English

### New in 1.0.2

- Alarm playback duration is now enforced correctly: if you set 120 seconds, the alarm keeps playing for the full 120 seconds.
- Alarm sound playback is now isolated with internal stop-timer tokens, preventing premature cutoff when other sounds are triggered.
- Added support for custom alarm audio files (for example MP3 and other formats supported by Windows MCI).
- New field in alarm editor: custom sound file picker (`🎵 Browse`).
- Custom alarm files are saved in alarm settings and restored after restart.
- Alarm table now shows custom file labels in the Sound column (for example `Custom: filename.mp3`).
- If a custom file is longer than the configured ring duration, playback is cut exactly at the configured duration.
- If a custom file is shorter than the configured ring duration, playback repeats until the configured duration ends.
- Added upcoming DST switch moments (winter -> summer and summer -> winter) in zone details.
- Added upcoming DST switch moments in Universal Converter output (source and target zones).

### Assets

- `WorldTimeSpecialist-Portable.exe`
- `WorldTimeSpecialist-Setup.exe`
- `build-scripts.zip` (build scripts + NSIS + spec)
- `checksums.txt`

---

## Polski

### Nowości w 1.0.2

- Długość dzwonienia alarmu działa teraz poprawnie: jeśli ustawisz 120 sekund, alarm gra pełne 120 sekund.
- Odtwarzanie alarmu ma teraz bezpieczne tokenowanie i kontrolę timera stopu, więc nie ucina się przed czasem przez inne dźwięki.
- Dodano obsługę własnych plików audio alarmu (np. MP3 i inne formaty wspierane przez Windows MCI).
- W formularzu alarmu dodano nowe pole wyboru własnego pliku dźwięku (`🎵 Wybierz`).
- Własny plik dźwięku alarmu zapisuje się w ustawieniach i wraca po ponownym uruchomieniu aplikacji.
- Tabela alarmów pokazuje własny plik w kolumnie Dźwięk (np. `Własny: plik.mp3`).
- Gdy własny plik jest dłuższy niż ustawiona długość alarmu, odtwarzanie kończy się dokładnie po ustawionym czasie.
- Gdy własny plik jest krótszy niż ustawiona długość alarmu, odtwarzanie zapętla się do końca ustawionego czasu.
- Dodano informacje o najbliższych momentach zmiany DST (z zimowego na letni oraz z letniego na zimowy) w szczegółach strefy.
- Dodano informacje o najbliższych zmianach DST także w wyniku Uniwersalnego Konwertera (dla strefy źródłowej i docelowej).

### Załączniki

- `WorldTimeSpecialist-Portable.exe`
- `WorldTimeSpecialist-Setup.exe`
- `build-scripts.zip` (skrypty build + NSIS + spec)
- `checksums.txt`
