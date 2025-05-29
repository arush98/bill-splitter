// Main App Component
function App() {
    const [file, setFile] = React.useState(null);
    const [parsedData, setParsedData] = React.useState(null);
    const [users, setUsers] = React.useState([
        { id: 1, name: 'Roommate 1', active: true, color: 'primary' },
        { id: 2, name: 'Roommate 2', active: true, color: 'success' },
        { id: 3, name: 'Roommate 3', active: true, color: 'warning' },
        { id: 4, name: 'Roommate 4', active: true, color: 'info' }
    ]);
    const [items, setItems] = React.useState([]);
    const [distributionId, setDistributionId] = React.useState(null);
    const [showShareModal, setShowShareModal] = React.useState(false);

    // Handle file upload
    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file && file.type === 'application/pdf') {
            setFile(file);
        } else {
            showToast('Please select a valid PDF file', 'error');
        }
    };

    // Handle file drop
    const handleDrop = (event) => {
        event.preventDefault();
        const file = event.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            setFile(file);
        } else {
            showToast('Please select a valid PDF file', 'error');
        }
    };

    // Parse receipt and coerce price to number
    const parseReceipt = async () => {
        if (!file) {
            showToast('Please select a PDF file first', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload_pdf', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data) {
                setParsedData(data);
                setItems(data.items.map(item => ({
                    ...item,
                    price: Number(item.price), // ensure price is numeric
                    assignedUsers: []
                })));
                showToast('Receipt parsed successfully!', 'success');
            }
        } catch (error) {
            showToast(error.message || 'Error parsing receipt', 'error');
        }
    };

    // Toggle user active state
    const toggleUser = (userId) => {
        setUsers(users.map(user => 
            user.id === userId ? { ...user, active: !user.active } : user
        ));
    };

    // Update user name
    const updateUserName = (userId, newName) => {
        setUsers(users.map(user => 
            user.id === userId ? { ...user, name: newName } : user
        ));
    };

    // Toggle item assignment with functional update
    const toggleItemAssignment = (itemIndex, userId) => {
        setItems(prevItems =>
            prevItems.map((item, idx) => {
                if (idx !== itemIndex) return item;
                // Ensure userId is always a number
                const userIdNum = Number(userId);
                const has = item.assignedUsers.includes(userIdNum);
                return {
                    ...item,
                    assignedUsers: has
                        ? item.assignedUsers.filter(id => Number(id) !== userIdNum)
                        : [...item.assignedUsers, userIdNum]
                };
            })
        );
    };

    // Memoized share calculation
    const calculateShares = React.useMemo(() => {
        const active = users.filter(u => u.active);
        return active.map(user => {
            const userIdNum = Number(user.id);
            const total = items.reduce((sum, item) => {
                if (!item.assignedUsers.map(Number).includes(userIdNum) || item.assignedUsers.length === 0) return sum;
                return sum + item.price / item.assignedUsers.length;
            }, 0);
            return { id: userIdNum, total };
        });
    }, [items, users]);

    // Save distribution
    const saveDistribution = async () => {
        if (!calculateShares.length) return;

        try {
            const response = await fetch('/api/save_distribution', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    items,
                    users: users.filter(u => u.active),
                    total: items.reduce((sum, item) => sum + item.price, 0)
                })
            });

            if (response.ok) {
                const data = await response.json();
                setDistributionId(data.distribution_id);
                showToast('Distribution saved successfully!', 'success');
            }
        } catch (error) {
            showToast('Error saving distribution', 'error');
        }
    };

    // Share distribution
    const shareDistribution = () => {
        if (!distributionId) {
            showToast('Please save the distribution first', 'error');
            return;
        }
        setShowShareModal(true);
    };

    // Toast notification
    const showToast = (message, type = 'info') => {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        const container = document.querySelector('.toast-container') || (() => {
            const div = document.createElement('div');
            div.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(div);
            return div;
        })();

        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
            if (container.children.length === 0) {
                container.remove();
            }
        });
    };

    // Calculate total amount
    const totalAmount = items.reduce((sum, item) => sum + item.price, 0);

    return (
        <div className="container py-5">
            {/* File Upload Section */}
            <div className="card mb-4">
                <div className="card-header">
                    <h5 className="card-title mb-0">
                        <i className="fas fa-file-pdf me-2 text-primary"></i>
                        Upload Receipt
                    </h5>
                </div>
                <div className="card-body">
                    <div 
                        className="file-upload-container mb-4"
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={handleDrop}
                        onClick={() => document.getElementById('file-input').click()}
                    >
                        <input
                            type="file"
                            id="file-input"
                            accept=".pdf"
                            onChange={handleFileChange}
                            style={{ display: 'none' }}
                        />
                        {file ? (
                            <div>
                                <p className="h5 mb-1">{file.name}</p>
                                <small className="text-muted">
                                    {(file.size / 1024 / 1024).toFixed(2)} MB
                                </small>
                            </div>
                        ) : (
                            <div>
                                <i className="fas fa-file-pdf fa-3x mb-3 text-primary"></i>
                                <p className="h5 mb-2">Drag & Drop PDF here</p>
                                <p className="text-muted mb-0">or click to browse</p>
                            </div>
                        )}
                    </div>
                    
                    <div className="d-flex gap-2">
                        <button 
                            className="btn btn-primary flex-grow-1"
                            onClick={parseReceipt}
                            disabled={!file}
                        >
                            <i className="fas fa-magic me-2"></i>Parse Receipt
                        </button>
                        {parsedData && (
                            <>
                                <button 
                                    className="btn btn-success"
                                    onClick={saveDistribution}
                                >
                                    <i className="fas fa-save me-2"></i>Save
                                </button>
                                <button 
                                    className="btn btn-outline-primary"
                                    onClick={shareDistribution}
                                >
                                    <i className="fas fa-share-alt me-2"></i>Share
                                </button>
                            </>
                        )}
                        <button 
                            className="btn btn-outline-secondary"
                            onClick={() => {
                                setFile(null);
                                setParsedData(null);
                                setItems([]);
                            }}
                        >
                            <i className="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
            </div>

            {/* Results Section */}
            {parsedData && (
                <div className="card">
                    <div className="card-header">
                        <h5 className="card-title mb-0">
                            <i className="fas fa-list me-2 text-primary"></i>
                            Parsed Items
                        </h5>
                    </div>
                    <div className="card-body">
                        {/* Users Section */}
                        <div className="row g-3 mb-4">
                            {users.map(user => {
                                const share = calculateShares.find(s => s.id === user.id)?.total || 0;
                                return (
                                    <div key={user.id} className="col-md-3">
                                        <div className="card h-100">
                                            <div className="card-body">
                                                <div className="form-check mb-2">
                                                    <input
                                                        className="form-check-input"
                                                        type="checkbox"
                                                        checked={user.active}
                                                        onChange={() => toggleUser(user.id)}
                                                    />
                                                    <label className="form-check-label">
                                                        <input
                                                            type="text"
                                                            className="form-control form-control-sm"
                                                            value={user.name}
                                                            onChange={(e) => updateUserName(user.id, e.target.value)}
                                                        />
                                                    </label>
                                                </div>
                                                <div className="d-flex justify-content-between align-items-center">
                                                    <small className="text-muted">Total:</small>
                                                    <span className={`h5 mb-0 text-${user.color}`}>
                                                        ${share.toFixed(2)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Items List */}
                        <div className="items-list">
                            {items.map((item, index) => {
                                // Determine item category and icon
                                let category = 'other';
                                let icon = 'fa-shopping-basket';
                                let badgeColor = 'secondary';
                                const name = item.name.toLowerCase();
                                if (name.includes('milk') || name.includes('cheese') || name.includes('yogurt') || name.includes('butter') || name.includes('eggs')) {
                                    category = 'dairy';
                                    icon = 'fa-cheese';
                                    badgeColor = 'primary';
                                } else if (name.includes('bread') || name.includes('bun') || name.includes('bakery') || name.includes('french')) {
                                    category = 'bakery';
                                    icon = 'fa-bread-slice';
                                    badgeColor = 'warning';
                                } else if (name.includes('apple') || name.includes('banana') || name.includes('fruit') || name.includes('vegetable') || name.includes('cauliflower') || name.includes('pepper') || name.includes('onion')) {
                                    category = 'fruits';
                                    icon = 'fa-apple-alt';
                                    badgeColor = 'success';
                                } else if (name.includes('juice') || name.includes('water') || name.includes('coffee') || name.includes('drink') || name.includes('soda') || name.includes('bottle') || name.includes('beverage')) {
                                    category = 'beverages';
                                    icon = 'fa-coffee';
                                    badgeColor = 'info';
                                }
                                return (
                                    <div key={index} className="item-row mb-3 p-3 bg-light rounded">
                                        <div className="d-flex justify-content-between align-items-center">
                                            <div className="d-flex align-items-center">
                                                <div className="item-icon me-3">
                                                    <i className={`fas ${icon} fa-lg text-${badgeColor}`}></i>
                                                </div>
                                                <div>
                                                    <div className="item-name fw-bold">{item.name}</div>
                                                    <div className={`badge bg-${badgeColor} text-uppercase`}>{category}</div>
                                                    <div className="badge bg-light text-dark ms-2">${item.price.toFixed(2)}</div>
                                                </div>
                                            </div>
                                            <div className="d-flex align-items-center">
                                                <div className="btn-group me-3">
                                                    {users.map(user => (
                                                        <button
                                                            key={user.id}
                                                            className={`btn btn-sm ${
                                                                item.assignedUsers.map(Number).includes(Number(user.id))
                                                                    ? `btn-${user.color}`
                                                                    : `btn-outline-${user.color}`
                                                            }`}
                                                            onClick={() => toggleItemAssignment(index, user.id)}
                                                            disabled={!user.active}
                                                        >
                                                            <i className="fas fa-user"></i>{user.id}
                                                        </button>
                                                    ))}
                                                </div>
                                                <div className="text-end">
                                                    <small className="text-muted">
                                                        {item.assignedUsers.length > 0 
                                                            ? `$${(item.price / item.assignedUsers.length).toFixed(2)} each${item.assignedUsers.length > 1 ? ` (${item.assignedUsers.length} sharing)` : ''}`
                                                            : 'Not assigned'}
                                                    </small>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Total Amount */}
                        <div className="mt-4 pt-3 border-top">
                            <div className="d-flex justify-content-between align-items-center">
                                <h6 className="mb-0">Total Amount</h6>
                                <div className="h3 text-primary mb-0">${totalAmount.toFixed(2)}</div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Share Modal */}
            {showShareModal && (
                <div className="modal fade show" style={{ display: 'block' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">Share Receipt</h5>
                                <button 
                                    type="button" 
                                    className="btn-close"
                                    onClick={() => setShowShareModal(false)}
                                ></button>
                            </div>
                            <div className="modal-body">
                                <p className="mb-3">
                                    Share this link with your roommates:
                                </p>
                                <div className="input-group mb-3">
                                    <input
                                        type="text"
                                        className="form-control"
                                        value={`${window.location.origin}/distribution/${distributionId}`}
                                        readOnly
                                    />
                                    <button 
                                        className="btn btn-outline-primary"
                                        onClick={() => {
                                            navigator.clipboard.writeText(
                                                `${window.location.origin}/distribution/${distributionId}`
                                            );
                                            showToast('Link copied to clipboard!', 'success');
                                        }}
                                    >
                                        <i className="fas fa-copy"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Render the app
ReactDOM.render(
    <App />, 
    document.getElementById('app-root')
);