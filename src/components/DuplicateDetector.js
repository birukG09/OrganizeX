function DuplicateDetector({ user, updateUser }) {
    const [duplicates, setDuplicates] = useState([]);
    const [isScanning, setIsScanning] = useState(false);
    const [scanPath, setScanPath] = useState('');
    const [selectedDuplicates, setSelectedDuplicates] = useState(new Set());
    const [scanProgress, setScanProgress] = useState(0);

    const scanForDuplicates = async (path = scanPath) => {
        setIsScanning(true);
        setScanProgress(0);
        setDuplicates([]);
        
        try {
            // Simulate progress updates
            const progressInterval = setInterval(() => {
                setScanProgress(prev => Math.min(prev + 10, 90));
            }, 500);

            const results = await API.scanDuplicates(path);
            clearInterval(progressInterval);
            setScanProgress(100);
            
            setDuplicates(results.duplicates || []);
        } catch (error) {
            console.error('Failed to scan for duplicates:', error);
        } finally {
            setIsScanning(false);
        }
    };

    const toggleDuplicateSelection = (duplicateId, fileId) => {
        const key = `${duplicateId}-${fileId}`;
        const newSelected = new Set(selectedDuplicates);
        
        if (newSelected.has(key)) {
            newSelected.delete(key);
        } else {
            newSelected.add(key);
        }
        
        setSelectedDuplicates(newSelected);
    };

    const deleteDuplicates = async () => {
        const filesToDelete = Array.from(selectedDuplicates).map(key => {
            const [duplicateId, fileId] = key.split('-');
            const duplicate = duplicates.find(d => d.id === duplicateId);
            return duplicate?.files.find(f => f.id === fileId);
        }).filter(Boolean);

        if (filesToDelete.length === 0) return;

        try {
            const result = await API.deleteDuplicateFiles(filesToDelete.map(f => f.path));
            if (result.success) {
                // Award XP for cleaning duplicates
                const xpGained = filesToDelete.length * 10;
                updateUser({
                    xp: user.xp + xpGained,
                    totalXp: user.totalXp + xpGained
                });

                // Remove deleted files from the list
                setDuplicates(prev => prev.map(duplicate => ({
                    ...duplicate,
                    files: duplicate.files.filter(file => 
                        !filesToDelete.some(deleted => deleted.path === file.path)
                    )
                })).filter(duplicate => duplicate.files.length > 1));

                setSelectedDuplicates(new Set());
            }
        } catch (error) {
            console.error('Failed to delete duplicates:', error);
        }
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const getTotalWastedSpace = () => {
        return duplicates.reduce((total, duplicate) => {
            // Count all files except the first one as wasted space
            return total + duplicate.files.slice(1).reduce((sum, file) => sum + file.size, 0);
        }, 0);
    };

    const quickScanOptions = [
        { name: 'Downloads', path: 'downloads', icon: 'fas fa-download' },
        { name: 'Pictures', path: 'pictures', icon: 'fas fa-image' },
        { name: 'Documents', path: 'documents', icon: 'fas fa-file-text' },
        { name: 'Entire System', path: '/', icon: 'fas fa-hdd' }
    ];

    return (
        <div className="duplicate-detector">
            <div className="detector-header">
                <h2>Duplicate File Detector</h2>
                <p>Find and remove duplicate files to free up space!</p>
            </div>

            <div className="scan-controls">
                <div className="quick-scan">
                    <h3>Quick Scan</h3>
                    <div className="quick-scan-buttons">
                        {quickScanOptions.map(option => (
                            <button
                                key={option.path}
                                className="quick-scan-btn"
                                onClick={() => scanForDuplicates(option.path)}
                                disabled={isScanning}
                            >
                                <i className={option.icon}></i>
                                {option.name}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="custom-scan">
                    <h3>Custom Path</h3>
                    <div className="scan-input">
                        <input
                            type="text"
                            placeholder="Enter path to scan..."
                            value={scanPath}
                            onChange={(e) => setScanPath(e.target.value)}
                        />
                        <button
                            className="scan-btn"
                            onClick={() => scanForDuplicates()}
                            disabled={!scanPath || isScanning}
                        >
                            {isScanning ? (
                                <>
                                    <i className="fas fa-spinner fa-spin"></i>
                                    Scanning...
                                </>
                            ) : (
                                <>
                                    <i className="fas fa-search"></i>
                                    Scan
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {isScanning && (
                <div className="scan-progress">
                    <h3>Scanning for duplicates...</h3>
                    <div className="progress-bar">
                        <div 
                            className="progress-fill" 
                            style={{ width: `${scanProgress}%` }}
                        ></div>
                    </div>
                    <span>{scanProgress}% complete</span>
                </div>
            )}

            {duplicates.length > 0 && (
                <div className="duplicate-results">
                    <div className="results-header">
                        <h3>Found {duplicates.length} duplicate groups</h3>
                        <div className="results-stats">
                            <span>Total wasted space: {formatFileSize(getTotalWastedSpace())}</span>
                            <span>Selected: {selectedDuplicates.size} files</span>
                        </div>
                        <button
                            className="delete-selected-btn"
                            onClick={deleteDuplicates}
                            disabled={selectedDuplicates.size === 0}
                        >
                            <i className="fas fa-trash"></i>
                            Delete Selected ({selectedDuplicates.size})
                        </button>
                    </div>

                    <div className="duplicate-groups">
                        {duplicates.map(duplicate => (
                            <div key={duplicate.id} className="duplicate-group">
                                <div className="group-header">
                                    <h4>
                                        <i className="fas fa-copy"></i>
                                        {duplicate.name}
                                    </h4>
                                    <span className="group-info">
                                        {duplicate.files.length} copies • {formatFileSize(duplicate.files[0].size)} each
                                    </span>
                                </div>
                                <div className="duplicate-files">
                                    {duplicate.files.map((file, index) => (
                                        <div key={file.id} className="duplicate-file">
                                            <label className="file-checkbox">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedDuplicates.has(`${duplicate.id}-${file.id}`)}
                                                    onChange={() => toggleDuplicateSelection(duplicate.id, file.id)}
                                                    disabled={index === 0} // Keep original file
                                                />
                                                <span className="checkmark"></span>
                                            </label>
                                            <div className="file-info">
                                                <div className="file-path">
                                                    {file.path}
                                                    {index === 0 && <span className="original-tag">Original</span>}
                                                </div>
                                                <div className="file-meta">
                                                    <span>Modified: {new Date(file.modified).toLocaleDateString()}</span>
                                                    <span>{formatFileSize(file.size)}</span>
                                                </div>
                                            </div>
                                            <div className="file-actions">
                                                <button className="preview-btn" title="Preview">
                                                    <i className="fas fa-eye"></i>
                                                </button>
                                                <button className="location-btn" title="Show in folder">
                                                    <i className="fas fa-folder-open"></i>
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {!isScanning && duplicates.length === 0 && scanPath && (
                <div className="no-duplicates">
                    <i className="fas fa-check-circle"></i>
                    <h3>No duplicates found!</h3>
                    <p>Your files are already well organized.</p>
                </div>
            )}

            {!isScanning && !scanPath && duplicates.length === 0 && (
                <div className="start-scanning">
                    <i className="fas fa-search"></i>
                    <h3>Start scanning for duplicates</h3>
                    <p>Choose a location to scan for duplicate files</p>
                </div>
            )}
        </div>
    );
}
