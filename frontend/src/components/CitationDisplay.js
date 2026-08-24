import React, { useState, useEffect } from 'react';
import api from '../api';

const CitationDisplay = () => {
    const [papers, setPapers] = useState([]);
    const [selectedPaperId, setSelectedPaperId] = useState('');
    const [citations, setCitations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Fetch available papers when component mounts
        const fetchPapers = async () => {
            try {
                const response = await api.get('/api/papers');
                setPapers(response.data.papers || []);
            } catch (err) {
                console.error('Error fetching papers:', err);
            }
        };

        fetchPapers();
    }, []);

    const fetchCitations = async () => {
        if (!selectedPaperId) {
            setError('Please select a paper first');
            return;
        }

        setLoading(true);
        setError(null);
        setCitations([]);

        try {
            const response = await api.get(`/api/citations/${selectedPaperId}`);
            setCitations(response.data.citations || []);
        } catch (err) {
            console.error('Citation fetch error:', err);
            setError(err.response?.data?.detail || 'Failed to fetch citations');
        } finally {
            setLoading(false);
        }
    };

    const handlePaperChange = (e) => {
        setSelectedPaperId(e.target.value);
        setError(null);
        setCitations([]);
    };

    return (
        <div>
            <div className="paper-selector">
                <label htmlFor="citation-paper-select">Select a paper:</label>
                <select 
                    id="citation-paper-select"
                    value={selectedPaperId} 
                    onChange={handlePaperChange}
                    disabled={loading || papers.length === 0}
                >
                    <option value="">-- Select a paper --</option>
                    {papers.map((paper) => (
                        <option key={paper.id} value={paper.id}>
                            {paper.title || `Paper ${paper.id}`}
                        </option>
                    ))}
                </select>
                {papers.length === 0 && <p className="no-papers">No papers available. Please upload papers first.</p>}
            </div>

            <div className="citation-controls">
                <button 
                    onClick={fetchCitations} 
                    disabled={loading || !selectedPaperId}
                    className="fetch-button"
                >
                    {loading ? 'Loading...' : 'Fetch Citations'}
                </button>
            </div>

            {error && <div className="error">{error}</div>}
            {loading && <div className="loading">Fetching citations. This may take a moment...</div>}
            
            {citations.length > 0 ? (
                <div className="citation-list">
                    <h3>Citations</h3>
                    <ul>
                        {citations.map((citation, index) => (
                            <li key={index} className="citation-item">
                                {typeof citation === 'object' ? (
                                    <div>
                                        <p className="citation-text">{citation.text || citation.citation}</p>
                                        {citation.source && <p className="citation-source">Source: {citation.source}</p>}
                                    </div>
                                ) : (
                                    <p>{citation}</p>
                                )}
                            </li>
                        ))}
                    </ul>
                </div>
            ) : selectedPaperId && !loading && !error ? (
                <div className="no-citations">No citations found for this paper</div>
            ) : null}
        </div>
    );
};

export default CitationDisplay; 