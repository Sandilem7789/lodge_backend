// Frontend API helper (TypeScript)
// - Frontend uses camelCase internally
// - This module converts request payload keys to snake_case before sending
// - Converts response keys to camelCase before returning to components

type AnyObject = { [k: string]: any };

function toSnake(obj: AnyObject): AnyObject {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return obj;
  const result: AnyObject = {};
  Object.keys(obj).forEach((key) => {
    const val = obj[key];
    const snakeKey = key.replace(/[A-Z]/g, (m) => `_${m.toLowerCase()}`);
    if (Array.isArray(val)) result[snakeKey] = val.map((v) => (typeof v === 'object' ? toSnake(v) : v));
    else if (val && typeof val === 'object') result[snakeKey] = toSnake(val);
    else result[snakeKey] = val;
  });
  return result;
}

function toCamel(obj: AnyObject): AnyObject {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return obj;
  const result: AnyObject = {};
  Object.keys(obj).forEach((key) => {
    const val = obj[key];
    const camelKey = key.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
    if (Array.isArray(val)) result[camelKey] = val.map((v) => (typeof v === 'object' ? toCamel(v) : v));
    else if (val && typeof val === 'object') result[camelKey] = toCamel(val);
    else result[camelKey] = val;
  });
  return result;
}

async function request(method: string, path: string, body?: any) {
  const base = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api';
  const url = `${base}${path}`;
  const opts: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  };

  if (body !== undefined) {
    // convert camelCase body -> snake_case
    opts.body = JSON.stringify(toSnake(body));
  }

  const res = await fetch(url, opts);
  const text = await res.text();
  if (!text) return { status: res.status, data: null };
  let json: any;
  try {
    json = JSON.parse(text);
  } catch (e) {
    throw new Error(`Invalid JSON response from ${url}`);
  }

  // If response contains an object under 'data', transform that; otherwise transform entire payload
  if (json && typeof json === 'object') {
    if (json.data) json.data = Array.isArray(json.data) ? json.data.map((d: any) => toCamel(d)) : toCamel(json.data);
    // also transform any top-level keys (if you prefer direct object)
    const transformed: any = { ...json };
    return { status: res.status, data: transformed };
  }

  return { status: res.status, data: toCamel(json) };
}

export async function getBookings(params?: Record<string, any>) {
  const query = params
    ?
      '?' +
      Object.keys(params)
        .map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`)
        .join('&')
    : '';
  return request('GET', `/bookings/${query}`);
}

export async function createBooking(payload: Record<string, any>) {
  // payload expected in camelCase by frontend
  return request('POST', '/bookings/', payload);
}

export async function cancelBooking(confirmationNumber: string, cancellationReason?: string) {
  const body = cancellationReason ? { cancellationReason } : undefined; // camelCase
  return request('PATCH', `/bookings/${confirmationNumber}/cancel/`, body);
}

export async function groupedBookings(params?: Record<string, any>) {
  const query = params
    ?
      '?' +
      Object.keys(params)
        .map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`)
        .join('&')
    : '';
  return request('GET', `/bookings/grouped/${query}`);
}

export { toCamel, toSnake };
