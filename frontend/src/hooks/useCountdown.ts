import { useEffect, useState } from 'react';

/**
 * Counts down to a given expiry date, updating every second.
 * Returns the remaining time as a `HH:MM:SS` string.
 * Returns `"00:00:00"` once the expiry date has passed.
 *
 * @param expiresAt - The date and time to count down to.
 * @returns The remaining time formatted as `HH:MM:SS`.
 */
export default function useCountdown(expiresAt: Date) {
    const [timeLeft, setTimeLeft] = useState<string>('');

    useEffect(() => {
        function calculate() {
            const diff = expiresAt.getTime() - Date.now();

            if (diff <= 0) {
                setTimeLeft('00:00:00');
                return;
            }

            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            setTimeLeft(
                `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
            );
        }

        calculate();
        const interval = setInterval(calculate, 1000);
        return () => clearInterval(interval);
    }, [expiresAt]);

    return timeLeft;
}
