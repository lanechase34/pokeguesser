import AnswerCard from 'components/AnswerCard';
import HintsList from 'components/HintsList';
import Toast from 'components/Toast';
import useCountdown from 'hooks/useCountdown';
import useGuessForm from 'hooks/useGuessForm';
import useQuestion from 'hooks/useQuestion';
import useToast from 'hooks/useToast';
import { useEffect, useMemo } from 'react';

const GameLayout = ({ todaysDate, children }: { todaysDate: string; children: React.ReactNode }) => (
    <div className="game-container">
        <div className="game-card">
            <div className="header">
                <h1 className="title">Who's That Pokémon?</h1>
                <p className="date">{todaysDate}</p>
            </div>
            {children}
        </div>
    </div>
);

export default function Question() {
    const { loading, imgId, hints, submitting, submitError, todayResult, submitGuess, setSubmitError } = useQuestion();

    // Submissions Errors
    const { message: submitErrorMessage, show: showSubmitError, dismiss: dismissSubmitError } = useToast();
    // Update the submitErrorToast as the submit error changes
    useEffect(() => {
        if (!submitError) return;
        showSubmitError(submitError);
        setSubmitError(null);
    }, [submitError, showSubmitError, setSubmitError]);

    // Guess Form
    const { guess, hasValidationError, validationToast, handleSubmit, handleChange } = useGuessForm(submitGuess);

    // Countdown til next question and todaysDate
    const { midnight, todaysDate } = useMemo(() => {
        const d = new Date();
        d.setHours(24, 0, 0, 0);
        return {
            midnight: d,
            todaysDate: new Date().toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
            }),
        };
    }, []);

    const countdown = useCountdown(midnight);

    const questionError = !loading && !todayResult && !imgId;

    if (loading) {
        return (
            <GameLayout todaysDate={todaysDate}>
                <div className="flex justify-content-center items-center align-items-center">
                    <div className="pokeball-loader"></div>
                </div>
            </GameLayout>
        );
    }

    if (questionError) {
        return (
            <GameLayout todaysDate={todaysDate}>
                <p className="error-message">Unable to load today's question. Please try again later.</p>
            </GameLayout>
        );
    }

    return (
        <GameLayout todaysDate={todaysDate}>
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
                        void handleSubmit();
                    }}
                    className="guess-form"
                >
                    <input
                        type="text"
                        value={guess}
                        onChange={(e) => handleChange(e.target.value)}
                        placeholder="Enter Pokémon name..."
                        className={`guess-input ${hasValidationError ? 'guess-input-error' : ''}`}
                        disabled={submitting}
                    />
                    <button type="submit" disabled={submitting || !guess.trim()} className="submit-button">
                        {submitting ? 'Checking...' : 'Guess!'}
                    </button>
                </form>
            )}

            {/* Toasts */}
            <div className="toast-container">
                {validationToast.message && (
                    <Toast
                        type="warning"
                        title="Invalid Guess"
                        body={validationToast.message}
                        onDismiss={validationToast.dismiss}
                    />
                )}
                {submitErrorMessage && (
                    <Toast
                        type="error"
                        title="Submission Failed"
                        body={submitErrorMessage}
                        onDismiss={dismissSubmitError}
                    />
                )}
            </div>
        </GameLayout>
    );
}
