import { act, renderHook } from '@testing-library/react';
import useGuessForm from 'hooks/useGuessForm';
import { validateGuess } from 'validators/validateGuess';

jest.mock('validators/validateGuess', () => ({
    validateGuess: {
        safeParse: jest.fn(),
    },
}));

let mockSafeParse: jest.SpyInstance;

function makeParseSuccess(guess: string) {
    return { success: true, data: { guess } };
}

function makeParseFailure(message: string) {
    return {
        success: false,
        error: { issues: [{ message }] },
    };
}

describe('useGuessForm', () => {
    let submitGuess: jest.Mock;

    beforeEach(() => {
        mockSafeParse = jest.spyOn(validateGuess, 'safeParse');
        submitGuess = jest.fn().mockResolvedValue(undefined);
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.clearAllMocks();
        jest.useRealTimers();
    });

    describe('Initial state', () => {
        it('Should have an empty guess', () => {
            const { result } = renderHook(() => useGuessForm(submitGuess));
            expect(result.current.guess).toBe('');
        });

        it('Should have no validation error', () => {
            const { result } = renderHook(() => useGuessForm(submitGuess));
            expect(result.current.hasValidationError).toBe(false);
        });

        it('Should have a null validation toast message', () => {
            const { result } = renderHook(() => useGuessForm(submitGuess));
            expect(result.current.validationToast.message).toBeNull();
        });
    });

    describe('handleChange', () => {
        it('Should update the guess value', () => {
            const { result } = renderHook(() => useGuessForm(submitGuess));

            act(() => result.current.handleChange('Pikachu'));
            expect(result.current.guess).toBe('Pikachu');
        });

        it('Should clear hasValidationError', () => {
            mockSafeParse.mockReturnValue(makeParseFailure('Please enter a Pokémon name.'));
            const { result } = renderHook(() => useGuessForm(submitGuess));

            act(() => {
                void result.current.handleSubmit();
            });
            expect(result.current.hasValidationError).toBe(true);

            act(() => result.current.handleChange('Pikachu'));
            expect(result.current.hasValidationError).toBe(false);
        });

        it('Should dismiss the validation toast', () => {
            mockSafeParse.mockReturnValue(makeParseFailure('Please enter a Pokémon name.'));
            const { result } = renderHook(() => useGuessForm(submitGuess));

            act(() => {
                void result.current.handleSubmit();
            });
            expect(result.current.validationToast.message).toBe('Please enter a Pokémon name.');

            act(() => result.current.handleChange('Pikachu'));
            expect(result.current.validationToast.message).toBeNull();
        });
    });

    describe('handleSubmit', () => {
        describe('On validation failure', () => {
            it('Should show the validation error message in the toast', async () => {
                mockSafeParse.mockReturnValue(makeParseFailure('Please enter a Pokémon name.'));
                const { result } = renderHook(() => useGuessForm(submitGuess));

                await act(() => result.current.handleSubmit());
                expect(result.current.validationToast.message).toBe('Please enter a Pokémon name.');
            });

            it('Should set hasValidationError to true', async () => {
                mockSafeParse.mockReturnValue(makeParseFailure('Please enter a Pokémon name.'));
                const { result } = renderHook(() => useGuessForm(submitGuess));

                await act(() => result.current.handleSubmit());
                expect(result.current.hasValidationError).toBe(true);
            });

            it('Should fall back to "Invalid input." if no issue message is present', async () => {
                mockSafeParse.mockReturnValue({
                    success: false,
                    error: { issues: [{ message: undefined }] },
                });
                const { result } = renderHook(() => useGuessForm(submitGuess));

                await act(() => result.current.handleSubmit());
                expect(result.current.validationToast.message).toBe('Invalid input.');
            });

            it('Should not call submitGuess', async () => {
                mockSafeParse.mockReturnValue(makeParseFailure('Too short.'));
                const { result } = renderHook(() => useGuessForm(submitGuess));

                await act(() => result.current.handleSubmit());
                expect(submitGuess).not.toHaveBeenCalled();
            });

            it('Should not reset the guess', async () => {
                mockSafeParse.mockReturnValue(makeParseFailure('Too short.'));
                const { result } = renderHook(() => useGuessForm(submitGuess));

                act(() => result.current.handleChange('ab'));
                await act(() => result.current.handleSubmit());
                expect(result.current.guess).toBe('ab');
            });
        });

        describe('On validation success', () => {
            it('Should call submitGuess with the current guess', async () => {
                mockSafeParse.mockReturnValue(makeParseSuccess('Pikachu'));
                const { result } = renderHook(() => useGuessForm(submitGuess));

                act(() => result.current.handleChange('Pikachu'));
                await act(() => result.current.handleSubmit());
                expect(submitGuess).toHaveBeenCalledWith('Pikachu');
            });

            it('Should reset the guess to an empty string', async () => {
                mockSafeParse.mockReturnValue(makeParseSuccess('Pikachu'));
                const { result } = renderHook(() => useGuessForm(submitGuess));

                act(() => result.current.handleChange('Pikachu'));
                await act(() => result.current.handleSubmit());
                expect(result.current.guess).toBe('');
            });

            it('Should not show a validation toast', async () => {
                mockSafeParse.mockReturnValue(makeParseSuccess('Pikachu'));
                const { result } = renderHook(() => useGuessForm(submitGuess));

                act(() => result.current.handleChange('Pikachu'));
                await act(() => result.current.handleSubmit());
                expect(result.current.validationToast.message).toBeNull();
            });

            it('Should not set hasValidationError', async () => {
                mockSafeParse.mockReturnValue(makeParseSuccess('Pikachu'));
                const { result } = renderHook(() => useGuessForm(submitGuess));

                act(() => result.current.handleChange('Pikachu'));
                await act(() => result.current.handleSubmit());
                expect(result.current.hasValidationError).toBe(false);
            });

            it('Should wait for submitGuess to resolve before resetting', async () => {
                let resolve!: () => void;
                submitGuess.mockReturnValue(
                    new Promise<void>((r) => {
                        resolve = r;
                    })
                );
                mockSafeParse.mockReturnValue(makeParseSuccess('Pikachu'));
                const { result } = renderHook(() => useGuessForm(submitGuess));

                act(() => result.current.handleChange('Pikachu'));

                const submitPromise = act(() => result.current.handleSubmit());
                expect(result.current.guess).toBe('Pikachu');

                resolve();
                await submitPromise;
                expect(result.current.guess).toBe('');
            });
        });
    });
});
