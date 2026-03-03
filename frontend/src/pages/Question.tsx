import AnswerCard from 'components/AnswerCard';
import HintsList from 'components/HintsList';
import Toast from 'components/Toast';
import useCountdown from 'hooks/useCountdown';
import useQuestion from 'hooks/useQuestion';
import { useEffect, useMemo, useState } from 'react';
import { z } from 'zod';

const guessSchema = z.object({
    guess: z
        .string()
        .min(3, 'Please enter a Pokémon name.')
        .max(50, 'That name is too long.')
        .regex(/^[a-zA-Z0-9\s\-.]+$/, 'Only letters, numbers, hyphens, and spaces are allowed.'),
});

export default function Question() {
    const { loading, imgId, hints, submitting, submitError, todayResult, submitGuess, setSubmitError } = useQuestion();

    const [guess, setGuess] = useState<string>('');
    const [validationError, setValidationError] = useState<string | null>(null);

    // Countdown til next question
    const midnight = useMemo(() => {
        const d = new Date();
        d.setHours(24, 0, 0, 0);
        return d;
    }, []);

    const countdown = useCountdown(midnight);

    const todaysDate = new Date().toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    });

    async function handleSubmitGuess() {
        const result = guessSchema.safeParse({ guess });
        if (!result.success) {
            const error = result.error.issues[0].message ?? 'Invalid input.';
            setValidationError(error);
            return;
        }

        await submitGuess(guess);
        setGuess('');
    }

    // Auto-dismiss toasts
    useEffect(() => {
        if (!validationError) return;
        const timer = setTimeout(() => setValidationError(null), 4000);
        return () => clearTimeout(timer);
    }, [validationError]);

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-screen">
                <div className="pokeball-loader"></div>
            </div>
        );
    }

    return (
        <div className="game-container">
            <div className="game-card">
                <div className="header">
                    <h1 className="title">Who's That Pokémon?</h1>
                    <p className="date">{todaysDate}</p>
                </div>

                <div className="silhouette-container">
                    <div className="silhouette-glow">
                        <img
                            src={
                                todayResult
                                    ? `/pokeguesser/images/${todayResult.answer.number}.webp`
                                    : `/pokeguesser/silhouettes/${imgId}.webp`
                            }
                            alt={todayResult ? "Today's answer" : 'Silhouette to guess'}
                            className={todayResult ? 'answer' : 'silhouette'}
                        />
                    </div>
                </div>

                <HintsList hints={hints} />

                {todayResult?.answer.id ? (
                    <AnswerCard result={todayResult} countdown={countdown} />
                ) : (
                    <form
                        onSubmit={(e) => {
                            e.preventDefault();
                            void handleSubmitGuess();
                        }}
                        className="guess-form"
                    >
                        <input
                            type="text"
                            value={guess}
                            onChange={(e) => {
                                setGuess(e.target.value);
                                setValidationError(null);
                            }}
                            placeholder="Enter Pokémon name..."
                            className={`guess-input ${validationError ? 'guess-input-error' : ''}`}
                            disabled={submitting}
                        />
                        <button type="submit" disabled={submitting || !guess.trim()} className="submit-button">
                            {submitting ? 'Checking...' : 'Guess!'}
                        </button>
                    </form>
                )}
            </div>

            {/* Toasts */}
            <div className="toast-container">
                {validationError && (
                    <Toast
                        type="warning"
                        title="Invalid Guess"
                        body={validationError}
                        onDismiss={() => setValidationError(null)}
                    />
                )}
                {submitError && (
                    <Toast
                        type="error"
                        title="Submission Failed"
                        body={submitError}
                        onDismiss={() => setSubmitError(null)}
                    />
                )}
            </div>
        </div>
    );
}
