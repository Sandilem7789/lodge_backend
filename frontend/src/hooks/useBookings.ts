import { useState, useEffect, useCallback } from 'react';
import { getBookings, createBooking, cancelBooking } from '../api';

export type Booking = {
  id?: number;
  confirmationNumber?: string;
  status?: string;
  type?: string;
  name?: string;
  email?: string;
  phone?: string;
  checkIn?: string;
  checkOut?: string;
  guests?: number;
  message?: string;
  cancelledAt?: string | null;
  cancellationReason?: string | null;
};

export function useBookings(initialParams?: Record<string, any>) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async (params?: Record<string, any>) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getBookings(params || initialParams);
      if (res.status >= 200 && res.status < 300) {
        // API returns { message, data }
        setBookings(res.data.data || []);
      } else {
        setError(`Failed to fetch bookings: ${res.status}`);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [initialParams]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  const create = useCallback(async (payload: Record<string, any>) => {
    setLoading(true);
    setError(null);
    try {
      const res = await createBooking(payload);
      if (res.status === 201) {
        const created = res.data.data;
        setBookings((prev) => [created, ...prev]);
        return { success: true, booking: created };
      }
      return { success: false, error: res.data };
    } catch (e: any) {
      return { success: false, error: e.message };
    } finally {
      setLoading(false);
    }
  }, []);

  const cancel = useCallback(async (confirmationNumber: string, reason?: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await cancelBooking(confirmationNumber, reason);
      if (res.status === 200) {
        const updated = res.data.data;
        setBookings((prev) => prev.map((b) => (b.confirmationNumber === updated.confirmationNumber ? updated : b)));
        return { success: true, booking: updated };
      }
      return { success: false, error: res.data };
    } catch (e: any) {
      return { success: false, error: e.message };
    } finally {
      setLoading(false);
    }
  }, []);

  return { bookings, loading, error, fetchBookings: fetch, createBooking: create, cancelBooking: cancel };
}
