import { act, renderHook } from '@testing-library/react';

import useCountdown from '../useCountdown';

describe('useCountdown', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    describe('Initial render', () => {
        it('Immediately calculates and displays time on mount', () => {
            const expiresAt = new Date(Date.now() + 1000 * 60 * 60);
            const { result } = renderHook(() => useCountdown(expiresAt));
            expect(result.current).toBe('01:00:00');
        });

        it('Returns 00:00:00 when expiresAt is in the past', () => {
            const expiresAt = new Date(Date.now() - 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));
            expect(result.current).toBe('00:00:00');
        });

        it('Returns 00:00:00 when expiresAt is exactly now', () => {
            const expiresAt = new Date(Date.now());
            const { result } = renderHook(() => useCountdown(expiresAt));
            expect(result.current).toBe('00:00:00');
        });
    });

    describe('Time formatting', () => {
        it('Pads hours with leading zero', () => {
            const expiresAt = new Date(Date.now() + 1 * 60 * 60 * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));
            expect(result.current).toBe('01:00:00');
        });

        it('Pads minutes with leading zero', () => {
            const expiresAt = new Date(Date.now() + 5 * 60 * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));
            expect(result.current).toBe('00:05:00');
        });

        it('Pads seconds with leading zero', () => {
            const expiresAt = new Date(Date.now() + 9 * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));
            expect(result.current).toBe('00:00:09');
        });

        it('Formats HH:MM:SS correctly for a complex time', () => {
            const expiresAt = new Date(Date.now() + (2 * 3600 + 34 * 60 + 56) * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));
            expect(result.current).toBe('02:34:56');
        });

        it('Handles large hour values without truncation', () => {
            const expiresAt = new Date(Date.now() + 25 * 60 * 60 * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));
            expect(result.current).toBe('25:00:00');
        });

        it('Matches HH:MM:SS format', () => {
            const expiresAt = new Date(Date.now() + 3661 * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));
            expect(result.current).toMatch(/^\d{2}:\d{2}:\d{2}$/);
        });
    });

    describe('Countdown ticking', () => {
        it('Decrements by 1 second after 1 second passes', () => {
            const expiresAt = new Date(Date.now() + 10 * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));

            expect(result.current).toBe('00:00:10');
            act(() => {
                jest.advanceTimersByTime(1000);
            });
            expect(result.current).toBe('00:00:09');
        });

        it('Decrements correctly across multiple seconds', () => {
            const expiresAt = new Date(Date.now() + 5 * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));

            expect(result.current).toBe('00:00:05');
            act(() => {
                jest.advanceTimersByTime(1000);
            });
            expect(result.current).toBe('00:00:04');
            act(() => {
                jest.advanceTimersByTime(1000);
            });
            expect(result.current).toBe('00:00:03');
            act(() => {
                jest.advanceTimersByTime(1000);
            });
            expect(result.current).toBe('00:00:02');
        });

        it('Transitions from minutes to seconds correctly', () => {
            const expiresAt = new Date(Date.now() + 61 * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));

            expect(result.current).toBe('00:01:01');
            act(() => {
                jest.advanceTimersByTime(1000);
            });
            expect(result.current).toBe('00:01:00');
            act(() => {
                jest.advanceTimersByTime(1000);
            });
            expect(result.current).toBe('00:00:59');
        });

        it('Transitions from hours to minutes correctly', () => {
            const expiresAt = new Date(Date.now() + 3601 * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));

            expect(result.current).toBe('01:00:01');
            act(() => {
                jest.advanceTimersByTime(1000);
            });
            expect(result.current).toBe('01:00:00');
            act(() => {
                jest.advanceTimersByTime(1000);
            });
            expect(result.current).toBe('00:59:59');
        });

        it('Shows 00:00:00 when timer expires', () => {
            const expiresAt = new Date(Date.now() + 2 * 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));

            expect(result.current).toBe('00:00:02');
            act(() => {
                jest.advanceTimersByTime(2000);
            });
            expect(result.current).toBe('00:00:00');
        });

        it('Remains at 00:00:00 after expiry', () => {
            const expiresAt = new Date(Date.now() + 1000);
            const { result } = renderHook(() => useCountdown(expiresAt));

            act(() => {
                jest.advanceTimersByTime(1000);
            });
            expect(result.current).toBe('00:00:00');
            act(() => {
                jest.advanceTimersByTime(5000);
            });
            expect(result.current).toBe('00:00:00');
        });
    });

    describe('Interval management', () => {
        it('Sets up an interval on mount', () => {
            const setIntervalSpy = jest.spyOn(global, 'setInterval');
            const expiresAt = new Date(Date.now() + 10000);
            renderHook(() => useCountdown(expiresAt));
            expect(setIntervalSpy).toHaveBeenCalledWith(expect.any(Function), 1000);
            setIntervalSpy.mockRestore();
        });

        it('Clears the interval on unmount', () => {
            const clearIntervalSpy = jest.spyOn(global, 'clearInterval');
            const expiresAt = new Date(Date.now() + 10000);
            const { unmount } = renderHook(() => useCountdown(expiresAt));
            unmount();
            expect(clearIntervalSpy).toHaveBeenCalled();
            clearIntervalSpy.mockRestore();
        });

        it('Clears old interval and starts new one when expiresAt changes', () => {
            const clearIntervalSpy = jest.spyOn(global, 'clearInterval');
            const expiresAt1 = new Date(Date.now() + 10000);
            const expiresAt2 = new Date(Date.now() + 20000);

            const { rerender } = renderHook(({ expiresAt }) => useCountdown(expiresAt), {
                initialProps: { expiresAt: expiresAt1 },
            });

            rerender({ expiresAt: expiresAt2 });
            expect(clearIntervalSpy).toHaveBeenCalled();
            clearIntervalSpy.mockRestore();
        });
    });

    describe('ExpiresAt changes', () => {
        it('Recalculates immediately when expiresAt changes', () => {
            const expiresAt1 = new Date(Date.now() + 5000);
            const { result, rerender } = renderHook(({ expiresAt }) => useCountdown(expiresAt), {
                initialProps: { expiresAt: expiresAt1 },
            });

            expect(result.current).toBe('00:00:05');

            const expiresAt2 = new Date(Date.now() + 10000);
            rerender({ expiresAt: expiresAt2 });
            expect(result.current).toBe('00:00:10');
        });

        it('Handles switching from future to past expiresAt', () => {
            const expiresAt1 = new Date(Date.now() + 10000);
            const { result, rerender } = renderHook(({ expiresAt }) => useCountdown(expiresAt), {
                initialProps: { expiresAt: expiresAt1 },
            });

            expect(result.current).toBe('00:00:10');

            const expiresAt2 = new Date(Date.now() - 1000);
            rerender({ expiresAt: expiresAt2 });
            expect(result.current).toBe('00:00:00');
        });
    });
});
