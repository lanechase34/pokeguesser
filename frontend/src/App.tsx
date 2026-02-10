import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './App.css';
import QuestionPage from 'pages/Question';
import NotFound from 'pages/NotFound';

const STALE_TIME = 15 * 60 * 1000; // 15 minutes
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: STALE_TIME,
            refetchOnWindowFocus: false, // Disable refetch on tab switch
            retry: 1, // Retry failed requests once
        },
    },
});

function AppRouter() {
    return (
        <Routes>
            <Route path="/" element={<QuestionPage />} />

            <Route path="*" element={<NotFound />} />
        </Routes>
    );
}

export default function App() {
    const basename = '/pokeguesser';
    return (
        <QueryClientProvider client={queryClient}>
            <Router basename={basename}>
                <AppRouter />
            </Router>
        </QueryClientProvider>
    );
}
