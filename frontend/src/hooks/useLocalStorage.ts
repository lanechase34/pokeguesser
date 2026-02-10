import { useState, useEffect, useMemo } from 'react';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';

interface Transform<T, S = string> {
    toStorage: (value: T) => S;
    fromStorage: (value: S) => T;
}

// Generic interface for intitialValue
interface UseLocalStorageOptions<T> {
    key: string;
    initialValue: T; // type for the state
    transform?: Transform<T>; // configurable transform functions going to and from localstorage
}

// Predefined helper transform functions
export const dayjsTransform: Transform<Dayjs | null> = {
    toStorage: (date) => date?.toISOString() ?? '',
    fromStorage: (str) => (str ? dayjs(str) : null),
};

/**
 * Stores a value in local storage - will sync across browsers and supports following options
 * @key local storage key
 * @initialValue
 * @serialize custom serializer before sending to local storage
 * @deserialize custom deserializer after reading from local storage and rehydrating to state
 * @returns
 */
export default function useLocalStorage<T>({ key, initialValue, transform }: UseLocalStorageOptions<T>) {
    /**
     * Memoize transform functions to stable references
     */
    const toStorage = useMemo(() => transform?.toStorage ?? ((v: T) => JSON.stringify(v)), [transform]);
    const fromStorage = useMemo(() => transform?.fromStorage ?? ((v: string) => JSON.parse(v) as T), [transform]);

    /**
     * Attempt to load local storage value on mount
     */
    const [storedValue, setStoredValue] = useState<T>(() => {
        if (typeof window === 'undefined') {
            return initialValue;
        }

        try {
            const item = localStorage.getItem(key);
            if (item !== null) {
                return fromStorage(item);
            }

            localStorage.setItem(key, toStorage(initialValue));
            return initialValue;
        } catch (err: unknown) {
            console.error(`Error reading localStorage key "${key}":`, err);
            return initialValue;
        }
    });

    /**
     * Update local storage whenever value changes
     */
    useEffect(() => {
        try {
            localStorage.setItem(key, toStorage(storedValue));
        } catch (err: unknown) {
            console.error(`Error writing to localStorage key "${key}":`, err);
        }
    }, [key, storedValue, toStorage]);

    /**
     * Listen for changes in other tabs/windows and sync changes
     */
    useEffect(() => {
        if (typeof window === 'undefined') return;

        const handleStorageChange = (e: StorageEvent) => {
            if (e.key !== key) return;

            try {
                if (e.newValue !== null) {
                    setStoredValue(fromStorage(e.newValue));
                } else {
                    setStoredValue(initialValue);
                }
            } catch (error) {
                console.error(`Error parsing storage event for key "${key}":`, error);
            }
        };

        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, [key, initialValue, fromStorage]);

    /**
     * Match useState declaration
     */
    return [storedValue, setStoredValue] as const;
}
