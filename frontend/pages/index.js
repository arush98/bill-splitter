import { useState } from 'react';
import Head from 'next/head';
import PDFUploader from '../components/PDFUploader';
import ResultDisplay from '../components/ResultDisplay';

export default function Home() {
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (formData) => {
    setError(null);
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/parse_pdf', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to parse receipt');
      }
      
      setResults(data);
    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'Failed to parse receipt');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleClear = () => {
    setResults(null);
    setError(null);
  };

  return (
    <div data-bs-theme="dark">
      <Head>
        <title>Walmart Receipt Parser</title>
        <meta name="description" content="Parse Walmart receipts to extract structured data in JSON format" />
      </Head>

      <div className="container py-4">
        <header className="app-header">
          <div className="d-flex align-items-center mb-3">
            <h1 className="mb-0">
              <i className="fas fa-receipt text-primary me-3"></i>
              Walmart Receipt Parser
            </h1>
          </div>
          <p className="lead">
            Upload a Walmart receipt PDF and extract structured item data as JSON
          </p>
        </header>

        <main>
          <div className="row">
            <div className="col-lg-5">
              <PDFUploader 
                onSubmit={handleSubmit} 
                onClear={handleClear}
                isLoading={isLoading}
              />
              
              <div className="card">
                <div className="card-header bg-dark">
                  <h5 className="card-title mb-0">
                    <i className="fas fa-info-circle me-2"></i>
                    Instructions
                  </h5>
                </div>
                <div className="card-body">
                  <ol className="mb-0">
                    <li className="mb-2">Upload a PDF file of a Walmart receipt</li>
                    <li className="mb-2">Click "Parse Receipt" to extract the item data</li>
                    <li className="mb-2">View the extracted JSON data</li>
                    <li>Copy the JSON output for your application</li>
                  </ol>
                </div>
              </div>
            </div>
            
            <div className="col-lg-7">
              <ResultDisplay 
                results={results} 
                error={error} 
                isLoading={isLoading}
              />
            </div>
          </div>
        </main>
        
        <footer className="app-footer text-center text-muted">
          <p className="mb-0">
            <small>
              Walmart Receipt Parser | Uses Gemini AI for extraction
            </small>
          </p>
        </footer>
      </div>
    </div>
  );
}