---
name: "kling-video-tiktok-poster"
description: "Generiše kratak vertikalni video Kling modelom (preko Higgsfield-a) iz teksta, traži odobrenje korisnika, pa ga objavljuje na povezani TikTok nalog."
---

# Kling → TikTok: generisanje i objava videa

Koristi ovaj skill kad korisnik želi da napravi video u Klingu (ili traži "video za TikTok", "napravi i postuj video" i sl.) i objavi ga na svoj TikTok nalog.

## Koraci

1. **Prikupi detalje o videu** (ako nisu već dati):
   - Koncept/prompt za video (šta se dešava, stil, ton)
   - Trajanje: 3–15 sekundi, podrazumevano 5 (Kling v3.0 limit)
   - Kvalitet (`mode`): std (podrazumevano) / pro / 4k — viši kvalitet košta više kredita
   - Zvuk (`sound`): on (podrazumevano) / off — off je jeftinije
   - Naslov/caption za TikTok (do 150 karaktera)
   - Da li žele muziku iz TikTok Commercial Music Library

2. **Proveri TikTok nalog** pozivom `tiktok_accounts`.
   - Ako nema aktivnog naloga → pozovi `tiktok_connect`, pošalji korisniku authorize_url, sačekaj da potvrdi da je odobrio pristup, pa ponovo proveri `tiktok_accounts` (status `active`).
   - Ako je nalog u statusu `error` → pozovi `tiktok_reconnect`.

3. **Preflight trošak generisanja**: pozovi `generate_video` sa `get_cost: true` da pokažeš korisniku koliko kredita košta (u zavisnosti od mode/sound/duration) pre nego što se bilo šta generiše. Sačekaj potvrdu ako je trošak značajan.

4. **Generiši video** pozivom `generate_video`:
   - `model: "kling3_0"` (podrazumevani izbor za Kling video)
   - `aspect_ratio: "9:16"` (vertikalni format za TikTok; model podržava i 16:9 i 1:1 ako korisnik izričito zatraži drugačiji format)
   - `prompt`: opis koji je korisnik dao
   - `params`: uključi `duration`, `mode`, `sound` prema koraku 1
   - Ako korisnik traži potpuno drugačiji model, koristi `models_explore` (action: recommend) da nađeš alternativu.

5. **Sačekaj generisanje** — koristi `jobs_wait` (ili prati generation widget ako je `generate_video` otvorio jedan). Kad je gotovo, prikaži korisniku rezultat (link/preview).

6. **Traži odobrenje sadržaja** — pitaj korisnika da li je video ok za objavu, ili želi izmenu prompta/parametara i regenerisanje. Ne nastavljaj na objavu bez eksplicitnog "da, objavi" ili ekvivalenta.

7. **Pripremi objavu** — pozovi `tiktok_prepare_publish`:
   - `connector_id`: aktivni nalog iz koraka 2
   - `mode: "DIRECT_POST"` (osim ako korisnik eksplicitno traži da ide samo u TikTok drafts — tada `UPLOAD_TO_DRAFT`)
   - `media_type: "VIDEO"`, `video_url`: Higgsfield-hosted URL generisanog videa
   - `title`: caption
   - `is_aigc: true` — video je AI-generisan, mora biti označen (TikTok AIGC disclosure)
   - Ostala prefill polja (privacy_level, allow_comment/duet/stitch) samo ako ih je korisnik već eksplicitno naveo

8. **Prikaži korisniku sve što `tiktok_prepare_publish` vrati** — preview, opcije privatnosti, sve `required_confirmations`. Postavi svako pitanje korisniku dok ne dobiješ jasan odgovor za svaku stavku (privatnost, AIGC disclosure, muzika ako je izabrana, branded content ako je primenjivo). Nikad ne pretpostavljaj "da" u njihovo ime.

9. **(Opciono) Muzika** — ako korisnik želi muziku, koristi `tiktok_music_trending` da predložiš pesme, i prosledi `music_sound_id` u `tiktok_publish` (samo za DIRECT_POST video).

10. **Objavi** — tek nakon što je korisnik eksplicitno potvrdio SVE stavke, pozovi `tiktok_publish` sa svim relevantnim `*_confirmed` poljima (uključujući `user_confirmed`, `preview_confirmed`) na `true`. Ovo je nepovratna javna objava — nikad je ne pokreći bez izričite poslednje potvrde korisnika u toj konkretnoj sesiji.

11. **Proveri status** — pozovi `tiktok_publish_status` da potvrdiš da je TikTok obradio i objavio post. Prenesi korisniku konačan status i link ako je dostupan.

## Bitna pravila

- Kvota: max 5 objava/min i 13/24h po nalogu. Ako dobiješ `cadence_burst`/`cadence_daily`, sačekaj `retry_after_seconds` — ne pokušavaj ponovo odmah.
- Mediji moraju biti Higgsfield-hosted URL (ne spoljni linkovi) i moraju zadovoljiti TikTok limite (MP4/WebM/MOV, do 1GB, 3–600s, min 360px, 23–60 FPS) — `tiktok_prepare_publish` ovo validira. Kling video (max 15s) uvek upada u ovaj opseg.
- Nikad ne objavljuj (`tiktok_publish`) bez svežeg, eksplicitnog "da" korisnika u TOJ sesiji za taj konkretan video — prethodno odobrenje ranijeg videa ne važi za novi.
- Ako korisnik samo traži da se video napravi bez objave, stani posle koraka 6.