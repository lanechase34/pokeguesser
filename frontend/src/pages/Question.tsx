import { useEffect, useMemo, useState } from 'react';
import { questionService } from 'schema/question';
import { z } from 'zod';

const guessForm = z.object({
    guess: z
        .string()
        .min(3, 'Please enter a Pokémon name.')
        .max(50, 'That name is too long.')
        .regex(/^[a-zA-Z0-9\s\-.]+$/, 'Only letters, numbers, hyphens, and spaces are allowed.'),
});

export default function Question() {
    const [loading, setLoading] = useState<boolean>(true);
    const [guess, setGuess] = useState<string>('');
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [validationError, setValidationError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState<boolean>(false);
    const [imgId, setImgId] = useState<string>('');

    const questionAPI = useMemo(() => questionService(), []);

    const todayDate = new Date().toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    });

    // Load today's question on mount
    useEffect(() => {
        let cancelled = false;

        async function loadQuestion() {
            try {
                setLoading(true);
                const question = await questionAPI.fetchTodaysQuestion();
                if (!cancelled) {
                    setImgId(`${question.id}`);
                    setLoading(false);
                }
            } catch (err: unknown) {
                console.error('Error retrieving todays question', err);
            }
        }

        void loadQuestion();

        return () => {
            cancelled = true;
        };
    }, [questionAPI]);

    async function submitGuess() {
        setValidationError(null);
        setSubmitError(null);

        // Validate the user's guess
        const result = guessForm.safeParse({ guess });
        if (!result.success) {
            const firstError = result.error.issues[0].message ?? 'Invalid Input.';
            setValidationError(firstError);
            return;
        }

        setSubmitting(true);
        try {
            const response = await questionAPI.submitGuess(guess);
        } catch (err: unknown) {
            console.error('Error submitting guess', err);
            setSubmitError('Something went wrong submitting your guess. Please try again.');
            setSubmitting(false);
        }
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
                    <p className="date">{todayDate}</p>
                </div>

                <div className="silhouette-container">
                    <div className="silhouette-glow">
                        <img
                            src={`/pokeguesser/silhouettes/${imgId}.webp`}
                            alt="Silhouette to guess"
                            className="silhouette"
                        />
                    </div>
                </div>

                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        void submitGuess();
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
            </div>

            {/* Toasts */}
            <div className="toast-container">
                {validationError && (
                    <div className="toast toast-warning">
                        <div className="toast-message">
                            <span className="toast-title">Invalid Guess</span>
                            <span className="toast-body">{validationError}</span>
                        </div>
                        <button className="toast-dismiss" onClick={() => setValidationError(null)}>
                            X
                        </button>
                    </div>
                )}
                {submitError && (
                    <div className="toast toast-error">
                        <div className="toast-message">
                            <span className="toast-title">Submission Failed</span>
                            <span className="toast-body">{submitError}</span>
                        </div>
                        <button className="toast-dismiss" onClick={() => setSubmitError(null)}>
                            X
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
