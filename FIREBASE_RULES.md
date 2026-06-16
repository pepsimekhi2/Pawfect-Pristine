# Firebase Realtime Database Rules — Pawfect & Pristine

Database URL: `https://mekhis-creations-default-rtdb.firebaseio.com/`

## How to install

1. Go to https://console.firebase.google.com/
2. Pick your `mekhis-creations` project
3. Left sidebar → **Realtime Database** → **Rules** tab
4. Paste the JSON below and click **Publish**

## Recommended rules (no client-side reads, server writes only)

These rules let the FastAPI backend mirror users + bookings to your RTDB via
the REST API (no auth token required), while keeping all data invisible to
anonymous browsers and unverified clients.

```json
{
  "rules": {
    ".read": false,
    ".write": false,

    "users": {
      "$uid": {
        ".write": true,
        ".read": false,
        ".validate": "newData.hasChildren(['id', 'email', 'name', 'role'])"
      }
    },

    "bookings": {
      "$bookingId": {
        ".write": true,
        ".read": false,
        ".validate": "newData.hasChildren(['id', 'service_value', 'grand_total'])"
      }
    },

    "user_bookings": {
      "$uid": {
        "$bookingId": {
          ".write": true,
          ".read": false
        }
      }
    }
  }
}
```

## Why these rules

- `"$key": { ".write": true }` lets the server PUT / PATCH at those paths over
  REST (since we don't have a Firebase Admin service-account credential).
- `.read: false` keeps the data invisible to random browsers — only you can
  see it inside the Firebase console.
- `.validate` blocks junk writes that don't include the right fields.

## When you want stricter rules

Once you add Firebase Auth (Email/Password) and a service-account credential
on the server, swap to these per-user rules:

```json
{
  "rules": {
    "users": {
      "$uid": {
        ".read": "auth != null && auth.uid == $uid",
        ".write": "auth != null && auth.uid == $uid"
      }
    },
    "bookings": {
      "$bookingId": {
        ".read":  "auth != null && (data.child('user_id').val() == auth.uid || root.child('users').child(auth.uid).child('role').val() == 'admin')",
        ".write": "auth != null"
      }
    },
    "user_bookings": {
      "$uid": {
        ".read":  "auth != null && auth.uid == $uid",
        ".write": "auth != null && auth.uid == $uid"
      }
    }
  }
}
```

## How the data lands in Firebase

After each booking the backend writes:

```
/bookings/{bookingId}        ← full booking record (with quote, eta, status)
/user_bookings/{uid}/{bookingId}  ← lightweight summary for that customer
/users/{uid}                 ← user profile (no password — only id/name/email/phone/role)
```

You can view it live at:
- https://mekhis-creations-default-rtdb.firebaseio.com/users.json
- https://mekhis-creations-default-rtdb.firebaseio.com/bookings.json
- https://mekhis-creations-default-rtdb.firebaseio.com/user_bookings.json

(Only visible inside the Firebase console with these rules — public REST calls
will return null because `.read: false`.)
