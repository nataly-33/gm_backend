# API Contract

## Auth
```
POST /api/auth/register/        Body: {email, password, full_name}  → {user, access, refresh}
POST /api/auth/login/           Body: {email, password}             → {access, refresh}
POST /api/auth/refresh/         Body: {refresh}                     → {access}
GET  /api/auth/me/              (auth requerida)                    → {id, email, full_name, credit_balance, role}
POST /api/auth/logout/          (auth requerida)  Body: {refresh}  → 204
POST /api/auth/change-password/ (auth requerida)  Body: {old_password, new_password} → 200
```

## Songs
```
POST  /api/songs/generate/           Body: {title, description?, prompt?, lyrics?, described_lyrics?, instrumental?, guidance_scale?}  → {job_id, song_id, status}
GET   /api/songs/jobs/{id}/          → {status, song_id, error_message}
GET   /api/songs/library/            → [{id, title, status, audio_s3_key, thumbnail_s3_key, tags, created_at}]
GET   /api/songs/{id}/               → canción completa
GET   /api/songs/{id}/play-url/      → {url}  (URL firmada S3, expira 1h)
GET   /api/songs/{id}/thumbnail-url/ → {url}  (URL firmada S3)
PATCH /api/songs/{id}/               Body: {title?, is_public?}  → canción actualizada
DELETE /api/songs/{id}/              → 204 (soft delete)
POST  /api/songs/{id}/like/          → {liked: true/false}
GET   /api/songs/tags/               → [{id, name, category, emoji}]
```

## Credits
```
GET  /api/credits/balance/           → {balance, plan}
GET  /api/credits/plans/             → [{slug, name, credits_per_month, price_usd, features}]
POST /api/credits/checkout/          Body: {plan_slug}  → {checkout_url}
POST /api/credits/stripe-webhook/    (Stripe llama esto — no requiere auth JWT)
GET  /api/credits/transactions/      → [{amount, type, balance_after, created_at}]
```

## Community
```
GET  /api/community/trending/        → [{canción + like_count + play_count}] (top 10, últimos 2 días)
GET  /api/community/feed/            → canciones públicas paginadas
POST /api/community/plays/           Body: {song_id, seconds_played, source}  → 201
```
