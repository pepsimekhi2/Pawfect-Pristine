# Auth Testing Playbook

## Endpoints
- POST `/api/auth/register` — body: `{name, email, password}` → returns `{user, token}`, sets bearer token
- POST `/api/auth/login` — body: `{email, password}` → returns `{user, token}`
- GET `/api/auth/me` — header `Authorization: Bearer <token>` → returns user
- POST `/api/auth/logout` — clears cookies (token revocation handled client-side by dropping token)

## Test credentials
- Admin: `admin@pawfectpristine.local` / `Pawfect2026!`
- Brand new user: create via `/api/auth/register`

## Notes
- Uses bcrypt for password hashing (hashes start with `$2b$`)
- Uses PyJWT (HS256, 7-day access token for simplicity)
- Token returned in JSON body AND in `access_token` httpOnly cookie
- Frontend stores token in localStorage and attaches `Authorization: Bearer` for protected calls
- Indexes: users.email unique, login_attempts.identifier
- Brute force: 5 failed attempts → 15-min lockout per (ip+email)

## Curl examples
```
TOKEN=$(curl -s -X POST $BACKEND_URL/api/auth/login -H "Content-Type: application/json" -d '{"email":"admin@pawfectpristine.local","password":"Pawfect2026!"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['token'])")
curl -s $BACKEND_URL/api/auth/me -H "Authorization: Bearer $TOKEN"
curl -s $BACKEND_URL/api/bookings/me -H "Authorization: Bearer $TOKEN"
```
