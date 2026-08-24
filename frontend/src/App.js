import React from 'react';
import './App.css';
import Upload from './components/Upload';
import ReviewGenerator from './components/ReviewGenerator';
import CitationDisplay from './components/CitationDisplay';

function App() {
  return (
    <div className="App">
      <div className="container">
        <header className="app-header">
          <span className="eyebrow">Research Paper Assistant</span>
          <h1>ScholarSynth</h1>
          <p className="app-subtitle">
            Upload papers, generate literature reviews, and manage citations in one place.
          </p>
        </header>

        <section className="panel">
          <h2>Upload Papers</h2>
          <Upload />
        </section>

        <section className="panel">
          <h2>Generate Review</h2>
          <ReviewGenerator />
        </section>

        <section className="panel">
          <h2>Citation Management</h2>
          <CitationDisplay />
        </section>
      </div>
    </div>
  );
}

export default App;
