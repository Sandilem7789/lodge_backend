Ikhaya Lami Lodge — Data Naming Conventions

Frontend (React/TypeScript)
- Use camelCase for all state, props, and internal variable names (e.g., checkIn, checkOut, confirmationNumber).
- API service layer (`frontend/src/api.ts`) must convert camelCase -> snake_case for outgoing requests.
- API service layer must convert snake_case -> camelCase for incoming responses.
- Components and hooks must only work with camelCase keys.

Backend (Django/DRF)
- Use snake_case in models, serializers, and API responses (e.g., check_in, check_out, confirmation_number).
- Ensure serializers expose the following consistent keys in responses: id, type, name, email, phone, check_in, check_out, guests, message, status, confirmation_number, created_at, cancelled_at (optional), cancellation_reason (optional).
- Query params/filters use snake_case (start_date, end_date, status, search, name).

Transformation Layer
- `frontend/src/api.ts` converts between naming styles and is the single place to do that conversion.
- Backend code never needs to perform camelCase conversions.

Developer Guidelines
- Always include these naming rules in prompts for both frontend and backend Copilot.
- Frontend Copilot: confirm payloads are transformed before sending.
- Backend Copilot: confirm serializers expose snake_case consistently.
- Copilot feedback must be succinct: list files updated, functions added/changed, and tests created.

Examples
- Frontend state: `{ checkIn: '2025-12-10', checkOut: '2025-12-12', guests: 2 }`
- Outgoing JSON (to backend): `{ "check_in": "2025-12-10", "check_out": "2025-12-12", "guests": 2 }`
- Backend response body: `{ "data": { "confirmation_number": "ABC123", "check_in": "2025-12-10", ... } }`
- Frontend receives response and uses `confirmationNumber` in components.

Automation
- When generating new endpoints or UI, ensure the transformation layer is wired and tested with at least one example call.
