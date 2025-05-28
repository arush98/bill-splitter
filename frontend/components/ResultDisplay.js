import { useState } from 'react';

const ResultDisplay = ({ results, error, isLoading }) => {
  const [isCopied, setIsCopied] = useState(false);

  const handleCopyToClipboard = async () => {
    if (!results) return;
    
    try {
      await navigator.clipboard.writeText(JSON.stringify(results, null, 2));
      setIsCopied(true);
      
      setTimeout(() => {
        setIsCopied(false);
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  // Highlight JSON syntax
  const highlightJson = (json) => {
    if (!json) return null;
    
    const formattedJson = JSON.stringify(json, null, 2);
    return formattedJson
      .replace(/"([^"]+)":/g, '<span style="color: #9cdcfe;">"$1"</span>:')
      .replace(/: "([^"]+)"/g, ': <span style="color: #ce9178;">"$1"</span>')
      .replace(/: (\d+(\.\d+)?)/g, ': <span style="color: #b5cea8;">$1</span>');
  };
  
  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3">Parsing receipt with Gemini AI...</p>
        </div>
      );
    }
    
    if (error) {
      return (
        <div className="text-center py-5 text-danger">
          <i className="fas fa-exclamation-circle fa-3x mb-3"></i>
          <p>{error}</p>
        </div>
      );
    }
    
    if (!results) {
      return (
        <div className="text-center py-5 text-muted">
          <i className="fas fa-arrow-left fa-2x mb-3"></i>
          <p>Upload and parse a receipt to see the structured JSON output here</p>
        </div>
      );
    }
    
    return (
      <pre 
        className="p-3 rounded mb-0 code-block"
        dangerouslySetInnerHTML={{ __html: highlightJson(results) }}
      />
    );
  };

  return (
    <div className="card">
      <div className="card-header bg-dark d-flex justify-content-between align-items-center">
        <h5 className="card-title mb-0">
          <i className="fas fa-code me-2"></i>JSON Output
        </h5>
        <button 
          className="btn btn-sm btn-outline-secondary"
          onClick={handleCopyToClipboard}
          disabled={!results || isLoading}
        >
          {isCopied ? (
            <>
              <i className="fas fa-check me-1"></i>Copied!
            </>
          ) : (
            <>
              <i className="fas fa-copy me-1"></i>Copy JSON
            </>
          )}
        </button>
      </div>
      <div className="card-body p-0">
        <div className="json-display">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default ResultDisplay;