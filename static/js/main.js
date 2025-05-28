document.addEventListener('DOMContentLoaded', function() {
    const receiptTextarea = document.getElementById('receipt-text');
    const parseButton = document.getElementById('parse-button');
    const clearButton = document.getElementById('clear-button');
    const copyButton = document.getElementById('copy-button');
    const resultContainer = document.getElementById('result-container');
    const errorAlert = document.getElementById('error-alert');
    const loadingSpinner = document.getElementById('loading-spinner');
    
    async function parseReceipt() {
        if (!receiptTextarea.value.trim()) {
            showError('Please enter receipt text');
            return;
        }
        
        hideError();
        loadingSpinner.classList.remove('d-none');
        
        try {
            const response = await fetch('/api/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ receipt_text: receiptTextarea.value }),
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to parse receipt');
            }
            
            displayJson(data);
        } catch (error) {
            showError(error.message || 'An error occurred');
        } finally {
            loadingSpinner.classList.add('d-none');
        }
    }
    
    function displayJson(data) {
        const formattedJson = JSON.stringify(data, null, 2);
        resultContainer.textContent = formattedJson;
        resultContainer.parentElement.classList.remove('d-none');
    }
    
    function clearAll() {
        receiptTextarea.value = '';
        resultContainer.textContent = '';
        resultContainer.parentElement.classList.add('d-none');
        hideError();
    }
    
    async function copyJsonToClipboard() {
        if (!resultContainer.textContent) return;
        
        try {
            await navigator.clipboard.writeText(resultContainer.textContent);
            const originalText = copyButton.textContent;
            copyButton.textContent = 'Copied!';
            setTimeout(() => {
                copyButton.textContent = originalText;
            }, 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    }
    
    function showError(message) {
        errorAlert.textContent = message;
        errorAlert.classList.remove('d-none');
    }
    
    function hideError() {
        errorAlert.classList.add('d-none');
    }
    
    if (parseButton) parseButton.addEventListener('click', parseReceipt);
    if (clearButton) clearButton.addEventListener('click', clearAll);
    if (copyButton) copyButton.addEventListener('click', copyJsonToClipboard);
});