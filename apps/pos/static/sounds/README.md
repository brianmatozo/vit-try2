# Sound Assets for Vitalcer POS

Place audio files here for the POS cashier feedback:
- `beep.mp3` or `scan.mp3` — Played when a barcode is successfully recognized.
- `error.mp3` or `buzzer.mp3` — Played when a barcode is invalid, product not found, or error occurs.
- `success.mp3` or `checkout.mp3` — Played when a payment/sale is successfully completed.

If these files are not present, the app automatically falls back to clean Web Audio API synthesized tones.
