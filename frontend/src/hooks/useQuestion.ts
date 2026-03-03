import useLocalStorage from 'hooks/useLocalStorage';
import { useEffect, useMemo, useState } from 'react';
import { questionService } from 'schema/question';
import type { GameOverResponse } from 'types/Guess.type';
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
    submitGuess: (guess: string) => Promise<void>;
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
 * @returns {UseQuestionReturn} Game state and actions
 */
export default function useQuestion(): UseQuestionReturn {
    const [loading, setLoading] = useState(true);
    const [imgId, setImgId] = useState('');
    const [hints, setHints] = useState<string[]>([]);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);

    /**
     * Memoized to prevent re-instantiating the service object on every render,
     * since it's used as a useEffect dependency below.
     */
    const questionAPI = useMemo(() => questionService(), []);

    const [storedResult, setStoredResult] = useLocalStorage<StoredResult | null>({
        key: 'pokeguesser_result',
        initialValue: null,
    });

    // Store the correct answer in localstorage
    const todayResult = useMemo<GameOverResponse | null>(() => {
        const today = new Date().toISOString().split('T')[0];
        return storedResult?.date === today ? storedResult.result : null;
    }, [storedResult]);

    // Clear stale storage
    useEffect(() => {
        if (storedResult && !todayResult) setStoredResult(null);
    }, [storedResult, todayResult, setStoredResult]);

    // Load question on mount
    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                const question = await questionAPI.fetchTodaysQuestion();
                if (!cancelled) {
                    setImgId(String(question.id));
                    setLoading(false);
                }
            } catch {
                console.error('Failed to load question');
            }
        }
        void load();
        return () => {
            cancelled = true;
        };
    }, [questionAPI]);

    /**
     * Submits the user's guess and handles all three possible outcomes:
     * - **Game over** (`answer` in response): persists result to localStorage and reveals the answer image
     * - **Incorrect guess**: appends a formatted hint string to the hints list
     * - **Unexpected error**: sets a user-facing error message
     *
     * @param guess - A pre-validated guess string
     */
    async function submitGuess(guess: string) {
        setSubmitError(null);
        setSubmitting(true);
        try {
            const response = await questionAPI.submitGuess(guess);
            if ('answer' in response) {
                const today = new Date().toISOString().split('T')[0];
                setStoredResult({ date: today, result: response });
                setImgId(String(response.answer.id));
                setHints([]);
            } else {
                setHints((prev) => [...prev, formatHint(response.hint)]);
            }
        } catch {
            setSubmitError('Something went wrong. Please try again.');
        } finally {
            setSubmitting(false);
        }
    }

    return { loading, imgId, hints, submitting, submitError, todayResult, submitGuess, setSubmitError };
}
