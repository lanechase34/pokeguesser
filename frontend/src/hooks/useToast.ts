import { useCallback, useEffect, useState } from 'react';

interface UseToastOptions {
    /** Duration in milliseconds before the toast auto-dismisses. Defaults to 4000. */
    autoDismissMs?: number;
}

export interface UseToastReturn {
    /** The current toast message, or `null` if no toast is active */
    message: string | null;
    /** Displays a toast with the given message, resetting the auto-dismiss timer */
    show: (msg: string) => void;
    /** Immediately clears the active toast message */
    dismiss: () => void;
}

/**
 * Manages a single toast message with optional auto-dismiss behaviour.
 *
 * @param options - Configuration options for the toast.
 * @param options.autoDismissMs - How long to show the toast before clearing it. Defaults to 4000ms.
 * @returns The current message, a setter to show a toast, and a dismiss function.
 */
export default function useToast({ autoDismissMs = 4000 }: UseToastOptions = {}): UseToastReturn {
    const [message, setMessage] = useState<string | null>(null);

    const show = useCallback((msg: string) => setMessage(msg), []);
    const dismiss = useCallback(() => setMessage(null), []);

    useEffect(() => {
        if (!message) return;
        const timer = setTimeout(() => setMessage(null), autoDismissMs);
        return () => clearTimeout(timer);
    }, [message, autoDismissMs]);

    return { message, show, dismiss };
}
