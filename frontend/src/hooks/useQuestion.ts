import { useMutation, useQuery } from '@tanstack/react-query';
import useLocalStorage from 'hooks/useLocalStorage';
import { useEffect, useMemo, useState } from 'react';
import { questionService } from 'services/question';
import type { GameOverResponse, GuessResponse } from 'types/Guess.type';
import { formatHint } from 'utils/formatHint';

interface StoredResult {
    date: string; // "YYYY-MM-DD"
    result: GameOverResponse;
}

interface UseQuestionReturn {
    /** True while the initial question fetch is in progress */
    loading: boolean;
    /**
     * The pokemon's internal ID used to construct the silhouette/answer image URL.
     * Starts as the daily question's ID, stays the same after game over since
     * the answer image uses `number` not `id`.
     */
    imgId: string;
    /** Accumulated formatted hint strings from incorrect guesses, in order */
    hints: string[];
    /** True while a guess submission is in flight */
    submitting: boolean;
    /** Non-null when a guess submission fails unexpectedly */
    submitError: string | null;
    /**
     * Today's game over result if the user has already completed today's puzzle,
     * either from this session or restored from localStorage. Null if the game
     * is still in progress.
     */
    todayResult: GameOverResponse | null;
    /** Submits a validated guess string to the API and updates game state */
    submitGuess: (guess: string) => Promise<GuessResponse>;
    /** Clears the current submit error, e.g. on toast dismiss */
    setSubmitError: (error: string | null) => void;
}

/**
 * Manages all state and side effects for the daily Pokémon guessing game.
 *
 * On mount, fetches today's question and restores any previously completed
 * result from localStorage. Incorrect guesses accumulate formatted hints.
 * A correct guess or running out of attempts triggers game over, persisting
 * the result to localStorage so the user cannot re-attempt on refresh.
 *
 * @returns Game state and actions
 */
export default function useQuestion(): UseQuestionReturn {
    const today = new Date().toISOString().split('T')[0];

    /**
     * Memoized to prevent re-instantiating the service object on every render,
     * since it's used as a useEffect dependency below.
     */
    const questionAPI = useMemo(() => questionService(), []);
    const [hints, setHints] = useState<string[]>([]);
    const [submitError, setSubmitError] = useState<string | null>(null);

    const [storedResult, setStoredResult] = useLocalStorage<StoredResult | null>({
        key: 'pokeguesser_result',
        initialValue: null,
    });

    // Store the correct answer in localstorage
    const todayResult = useMemo<GameOverResponse | null>(() => {
        return storedResult?.date === today ? storedResult.result : null;
    }, [storedResult, today]);

    // Clear stale storage
    useEffect(() => {
        if (storedResult && !todayResult) setStoredResult(null);
    }, [storedResult, todayResult, setStoredResult]);

    const { isLoading, data: question } = useQuery({
        queryKey: ['question', today],
        queryFn: () => questionAPI.fetchTodaysQuestion(),
        staleTime: Infinity,
        enabled: !todayResult,
    });

    /**
     * Submits the user's guess and handles all three possible outcomes:
     * - **Game over** (`answer` in response): persists result to localStorage and reveals the answer image
     * - **Incorrect guess**: appends a formatted hint string to the hints list
     * - **Unexpected error**: sets a user-facing error message
     *
     * @param guess - A pre-validated guess string
     */
    const { mutateAsync, isPending } = useMutation({
        mutationFn: (guess: string) => questionAPI.submitGuess(guess),
        onSuccess: (response) => {
            setSubmitError(null);
            if ('answer' in response) {
                setStoredResult({ date: today, result: response });
                setHints([]);
            } else {
                setHints((prev) => [...prev, formatHint(response.hint)]);
            }
        },
        onError: (error: Error) => {
            setSubmitError(error.message);
        },
    });

    // Derive the imgId based on whether we are guessing or the answer is displayed
    const imgId = todayResult ? String(todayResult.answer.id) : String(question?.id ?? '');

    return {
        loading: isLoading,
        imgId,
        hints,
        submitting: isPending,
        submitError,
        setSubmitError,
        todayResult,
        submitGuess: mutateAsync,
    };
}
