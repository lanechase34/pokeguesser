import type { GameOverResponse } from 'types/Guess.type';

interface AnswerCardProps {
    /** The completed game result containing the correct Pokémon and whether the user guessed correctly */
    result: GameOverResponse;
    /**
     * Pre-formatted countdown string in HH:MM:SS format until the next question is available.
     * Provided by the `useCountdown` hook.
     */
    countdown: string;
}

/**
 * Displays the end-of-game summary card and a countdown to the next question.
 *
 * @param result - The completed game result from the API
 * @param countdown - HH:MM:SS string counting down to when the next question unlocks
 */
export default function AnswerCard({ result, countdown }: AnswerCardProps) {
    return (
        <>
            <div className={`answer-card ${result.correct ? 'correct' : 'incorrect'}`}>
                <div className="answer-card-header">{result.correct ? 'Correct!' : 'Good try!'}</div>
                <div className="answer-card-body">
                    <div>
                        <p className="answer-name">{result.answer.name}</p>
                        <p className="answer-meta">
                            #{result.answer.number} {result.answer.type1}
                            {result.answer.type2 ? ` / ${result.answer.type2}` : ''}
                        </p>
                        <p className="answer-attempt">
                            {result.correct
                                ? `Guessed in ${result.attempt} ${result.attempt === 1 ? 'try' : 'tries'}`
                                : 'Incorrect guess'}
                        </p>
                    </div>
                </div>
            </div>
            <div className="next-question-banner">
                <span className="next-question-label">Next question available in</span>
                <span className="next-question-timer">{countdown}</span>
            </div>
        </>
    );
}
