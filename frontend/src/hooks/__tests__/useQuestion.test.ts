import { act, renderHook, waitFor } from '@testing-library/react';

import useQuestion from '../useQuestion';

// Mocks

const mockFetchTodaysQuestion = jest.fn();
const mockSubmitGuess = jest.fn();

jest.mock('services/question', () => ({
    questionService: () => ({
        fetchTodaysQuestion: mockFetchTodaysQuestion,
        submitGuess: mockSubmitGuess,
    }),
}));

jest.mock('utils/formatHint', () => ({
    formatHint: (hint: unknown) => `formatted:${JSON.stringify(hint)}`,
}));

// Capture stored values across setStoredResult calls
let mockStoredValue: unknown = null;
const mockSetStoredResult = jest.fn((val) => {
    mockStoredValue = val;
});

jest.mock('hooks/useLocalStorage', () => ({
    __esModule: true,
    default: jest.fn(() => [mockStoredValue, mockSetStoredResult]),
}));

// Helpers

const TODAY = new Date().toISOString().split('T')[0];

const mockGameOverCorrect = {
    correct: true,
    answer: { id: 1, name: 'Bulbasaur', number: 1, sprite: '1', type1: 'Grass', type2: 'Poison' },
    attempt: 2,
};

const mockGameOverIncorrect = {
    correct: false,
    answer: { id: 1, name: 'Bulbasaur', number: 1, sprite: '1', type1: 'Grass', type2: 'Poison' },
    attempt: 3,
};

const mockIncorrectResponse = {
    correct: false,
    attempt: 1,
    attempts_remaining: 2,
    hint: { Type1: 'Grass', Type2: 'Poison' },
};

function renderQuestion() {
    return renderHook(() => useQuestion());
}

