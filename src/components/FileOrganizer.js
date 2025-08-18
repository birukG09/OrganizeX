function FileOrganizer({ user, updateUser }) {
    const [selectedFolder, setSelectedFolder] = useState('');
    const [scanResults, setScanResults] = useState(null);
    const [isScanning, setIsScanning] = useState(false);
    const [isOrganizing, setIsOrganizing] = useState(false);
    const [organizationRules, setOrganizationRules] = useState({});

    const fileTypes = {
        'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
        'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
        'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods'],
        'Presentations': ['.ppt', '.pptx', '.odp'],
        'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
        'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
        'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'Code': ['.js', '.py', '.html', '.css', '.java', '.cpp', '.c'],
        'Executables': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm']
    };

    const quickFolders = [
        { name: 'Downloads', path: 'downloads', icon: 'fas fa-download' },
        { name: 'Desktop', path: 'desktop', icon: 'fas fa-desktop' },
        { name: 'Documents', path: 'documents', icon: 'fas fa-file-text' },
        { name: 'Pictures', path: 'pictures', icon: 'fas fa-image' }
    ];

    const scanFolder = async (folderPath) => {
        setIsScanning(true);
        try {
            const results = await API.scanFolder(folderPath);
            setScanResults(results);
        } catch (error) {
            console.error('Failed to scan folder:', error);
        } finally {
            setIsScanning(false);
        }
    };

    const organizeFiles = async () => {
        if (!scanResults) return;
        
        setIsOrganizing(true);
        try {
            const result = await API.organizeFiles(selectedFolder, organizationRules);
            if (result.success) {
                // Award XP based on files organized
                const xpGained = result.filesOrganized * 5;
                updateUser({
                    xp: user.xp + xpGained,
                    totalXp: user.totalXp + xpGained
                });
                
                // Refresh scan results
                await scanFolder(selectedFolder);
            }
        } catch (error) {
            console.error('Failed to organize files:', error);
        } finally {
            setIsOrganizing(false);
        }
    };

    const handleQuickFolder = (folderPath) => {
        setSelectedFolder(folderPath);
        scanFolder(folderPath);
    };

    const updateOrganizationRule = (fileType, enabled) => {
        setOrganizationRules(prev => ({
            ...prev,
            [fileType]: enabled
        }));
    };

    return (
        <div className="file-organizer">
            <div className="organizer-header">
                <h2>AI File Organizer</h2>
                <p>Let AI help you organize your files automatically!</p>
            </div>

            <div className="quick-folders">
                <h3>Quick Access</h3>
                <div className="folder-buttons">
                    {quickFolders.map(folder => (
                        <button
                            key={folder.path}
                            className={`folder-btn ${selectedFolder === folder.path ? 'active' : ''}`}
                            onClick={() => handleQuickFolder(folder.path)}
                        >
                            <i className={folder.icon}></i>
                            {folder.name}
                        </button>
                    ))}
                </div>
            </div>

            <div className="folder-selector">
                <h3>Custom Folder</h3>
                <div className="folder-input">
                    <input
                        type="text"
                        placeholder="Enter folder path..."
                        value={selectedFolder}
                        onChange={(e) => setSelectedFolder(e.target.value)}
                    />
                    <button 
                        className="scan-btn"
                        onClick={() => scanFolder(selectedFolder)}
                        disabled={!selectedFolder || isScanning}
                    >
                        {isScanning ? (
                            <>
                                <i className="fas fa-spinner fa-spin"></i>
                                Scanning...
                            </>
                        ) : (
                            <>
                                <i className="fas fa-search"></i>
                                Scan Folder
                            </>
                        )}
                    </button>
                </div>
            </div>

            {scanResults && (
                <div className="scan-results">
                    <h3>Scan Results</h3>
                    <div className="results-summary">
                        <div className="summary-card">
                            <i className="fas fa-file"></i>
                            <div>
                                <span className="summary-number">{scanResults.totalFiles}</span>
                                <span className="summary-label">Total Files</span>
                            </div>
                        </div>
                        <div className="summary-card">
                            <i className="fas fa-folder"></i>
                            <div>
                                <span className="summary-number">{scanResults.totalFolders}</span>
                                <span className="summary-label">Folders</span>
                            </div>
                        </div>
                        <div className="summary-card">
                            <i className="fas fa-hdd"></i>
                            <div>
                                <span className="summary-number">{scanResults.totalSize}</span>
                                <span className="summary-label">Total Size</span>
                            </div>
                        </div>
                    </div>

                    <div className="file-type-breakdown">
                        <h4>File Type Distribution</h4>
                        <div className="file-types">
                            {Object.entries(scanResults.fileTypes || {}).map(([type, count]) => (
                                <div key={type} className="file-type-card">
                                    <div className="file-type-header">
                                        <span className="file-type-name">{type}</span>
                                        <span className="file-type-count">{count} files</span>
                                        <label className="organization-toggle">
                                            <input
                                                type="checkbox"
                                                checked={organizationRules[type] || false}
                                                onChange={(e) => updateOrganizationRule(type, e.target.checked)}
                                            />
                                            <span className="toggle-slider"></span>
                                        </label>
                                    </div>
                                    <div className="file-extensions">
                                        {fileTypes[type]?.join(', ') || 'Various extensions'}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="organization-actions">
                        <button
                            className="organize-btn"
                            onClick={organizeFiles}
                            disabled={isOrganizing || Object.values(organizationRules).every(v => !v)}
                        >
                            {isOrganizing ? (
                                <>
                                    <i className="fas fa-spinner fa-spin"></i>
                                    Organizing...
                                </>
                            ) : (
                                <>
                                    <i className="fas fa-magic"></i>
                                    Organize Selected Types
                                </>
                            )}
                        </button>
                        <div className="organization-info">
                            <p>Selected types will be organized into dedicated folders</p>
                            <p>Estimated XP: +{Object.values(organizationRules).filter(Boolean).length * 25}</p>
                        </div>
                    </div>
                </div>
            )}

            {!scanResults && !isScanning && (
                <div className="no-results">
                    <i className="fas fa-folder-open"></i>
                    <h3>Select a folder to scan</h3>
                    <p>Choose a folder to analyze and organize your files</p>
                </div>
            )}
        </div>
    );
}
