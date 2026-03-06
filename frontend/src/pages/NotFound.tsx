export default function NotFound() {
    return (
        <div className="game-container">
            <div className="game-card nf-card">
                <div className="nf-404">404</div>
                <h1 className="title nf-title">Who's That Page?</h1>
                <p className="nf-subtitle">
                    This page fled into the tall grass.
                    <br />
                    It's not coming back.
                </p>
                <button className="submit-button nf-btn" onClick={() => (window.location.href = '/')}>
                    Return
                </button>
            </div>
        </div>
    );
}