describe('useQuestion', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockStoredValue = null;
        mockFetchTodaysQuestion.mockResolvedValue({ id: 42 });
    });

    describe('Initial load', () => {
        it('Starts in loading state', () => {
            const { result } = renderQuestion();
            expect(result.current.loading).toBe(true);
        });

        it('Sets loading false and imgId after question fetch resolves', async () => {
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));
            expect(result.current.imgId).toBe('42');
        });

        it('Initializes with empty hints', async () => {
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));
            expect(result.current.hints).toEqual([]);
        });

        it('Initializes with no submit error', async () => {
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));
            expect(result.current.submitError).toBeNull();
        });

        it('Initializes submitting as false', async () => {
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));
            expect(result.current.submitting).toBe(false);
        });

        it('Does not crash when fetch fails', async () => {
            mockFetchTodaysQuestion.mockRejectedValue(new Error('Network error'));
            const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {
                // silence
            });
            const { result } = renderQuestion();
            // Loading never resolves to false on error - remains true
            await waitFor(() => expect(consoleSpy).toHaveBeenCalledWith('Failed to load question'));
            expect(result.current.loading).toBe(true);
            consoleSpy.mockRestore();
        });

        it('Does not set state after unmount', async () => {
            mockFetchTodaysQuestion.mockImplementation(
                () => new Promise((resolve) => setTimeout(() => resolve({ id: 42 }), 100))
            );
            const { unmount } = renderQuestion();
            unmount();
            // Advance past the fetch resolution - should not throw
            await act(async () => {
                jest.advanceTimersByTime(100);
                await Promise.resolve();
            });
        });
    });

    describe('localStorage restoration', () => {
        it('Returns todayResult when stored result matches today', async () => {
            mockStoredValue = { date: TODAY, result: mockGameOverCorrect };
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));
            expect(result.current.todayResult).toEqual(mockGameOverCorrect);
        });

        it('Returns null todayResult when stored result is from a previous day', async () => {
            mockStoredValue = { date: '2000-01-01', result: mockGameOverCorrect };
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));
            expect(result.current.todayResult).toBeNull();
        });

        it('Returns null todayResult when nothing is stored', async () => {
            mockStoredValue = null;
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));
            expect(result.current.todayResult).toBeNull();
        });

        it('Clears stale stored result from a previous day', async () => {
            mockStoredValue = { date: '2000-01-01', result: mockGameOverCorrect };
            renderQuestion();
            await waitFor(() => expect(mockSetStoredResult).toHaveBeenCalledWith(null));
        });

        it('Does not clear storage when result is from today', async () => {
            mockStoredValue = { date: TODAY, result: mockGameOverCorrect };
            renderQuestion();
            await waitFor(() => expect(mockFetchTodaysQuestion).toHaveBeenCalled());
            expect(mockSetStoredResult).not.toHaveBeenCalledWith(null);
        });

        it('Does not clear storage when nothing is stored', async () => {
            mockStoredValue = null;
            renderQuestion();
            await waitFor(() => expect(mockFetchTodaysQuestion).toHaveBeenCalled());
            expect(mockSetStoredResult).not.toHaveBeenCalled();
        });
    });

    describe('submitGuess - game over', () => {
        it('Stores result in localStorage on correct answer', async () => {
            mockSubmitGuess.mockResolvedValue(mockGameOverCorrect);
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('bulbasaur');
            });

            expect(mockSetStoredResult).toHaveBeenCalledWith({
                date: TODAY,
                result: mockGameOverCorrect,
            });
        });

        it('Stores result in localStorage when out of attempts', async () => {
            mockSubmitGuess.mockResolvedValue(mockGameOverIncorrect);
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('wrongmon');
            });

            expect(mockSetStoredResult).toHaveBeenCalledWith({
                date: TODAY,
                result: mockGameOverIncorrect,
            });
        });

        it('Updates imgId to the answer pokemon id on game over', async () => {
            mockSubmitGuess.mockResolvedValue(mockGameOverCorrect);
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('bulbasaur');
            });

            expect(result.current.imgId).toBe('1');
        });

        it('Clears hints on game over', async () => {
            // First build up a hint
            mockSubmitGuess.mockResolvedValueOnce(mockIncorrectResponse).mockResolvedValueOnce(mockGameOverCorrect);

            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('wrongmon');
            });
            expect(result.current.hints).toHaveLength(1);

            await act(async () => {
                await result.current.submitGuess('bulbasaur');
            });
            expect(result.current.hints).toEqual([]);
        });

        it('Sets submitting false after game over', async () => {
            mockSubmitGuess.mockResolvedValue(mockGameOverCorrect);
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('bulbasaur');
            });

            expect(result.current.submitting).toBe(false);
        });
    });

    describe('submitGuess - incorrect guess', () => {
        it('Appends a formatted hint on incorrect guess', async () => {
            mockSubmitGuess.mockResolvedValue(mockIncorrectResponse);
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('wrongmon');
            });

            expect(result.current.hints).toHaveLength(1);
            expect(result.current.hints[0]).toBe(`formatted:${JSON.stringify(mockIncorrectResponse.hint)}`);
        });

        it('Accumulates hints across multiple incorrect guesses', async () => {
            const hint2 = { ...mockIncorrectResponse, attempt: 2, hint: { Generation: 1 } };
            mockSubmitGuess.mockResolvedValueOnce(mockIncorrectResponse).mockResolvedValueOnce(hint2);

            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('wrongmon');
            });
            await act(async () => {
                await result.current.submitGuess('wrongmon2');
            });

            expect(result.current.hints).toHaveLength(2);
        });

        it('Does not update imgId or localStorage on incorrect guess', async () => {
            mockSubmitGuess.mockResolvedValue(mockIncorrectResponse);
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));
            const imgIdBefore = result.current.imgId;

            await act(async () => {
                await result.current.submitGuess('wrongmon');
            });

            expect(result.current.imgId).toBe(imgIdBefore);
            expect(mockSetStoredResult).not.toHaveBeenCalled();
        });

        it('Sets submitting false after incorrect guess', async () => {
            mockSubmitGuess.mockResolvedValue(mockIncorrectResponse);
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('wrongmon');
            });

            expect(result.current.submitting).toBe(false);
        });
    });

    describe('submitGuess - error handling', () => {
        it('Sets submitError when API throws', async () => {
            mockSubmitGuess.mockRejectedValue(new Error('Server error'));
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('bulbasaur');
            });

            expect(result.current.submitError).toBe('Something went wrong. Please try again.');
        });

        it('Clears submitError at the start of a new submission', async () => {
            mockSubmitGuess.mockRejectedValueOnce(new Error('fail')).mockResolvedValueOnce(mockIncorrectResponse);

            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('bulbasaur');
            });
            expect(result.current.submitError).not.toBeNull();

            await act(async () => {
                await result.current.submitGuess('bulbasaur');
            });
            expect(result.current.submitError).toBeNull();
        });

        it('Sets submitting false even when API throws', async () => {
            mockSubmitGuess.mockRejectedValue(new Error('Server error'));
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('bulbasaur');
            });

            expect(result.current.submitting).toBe(false);
        });
    });

    describe('setSubmitError', () => {
        it('Clears submitError when called with null', async () => {
            mockSubmitGuess.mockRejectedValue(new Error('fail'));
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await result.current.submitGuess('bulbasaur');
            });
            expect(result.current.submitError).not.toBeNull();

            act(() => {
                result.current.setSubmitError(null);
            });
            expect(result.current.submitError).toBeNull();
        });

        it('Can set a custom error message', async () => {
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            act(() => {
                result.current.setSubmitError('Custom error');
            });
            expect(result.current.submitError).toBe('Custom error');
        });
    });
});
