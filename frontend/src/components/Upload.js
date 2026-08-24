import React, { useState, useRef } from 'react';
import api from '../api';

const Upload = () => {
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef(null);

    const handleFileChange = (e) => {
        const selectedFiles = Array.from(e.target.files);
        if (selectedFiles.length === 0) return;
        
        // Validate if all files are PDFs
        const nonPdfFiles = selectedFiles.filter(file => !file.name.toLowerCase().endsWith('.pdf'));
        if (nonPdfFiles.length > 0) {
            setError(`Only PDF files are allowed. The following files were rejected: ${nonPdfFiles.map(f => f.name).join(', ')}`);
            // Only add the PDF files
            const pdfFiles = selectedFiles.filter(file => file.name.toLowerCase().endsWith('.pdf'));
            setFiles(prevFiles => [...prevFiles, ...pdfFiles]);
        } else {
            setFiles(prevFiles => [...prevFiles, ...selectedFiles]);
            setError('');
        }
    };

    const handleDragEnter = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!isDragging) {
            setIsDragging(true);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        
        const droppedFiles = Array.from(e.dataTransfer.files);
        if (droppedFiles.length === 0) return;
        
        // Filter out non-PDF files and notify user
        const pdfFiles = droppedFiles.filter(file => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'));
        const nonPdfFiles = droppedFiles.filter(file => !(file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')));
        
        if (nonPdfFiles.length > 0) {
            setError(`Only PDF files are allowed. ${nonPdfFiles.length} files were rejected.`);
        }
        
        if (pdfFiles.length > 0) {
            setFiles(prevFiles => [...prevFiles, ...pdfFiles]);
            if (nonPdfFiles.length === 0) {
                setError('');
            }
        } else {
            setError('Please drop at least one PDF file');
        }
    };

    const handleUpload = async () => {
        if (files.length === 0) {
            setError('Please select at least one PDF file');
            return;
        }

        setUploading(true);
        setError('');
        setMessage('');

        try {
            const formData = new FormData();
            files.forEach((file) => {
                formData.append('files', file);
            });

            const response = await api.post('/api/process-papers', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 60000, // Set a 60-second timeout
            });

            if (response.data.processed_papers && response.data.processed_papers.length > 0) {
                setMessage(`Successfully processed ${response.data.processed_papers.length} papers`);
                setFiles([]);
            } else {
                setError('No papers were processed. Please try again with different files.');
            }
        } catch (err) {
            console.error('Upload error:', err);
            
            let errorMessage = 'Error uploading papers. ';
            
            if (err.response) {
                // Server responded with a status code outside the 2xx range
                const statusCode = err.response.status;
                const detail = err.response.data.detail || 'Unknown error';
                
                if (statusCode === 400) {
                    errorMessage += `Bad request: ${detail}`;
                } else if (statusCode === 404) {
                    errorMessage += 'Server endpoint not found. Please ensure the API server is running properly.';
                } else if (statusCode === 413) {
                    errorMessage += 'Files too large. Please try with smaller files or fewer files.';
                } else if (statusCode === 500) {
                    errorMessage += `Server error: ${detail}`;
                } else {
                    errorMessage += `Error ${statusCode}: ${detail}`;
                }
            } else if (err.request) {
                // Request was made but no response received
                errorMessage += 'No response from server. Please check if the server is running.';
            } else if (err.code === 'ECONNABORTED') {
                errorMessage += 'Request timed out. The server is taking too long to respond.';
            } else {
                // Something else happened while setting up the request
                errorMessage += err.message || 'Unknown error occurred';
            }
            
            setError(errorMessage);
        } finally {
            setUploading(false);
        }
    };

    const removeFile = (index) => {
        setFiles(prev => {
            const newFiles = [...prev];
            newFiles.splice(index, 1);
            return newFiles;
        });
        
        // Clear error if there was an error related to file selection
        if (error.includes('PDF') || error.includes('select')) {
            setError('');
        }
    };
    
    const removeAllFiles = () => {
        setFiles([]);
        if (error.includes('PDF') || error.includes('select')) {
            setError('');
        }
    };
    
    const triggerFileInput = () => {
        fileInputRef.current.click();
    };

    return (
        <div className="upload-container">
            <div 
                className={`upload-area ${isDragging ? 'dragging' : ''}`}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={triggerFileInput}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="file-input"
                />
                <div className="upload-icon">
                    <svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 7L12 17M12 7L16 11M12 7L8 11" stroke="#3498db" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M20 16V17.2C20 18.8802 20 19.7202 19.673 20.362C19.3854 20.9265 18.9265 21.3854 18.362 21.673C17.7202 22 16.8802 22 15.2 22H8.8C7.11984 22 6.27976 22 5.63803 21.673C5.07354 21.3854 4.6146 20.9265 4.32698 20.362C4 19.7202 4 18.8802 4 17.2V16" stroke="#3498db" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                </div>
                <p>Drag & drop PDF files here or click to browse</p>
                <p className="file-hint">Supports multiple PDF files</p>
            </div>

            {files.length > 0 && (
                <div className="file-list">
                    <div className="file-list-header">
                        <h3>Selected Files: {files.length}</h3>
                        {files.length > 1 && (
                            <button 
                                onClick={(e) => {
                                    e.stopPropagation();
                                    removeAllFiles();
                                }}
                                className="remove-all-button"
                                aria-label="Remove all files"
                            >
                                Clear all
                            </button>
                        )}
                    </div>
                    <ul>
                        {files.map((file, index) => (
                            <li key={index} className="file-item">
                                <span title={file.name}>
                                    {file.name.length > 40 ? `${file.name.substring(0, 37)}...` : file.name}
                                    <span className="file-size">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                                </span>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        removeFile(index);
                                    }}
                                    className="remove-button"
                                    aria-label="Remove file"
                                >
                                    ×
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <button
                onClick={handleUpload}
                disabled={uploading || files.length === 0}
                className="upload-button"
            >
                {uploading ? 'Uploading...' : 'Upload Papers'}
            </button>

            {error && <div className="error">{error}</div>}
            {message && <div className="success">{message}</div>}
            {uploading && <div className="loading">Uploading files. This may take a moment depending on file size...</div>}
        </div>
    );
};

export default Upload; 