import { useState, useEffect, useMemo } from 'react';
import { questionService } from 'schema/question';

export default function Question() {
    const [loading, setLoading] = useState<boolean>(true);
    const [guess, setGuess] = useState<string>('');
    const [submitting, setSubmitting] = useState<boolean>(false);
    const [imgId, setImgId] = useState<string>('');

    const questionAPI = useMemo(() => questionService(), []);

    const todayDate = new Date().toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    });

    async function loadQuestion() {
        try {
            setLoading(true);
            const question = await questionAPI.fetchTodaysQuestion();
            setImgId(`${question.id}`);
            setLoading(false);
        } catch (err: unknown) {}
    }

    useEffect(() => {
        loadQuestion();
    }, []);

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
                    }}
                    className="guess-form"
                >
                    <input
                        type="text"
                        value={guess}
                        onChange={(e) => setGuess(e.target.value)}
                        placeholder="Enter Pokémon name..."
                        className="guess-input"
                        disabled={submitting}
                        autoFocus
                    />
                    <button type="submit" disabled={submitting || !guess.trim()} className="submit-button">
                        {submitting ? 'Checking...' : 'Guess!'}
                    </button>
                </form>
            </div>
        </div>
    );
}
