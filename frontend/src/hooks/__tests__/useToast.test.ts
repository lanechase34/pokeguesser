import { act, renderHook } from '@testing-library/react';

import useToast from '../useToast';

describe('useToast', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    describe('Initial state', () => {
        it('Should have a null message by default', () => {
            const { result } = renderHook(() => useToast());
            expect(result.current.message).toBeNull();
        });

        it('Should use default autoDismissMs of 4000 when no options are provided', () => {
            const { result } = renderHook(() => useToast());

            act(() => result.current.show('Hello'));
            expect(result.current.message).toBe('Hello');

            act(() => jest.advanceTimersByTime(3999));
            expect(result.current.message).toBe('Hello');

            act(() => jest.advanceTimersByTime(1));
            expect(result.current.message).toBeNull();
        });
    });

    describe('Show', () => {
        it('Should set the message', () => {
            const { result } = renderHook(() => useToast());

            act(() => result.current.show('Something went wrong'));
            expect(result.current.message).toBe('Something went wrong');
        });

        it('Should replace an existing message', () => {
            const { result } = renderHook(() => useToast());

            act(() => result.current.show('First'));
            act(() => result.current.show('Second'));
            expect(result.current.message).toBe('Second');
        });
    });

    describe('Dismiss', () => {
        it('Should clear the message', () => {
            const { result } = renderHook(() => useToast());

            act(() => result.current.show('Hello'));
            act(() => result.current.dismiss());
            expect(result.current.message).toBeNull();
        });

        it('Should be a no-op when message is already null', () => {
            const { result } = renderHook(() => useToast());

            act(() => result.current.dismiss());
            expect(result.current.message).toBeNull();
        });
    });

    describe('Auto-dismiss', () => {
        it('Should auto-dismiss after the default 4000ms', () => {
            const { result } = renderHook(() => useToast());

            act(() => result.current.show('Auto dismiss me'));
            act(() => jest.advanceTimersByTime(4000));
            expect(result.current.message).toBeNull();
        });

        it('Should auto-dismiss after a custom autoDismissMs', () => {
            const { result } = renderHook(() => useToast({ autoDismissMs: 2000 }));

            act(() => result.current.show('Quick toast'));
            act(() => jest.advanceTimersByTime(2000));
            expect(result.current.message).toBeNull();
        });

        it('Should not auto-dismiss before the timeout elapses', () => {
            const { result } = renderHook(() => useToast({ autoDismissMs: 2000 }));

            act(() => result.current.show('Still here'));
            act(() => jest.advanceTimersByTime(1999));
            expect(result.current.message).toBe('Still here');
        });

        it('Should reset the timer when a new message is shown', () => {
            const { result } = renderHook(() => useToast({ autoDismissMs: 2000 }));

            act(() => result.current.show('First'));
            act(() => jest.advanceTimersByTime(1000));
            act(() => result.current.show('Second'));

            // 1000ms after 'Second' was shown - should still be visible
            act(() => jest.advanceTimersByTime(1000));
            expect(result.current.message).toBe('Second');

            // Full 2000ms after 'Second' was shown - should be dismissed
            act(() => jest.advanceTimersByTime(1000));
            expect(result.current.message).toBeNull();
        });

        it('Should not start a timer when message is null', () => {
            const { result } = renderHook(() => useToast());

            // Advance time without ever showing a message
            act(() => jest.advanceTimersByTime(4000));
            expect(result.current.message).toBeNull();
        });

        it('Should clear the timer on unmount', () => {
            const { result, unmount } = renderHook(() => useToast());

            act(() => result.current.show('Will unmount'));
            unmount();

            // Should not throw after unmount
            act(() => jest.advanceTimersByTime(4000));
        });
    });
});
