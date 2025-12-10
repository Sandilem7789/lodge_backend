Summary of recent additions (succinct):

- Files created:
  - `frontend/src/api.ts` : API helper that converts camelCase ↔ snake_case and exposes `getBookings`, `createBooking`, `cancelBooking`, `groupedBookings`.
  - `frontend/src/hooks/useBookings.ts` : React hook (camelCase state) to list/create/cancel bookings; uses `api.ts`.
  - `frontend/src/components/BookingForm.tsx` : Example React component with camelCase form state and submits through `useBookings`.
  - `CONVENTIONS.md` : Project naming conventions and development guidelines.
  - `FEEDBACK.md` : This succinct summary.

- Backend files unchanged (already follow snake_case):
  - `bookings/models.py` : exposes snake_case fields including `check_in`, `check_out`, `confirmation_number`, `cancelled_at`, `cancellation_reason`.
  - `bookings/serializers.py` : exposes snake_case keys in API responses.
  - `bookings/views.py` : endpoints include filters (snake_case query params), grouped counts, cancel endpoint with `cancellation_reason`.
  - `bookings/urls.py` : new `grouped/` route added.

- Tests created:
  - `test_grouped.py` : script to validate grouped endpoint and cancellation logging.

Notes:
- Frontend `api.ts` uses environment variable `REACT_APP_API_BASE` (falls back to `http://localhost:8000/api`).
- All frontend code uses camelCase internally; conversions happen in `api.ts` only.
- Backend remains snake_case in models/serializers/views as required.

Next recommended actions (pick any):
- Add automated unit tests for the frontend transformation functions.
- Add authentication for staff dashboard frontend (CSRF + session or token-based).
- Add IP whitelist middleware for extra dashboard security.
