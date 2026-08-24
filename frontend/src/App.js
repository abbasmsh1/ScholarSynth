import React from 'react';
import './App.css';
import Upload from './components/Upload';
import ReviewGenerator from './components/ReviewGenerator';
import CitationDisplay from './components/CitationDisplay';

const IconUpload = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 15V4M12 4L7 9M12 4L17 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M4 15V17.8C4 18.9201 4 19.4802 4.21799 19.908C4.40973 20.2843 4.71569 20.5903 5.09202 20.782C5.51984 21 6.07989 21 7.2 21H16.8C17.9201 21 18.4802 21 18.908 20.782C19.2843 20.5903 19.5903 20.2843 19.782 19.908C20 19.4802 20 18.9201 20 17.8V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const IconSparkle = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 3L13.7 9.1C14.05 10.35 15.05 11.35 16.3 11.7L22.5 13.5L16.3 15.3C15.05 15.65 14.05 16.65 13.7 17.9L12 24L10.3 17.9C9.95 16.65 8.95 15.65 7.7 15.3L1.5 13.5L7.7 11.7C8.95 11.35 9.95 10.35 10.3 9.1L12 3Z" fill="currentColor" />
  </svg>
);

const IconQuote = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M7.5 8C5.567 8 4 9.567 4 11.5C4 13.433 5.567 15 7.5 15C7.5 17 6 18.5 4 18.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M17 8C15.067 8 13.5 9.567 13.5 11.5C13.5 13.433 15.067 15 17 15C17 17 15.5 18.5 13.5 18.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

function App() {
  return (
    <div className="App">
      <div className="bg-glow" aria-hidden="true" />
      <div className="container">
        <header className="app-header">
          <span className="eyebrow">Research Paper Assistant</span>
          <h1>Scholar<span className="accent-text">Synth</span></h1>
          <p className="app-subtitle">
            Upload papers, generate literature reviews, and manage citations in one place.
          </p>
        </header>

        <section className="panel">
          <div className="panel-header">
            <span className="panel-icon"><IconUpload /></span>
            <div className="panel-heading">
              <span className="panel-index">01</span>
              <h2>Upload papers</h2>
              <p className="panel-description">Drop in PDFs to extract text, authors, and metadata.</p>
            </div>
          </div>
          <Upload />
        </section>

        <section className="panel">
          <div className="panel-header">
            <span className="panel-icon"><IconSparkle /></span>
            <div className="panel-heading">
              <span className="panel-index">02</span>
              <h2>Generate review</h2>
              <p className="panel-description">Synthesize an uploaded paper into a structured literature review.</p>
            </div>
          </div>
          <ReviewGenerator />
        </section>

        <section className="panel">
          <div className="panel-header">
            <span className="panel-icon"><IconQuote /></span>
            <div className="panel-heading">
              <span className="panel-index">03</span>
              <h2>Citation management</h2>
              <p className="panel-description">Pull formatted citations for any paper you've uploaded.</p>
            </div>
          </div>
          <CitationDisplay />
        </section>

        <footer className="app-footer">
          <span>FastAPI</span>
          <span className="dot">·</span>
          <span>LangChain</span>
          <span className="dot">·</span>
          <span>spaCy</span>
          <span className="dot">·</span>
          <span>Together AI</span>
        </footer>
      </div>
    </div>
  );
}

export default App;
