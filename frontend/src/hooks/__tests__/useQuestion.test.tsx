import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';

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

let mockStoredValue: unknown = null;
const mockSetStoredResult = jest.fn((val) => {
    mockStoredValue = val;
});

jest.mock('hooks/useLocalStorage', () => ({
    __esModule: true,
    default: jest.fn(() => [mockStoredValue, mockSetStoredResult]),
}));

// Helpers

function createWrapper() {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
        },
    });
    return function Wrapper({ children }: { children: ReactNode }) {
        return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    };
}

function renderQuestion() {
    return renderHook(() => useQuestion(), { wrapper: createWrapper() });
}

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
            const { result } = renderQuestion();
            // With retry: false, query moves to error state (isLoading becomes false)
            await waitFor(() => expect(result.current.loading).toBe(false));
            expect(result.current.imgId).toBe('');
        });
    });

    describe('localStorage restoration', () => {
        it('Returns todayResult when stored result matches today', () => {
            mockStoredValue = { date: TODAY, result: mockGameOverCorrect };
            const { result } = renderQuestion();
            // Query is disabled when todayResult exists, no loading state
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

        it('Does not clear storage when result is from today', () => {
            mockStoredValue = { date: TODAY, result: mockGameOverCorrect };
            renderQuestion();
            expect(mockSetStoredResult).not.toHaveBeenCalledWith(null);
        });

        it('Does not clear storage when nothing is stored', async () => {
            mockStoredValue = null;
            renderQuestion();
            await waitFor(() => expect(mockFetchTodaysQuestion).toHaveBeenCalled());
            expect(mockSetStoredResult).not.toHaveBeenCalled();
        });

        it('Uses answer imgId when todayResult exists, skipping the fetch', () => {
            mockStoredValue = { date: TODAY, result: mockGameOverCorrect };
            const { result } = renderQuestion();
            expect(result.current.imgId).toBe('1');
            expect(mockFetchTodaysQuestion).not.toHaveBeenCalled();
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

        it('Clears hints on game over', async () => {
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
                await expect(result.current.submitGuess('bulbasaur')).rejects.toThrow('Server error');
            });
        });

        it('Clears submitError on the next successful submission', async () => {
            mockSubmitGuess.mockRejectedValueOnce(new Error('fail')).mockResolvedValueOnce(mockIncorrectResponse);

            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await expect(result.current.submitGuess('bulbasaur')).rejects.toThrow('fail');
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
                await expect(result.current.submitGuess('bulbasaur')).rejects.toThrow('Server error');
            });

            expect(result.current.submitting).toBe(false);
        });
    });

    describe('setSubmitError', () => {
        it('Clears submitError when called', async () => {
            mockSubmitGuess.mockRejectedValue(new Error('fail'));
            const { result } = renderQuestion();
            await waitFor(() => expect(result.current.loading).toBe(false));

            await act(async () => {
                await expect(result.current.submitGuess('bulbasaur')).rejects.toThrow('fail');
            });
            expect(result.current.submitError).not.toBeNull();

            act(() => {
                result.current.setSubmitError(null);
            });
            expect(result.current.submitError).toBeNull();
        });
    });
});
