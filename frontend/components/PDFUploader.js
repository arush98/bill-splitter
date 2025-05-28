import { useState, useRef } from 'react';

const PDFUploader = ({ onSubmit, onClear, isLoading }) => {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
    } else {
      alert('Please select a valid PDF file');
    }
  };
  
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = () => {
    setIsDragging(false);
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
    } else {
      alert('Please drop a valid PDF file');
    }
  };
  
  const handleUploadClick = () => {
    fileInputRef.current.click();
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!file) {
      alert('Please select a PDF file first');
      return;
    }
    
    const formData = new FormData();
    formData.append('pdf', file);
    
    onSubmit(formData);
  };
  
  const handleClear = () => {
    setFile(null);
    onClear();
  };
  
  return (
    <div className="card">
      <div className="card-header bg-dark">
        <h5 className="card-title mb-0">
          <i className="fas fa-file-pdf me-2"></i>Upload Receipt PDF
        </h5>
      </div>
      <div className="card-body">
        <form onSubmit={handleSubmit}>
          <div 
            className={`file-upload-container mb-3 ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleUploadClick}
          >
            <input
              type="file"
              accept=".pdf"
              className="d-none"
              onChange={handleFileChange}
              ref={fileInputRef}
            />
            
            {file ? (
              <div>
                <i className="fas fa-file-pdf fa-2x text-success mb-2"></i>
                <p className="mb-0">{file.name}</p>
                <small className="text-muted">
                  {(file.size / 1024).toFixed(2)} KB
                </small>
              </div>
            ) : (
              <div>
                <i className="fas fa-cloud-upload-alt fa-2x text-secondary mb-2"></i>
                <p className="mb-0">Drag & Drop PDF here</p>
                <p className="small text-muted mb-0">or click to browse</p>
              </div>
            )}
          </div>
          
          <div className="d-flex">
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={!file || isLoading}
            >
              {isLoading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Processing...
                </>
              ) : (
                <>
                  <i className="fas fa-magic me-2"></i>Parse Receipt
                </>
              )}
            </button>
            
            <button 
              type="button" 
              className="btn btn-secondary ms-2"
              onClick={handleClear}
              disabled={isLoading}
            >
              <i className="fas fa-trash-alt me-2"></i>Clear
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PDFUploader;