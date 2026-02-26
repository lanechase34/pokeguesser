import { act, renderHook } from '@testing-library/react';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import useLocalStorage, { dayjsTransform } from 'hooks/useLocalStorage';

describe('useLocalStorage', () => {
    const KEY = 'test-key';

    beforeEach(() => {
        localStorage.clear();
        jest.clearAllMocks();
        jest.spyOn(console, 'error').mockImplementation(() => {
            // Silence expected errors
        });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    describe('Initialization', () => {
        it('Should initialize with initialValue when localStorage is empty', () => {
            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 'default' }));

            expect(result.current[0]).toBe('default');
            expect(localStorage.getItem(KEY)).toBe(JSON.stringify('default'));
        });

        it('Should initialize from existing localStorage value', () => {
            localStorage.setItem(KEY, JSON.stringify('stored-value'));

            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 'default' }));

            expect(result.current[0]).toBe('stored-value');
        });

        it('Should handle various data types', () => {
            const testCases = [
                { value: true, expected: true },
                { value: 42, expected: 42 },
                { value: { nested: 'object' }, expected: { nested: 'object' } },
                { value: ['array', 'items'], expected: ['array', 'items'] },
                { value: null, expected: null },
            ];

            testCases.forEach(({ value, expected }, index) => {
                const testKey = `${KEY}-${index}`;
                const { result } = renderHook(() => useLocalStorage({ key: testKey, initialValue: value }));

                expect(result.current[0]).toEqual(expected);
            });
        });

        it('Should handle corrupted localStorage data gracefully', () => {
            localStorage.setItem(KEY, '{invalid json}');

            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 'fallback' }));

            expect(result.current[0]).toBe('fallback');
            expect(console.error).toHaveBeenCalledWith(
                expect.stringContaining(`Error reading localStorage key "${KEY}"`),
                expect.any(Error)
            );
        });

        it('Should handle localStorage.getItem throwing error', () => {
            jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
                throw new Error('Storage quota exceeded');
            });

            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 'fallback' }));

            expect(result.current[0]).toBe('fallback');
            expect(console.error).toHaveBeenCalled();
        });
    });

    describe('State updates', () => {
        it('Should update localStorage when value changes', () => {
            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 0 }));

            act(() => {
                result.current[1](42);
            });

            expect(result.current[0]).toBe(42);
            expect(localStorage.getItem(KEY)).toBe(JSON.stringify(42));
        });

        it('Should handle multiple rapid updates', () => {
            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 0 }));

            act(() => {
                result.current[1](1);
                result.current[1](2);
                result.current[1](3);
            });

            expect(result.current[0]).toBe(3);
            expect(localStorage.getItem(KEY)).toBe(JSON.stringify(3));
        });

        it('Should handle functional updates', () => {
            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 10 }));

            act(() => {
                result.current[1]((prev) => prev + 5);
            });

            expect(result.current[0]).toBe(15);
            expect(localStorage.getItem(KEY)).toBe(JSON.stringify(15));
        });

        it('Should handle localStorage.setItem throwing error', () => {
            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 'initial' }));

            jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
                throw new Error('Storage quota exceeded');
            });

            act(() => {
                result.current[1]('new-value');
            });

            // State updates but localStorage write fails gracefully
            expect(result.current[0]).toBe('new-value');
            expect(console.error).toHaveBeenCalledWith(
                expect.stringContaining(`Error writing to localStorage key "${KEY}"`),
                expect.any(Error)
            );
        });
    });

    describe('Cross-tab synchronization', () => {
        it('Should sync state when storage event occurs for same key', () => {
            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 'initial' }));

            act(() => {
                window.dispatchEvent(
                    new StorageEvent('storage', {
                        key: KEY,
                        newValue: JSON.stringify('updated-from-tab'),
                    })
                );
            });

            expect(result.current[0]).toBe('updated-from-tab');
        });

        it('Should reset to initialValue when storage key is deleted', () => {
            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 'initial' }));

            act(() => {
                window.dispatchEvent(
                    new StorageEvent('storage', {
                        key: KEY,
                        newValue: null,
                    })
                );
            });

            expect(result.current[0]).toBe('initial');
        });

        it('Should ignore storage events for different keys', () => {
            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 'initial' }));

            const initialValue = result.current[0];

            act(() => {
                window.dispatchEvent(
                    new StorageEvent('storage', {
                        key: 'different-key',
                        newValue: JSON.stringify('should-be-ignored'),
                    })
                );
            });

            expect(result.current[0]).toBe(initialValue);
        });

        it('Should handle corrupted data in storage events gracefully', () => {
            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 'initial' }));

            act(() => {
                window.dispatchEvent(
                    new StorageEvent('storage', {
                        key: KEY,
                        newValue: '{invalid json}',
                    })
                );
            });

            // State should remain unchanged
            expect(result.current[0]).toBe('initial');
            expect(console.error).toHaveBeenCalledWith(
                expect.stringContaining(`Error parsing storage event for key "${KEY}"`),
                expect.any(Error)
            );
        });

        it('Should clean up event listener on unmount', () => {
            const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

            const { unmount } = renderHook(() => useLocalStorage({ key: KEY, initialValue: 'test' }));

            unmount();

            expect(removeEventListenerSpy).toHaveBeenCalledWith('storage', expect.any(Function));
        });
    });

    describe('Custom transforms', () => {
        it('Should use custom toStorage and fromStorage functions', () => {
            const customTransform = {
                toStorage: jest.fn((v: string) => `wrapped:${v}`),
                fromStorage: jest.fn((v: string) => v.replace('wrapped:', '')),
            };

            const { result } = renderHook(() =>
                useLocalStorage({
                    key: KEY,
                    initialValue: 'test',
                    transform: customTransform,
                })
            );

            expect(customTransform.toStorage).toHaveBeenCalledWith('test');
            expect(localStorage.getItem(KEY)).toBe('wrapped:test');

            act(() => {
                result.current[1]('new-value');
            });

            expect(customTransform.toStorage).toHaveBeenCalledWith('new-value');
            expect(localStorage.getItem(KEY)).toBe('wrapped:new-value');
        });

        it('Should deserialize from localStorage using custom transform', () => {
            localStorage.setItem(KEY, 'wrapped:stored-value');

            const customTransform = {
                toStorage: (v: string) => `wrapped:${v}`,
                fromStorage: (v: string) => v.replace('wrapped:', ''),
            };

            const { result } = renderHook(() =>
                useLocalStorage({
                    key: KEY,
                    initialValue: 'default',
                    transform: customTransform,
                })
            );

            expect(result.current[0]).toBe('stored-value');
        });

        it('Should work with dayjsTransform helper', () => {
            const testDate = dayjs('2026-03-15T10:30:00Z');

            const { result } = renderHook(() =>
                useLocalStorage<Dayjs | null>({
                    key: KEY,
                    initialValue: testDate,
                    transform: dayjsTransform,
                })
            );

            expect(result.current[0]?.toISOString()).toBe(testDate.toISOString());
            expect(localStorage.getItem(KEY)).toBe(testDate.toISOString());
        });

        it('Should handle null Dayjs values with dayjsTransform', () => {
            const { result } = renderHook(() =>
                useLocalStorage<Dayjs | null>({
                    key: KEY,
                    initialValue: null,
                    transform: dayjsTransform,
                })
            );

            expect(result.current[0]).toBeNull();
            expect(localStorage.getItem(KEY)).toBe('');

            const testDate = dayjs('2026-01-01');
            act(() => {
                result.current[1](testDate);
            });

            expect(result.current[0]?.toISOString()).toBe(testDate.toISOString());

            act(() => {
                result.current[1](null);
            });

            expect(result.current[0]).toBeNull();
            expect(localStorage.getItem(KEY)).toBe('');
        });

        it('Should handle storage events with custom transform', () => {
            const customTransform = {
                toStorage: (v: string) => `wrapped:${v}`,
                fromStorage: (v: string) => v.replace('wrapped:', ''),
            };

            const { result } = renderHook(() =>
                useLocalStorage({
                    key: KEY,
                    initialValue: 'initial',
                    transform: customTransform,
                })
            );

            act(() => {
                window.dispatchEvent(
                    new StorageEvent('storage', {
                        key: KEY,
                        newValue: 'wrapped:from-other-tab',
                    })
                );
            });

            expect(result.current[0]).toBe('from-other-tab');
        });
    });

    describe('Performance and stability', () => {
        it('Should not cause infinite re-renders with stable transform', () => {
            let renderCount = 0;

            const stableTransform = {
                toStorage: (v: string) => v.toUpperCase(),
                fromStorage: (v: string) => v.toLowerCase(),
            };

            const { rerender } = renderHook(() => {
                renderCount++;
                return useLocalStorage({
                    key: KEY,
                    initialValue: 'test',
                    transform: stableTransform,
                });
            });

            const initialRenderCount = renderCount;

            // Force multiple re-renders
            rerender();
            rerender();
            rerender();

            // Should only render 4 times total (initial + 3 rerenders)
            // Not infinite loop
            expect(renderCount).toBe(initialRenderCount + 3);
        });

        it('Should memoize transform functions correctly', () => {
            const transform = {
                toStorage: jest.fn((v: number) => String(v)),
                fromStorage: jest.fn((v: string) => parseInt(v, 10)),
            };

            const { rerender } = renderHook((props) => useLocalStorage(props), {
                initialProps: {
                    key: KEY,
                    initialValue: 0,
                    transform,
                },
            });

            const initialToStorageCalls = transform.toStorage.mock.calls.length;

            // Rerender without changing transform
            rerender({
                key: KEY,
                initialValue: 0,
                transform,
            });

            // toStorage should not be called again (just initial write)
            expect(transform.toStorage.mock.calls.length).toBe(initialToStorageCalls);
        });

        it('Should handle transform changing between renders', () => {
            const transform1 = {
                toStorage: (v: string) => `v1:${v}`,
                fromStorage: (v: string) => v.replace('v1:', ''),
            };

            const transform2 = {
                toStorage: (v: string) => `v2:${v}`,
                fromStorage: (v: string) => v.replace('v2:', ''),
            };

            const { rerender } = renderHook((props) => useLocalStorage(props), {
                initialProps: {
                    key: KEY,
                    initialValue: 'test',
                    transform: transform1,
                },
            });

            expect(localStorage.getItem(KEY)).toBe('v1:test');

            // Change transform
            rerender({
                key: KEY,
                initialValue: 'test',
                transform: transform2,
            });

            // New transform should be applied
            expect(localStorage.getItem(KEY)).toBe('v2:test');
        });

        it('Should not re-write to localStorage unnecessarily on mount', () => {
            localStorage.setItem(KEY, JSON.stringify('existing'));
            const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');

            renderHook(() => useLocalStorage({ key: KEY, initialValue: 'default' }));

            // Should write once in the effect after mount
            expect(setItemSpy).toHaveBeenCalledTimes(1);
        });

        it('Should handle key changes correctly', () => {
            const { rerender } = renderHook((props) => useLocalStorage(props), {
                initialProps: {
                    key: 'key1',
                    initialValue: 'value1',
                },
            });

            expect(localStorage.getItem('key1')).toBe(JSON.stringify('value1'));

            // Change key
            rerender({
                key: 'key2',
                initialValue: 'value2',
            });

            // Should write to new key
            expect(localStorage.getItem('key2')).toBe(JSON.stringify('value1'));
        });
    });

    describe('Edge cases', () => {
        it('Should handle empty string as valid value', () => {
            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: '' }));

            expect(result.current[0]).toBe('');
            expect(localStorage.getItem(KEY)).toBe(JSON.stringify(''));

            act(() => {
                result.current[1]('non-empty');
            });

            expect(result.current[0]).toBe('non-empty');

            act(() => {
                result.current[1]('');
            });

            expect(result.current[0]).toBe('');
        });

        it('Should handle undefined in complex objects', () => {
            const complexObject = {
                defined: 'value',
                nullValue: null,
                // undefined will be lost in JSON.stringify
            };

            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: complexObject }));

            expect(result.current[0]).toEqual(complexObject);
        });

        it('Should handle very large data', () => {
            const largeArray = Array.from({ length: 1000 }, (_, i) => ({
                id: i,
                data: `item-${i}`,
            }));

            const { result } = renderHook(() => useLocalStorage({ key: KEY, initialValue: largeArray }));

            expect(result.current[0]).toEqual(largeArray);
        });

        it('Should handle special characters in key', () => {
            const specialKey = 'key-with-special-chars-!@#$%^&*()';

            const { result } = renderHook(() => useLocalStorage({ key: specialKey, initialValue: 'test' }));

            expect(result.current[0]).toBe('test');
            expect(localStorage.getItem(specialKey)).toBe(JSON.stringify('test'));
        });

        it('Should handle transform returning empty string', () => {
            const emptyStringTransform = {
                toStorage: () => '',
                fromStorage: () => 'default-value',
            };

            renderHook(() =>
                useLocalStorage({
                    key: KEY,
                    initialValue: 'test',
                    transform: emptyStringTransform,
                })
            );

            expect(localStorage.getItem(KEY)).toBe('');
        });
    });

    describe('Real-world scenarios', () => {
        it('Should work in authentication flow', () => {
            const { result } = renderHook(() => useLocalStorage({ key: 'isAuthenticated', initialValue: false }));

            expect(result.current[0]).toBe(false);

            // User logs in
            act(() => {
                result.current[1](true);
            });

            expect(result.current[0]).toBe(true);
            expect(localStorage.getItem('isAuthenticated')).toBe(JSON.stringify(true));

            // Simulate logout from another tab
            act(() => {
                window.dispatchEvent(
                    new StorageEvent('storage', {
                        key: 'isAuthenticated',
                        newValue: JSON.stringify(false),
                    })
                );
            });

            expect(result.current[0]).toBe(false);
        });

        it('Should work with DateRangeContext scenario', () => {
            const { result: rangeTypeResult } = renderHook(() =>
                useLocalStorage<'this-month' | 'last-month' | 'custom'>({
                    key: 'rangeType',
                    initialValue: 'this-month',
                })
            );

            const { result: customStartResult } = renderHook(() =>
                useLocalStorage<Dayjs | null>({
                    key: 'customStartDate',
                    initialValue: null,
                    transform: dayjsTransform,
                })
            );

            // Switch to custom range
            act(() => {
                rangeTypeResult.current[1]('custom');
                customStartResult.current[1](dayjs('2026-01-10'));
            });

            expect(rangeTypeResult.current[0]).toBe('custom');
            expect(customStartResult.current[0]?.format('YYYY-MM-DD')).toBe('2026-01-10');

            // Verify persistence
            expect(localStorage.getItem('rangeType')).toBe(JSON.stringify('custom'));
            expect(localStorage.getItem('customStartDate')).toBe(dayjs('2026-01-10').toISOString());
        });
    });
});
