import React, { useState } from 'react';
import { useBookings } from '../hooks/useBookings';

export default function BookingForm() {
  const { createBooking } = useBookings();
  const [form, setForm] = useState({
    type: 'chalet',
    name: '',
    email: '',
    phone: '',
    checkIn: '',
    checkOut: '',
    guests: 1,
    message: '',
  });

  const [status, setStatus] = useState<string | null>(null);

  function onChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: name === 'guests' ? Number(value) : value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('submitting');
    const res = await createBooking(form as any);
    if (res?.success) setStatus('created: ' + res.booking.confirmationNumber);
    else setStatus('error');
  }

  return (
    <form onSubmit={onSubmit}>
      <label>
        Type
        <select name="type" value={form.type} onChange={onChange}>
          <option value="chalet">Chalet</option>
          <option value="campsite">Campsite</option>
          <option value="conference">Conference</option>
          <option value="event">Event</option>
          <option value="safari">Safari</option>
        </select>
      </label>

      <label>
        Name
        <input name="name" value={form.name} onChange={onChange} />
      </label>

      <label>
        Email
        <input name="email" value={form.email} onChange={onChange} />
      </label>

      <label>
        Phone
        <input name="phone" value={form.phone} onChange={onChange} />
      </label>

      <label>
        Check In
        <input type="date" name="checkIn" value={form.checkIn} onChange={onChange} />
      </label>

      <label>
        Check Out
        <input type="date" name="checkOut" value={form.checkOut} onChange={onChange} />
      </label>

      <label>
        Guests
        <input type="number" name="guests" value={String(form.guests)} onChange={onChange} min={1} />
      </label>

      <label>
        Message
        <textarea name="message" value={form.message} onChange={onChange} />
      </label>

      <button type="submit">Book</button>

      {status && <div>{status}</div>}
    </form>
  );
}
