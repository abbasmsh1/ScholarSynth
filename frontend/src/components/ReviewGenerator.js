import React, { useState, useEffect } from 'react';
import api from '../api';

const ReviewGenerator = () => {
  const [papers, setPapers] = useState([]);
  const [selectedPaperId, setSelectedPaperId] = useState('');
  const [review, setReview] = useState(null);
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

  const generateReview = async () => {
    if (!selectedPaperId) {
      setError('Please select a paper first');
      return;
    }

    setLoading(true);
    setError(null);
    setReview(null);

    try {
      const response = await api.post(`/api/generate-review/${selectedPaperId}`);
      setReview(response.data);
    } catch (err) {
      console.error('Review generation error:', err);
      setError(err.response?.data?.detail || 'Failed to generate review');
    } finally {
      setLoading(false);
    }
  };

  const handlePaperChange = (e) => {
    setSelectedPaperId(e.target.value);
    setError(null);
    setReview(null);
  };

  return (
    <div>
      <div className="paper-selector">
        <label htmlFor="paper-select">Select a paper:</label>
        <select 
          id="paper-select"
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

      <div className="review-controls">
        <button 
          onClick={generateReview} 
          disabled={loading || !selectedPaperId}
          className="generate-button"
        >
          {loading ? 'Generating...' : 'Generate Review'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Generating review. This may take a moment...</div>}
      
      {review && (
        <div className="review-content">
          <h3>Review</h3>
          <div className="review-sections">
            {review.sections ? (
              review.sections.map((section, index) => (
                <div key={index} className="review-section-item">
                  <h4>{section.title}</h4>
                  <p>{section.content}</p>
                </div>
              ))
            ) : (
              <p>{review.content || 'No review content available'}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewGenerator; 