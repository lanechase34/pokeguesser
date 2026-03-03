import { useEffect, useState } from 'react';

export default function useCountdown(expiresAt: Date): string {
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
