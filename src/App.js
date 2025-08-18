const { useState, useEffect } = React;

function App() {
    const [user, setUser] = useState({
        level: 1,
        xp: 0,
        totalXp: 0,
        streak: 0,
        badges: [],
        completedQuests: 0
    });
    
    const [activeTab, setActiveTab] = useState('dashboard');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadUserData();
    }, []);

    const loadUserData = async () => {
        try {
            const userData = await API.getUserData();
            setUser(userData);
        } catch (error) {
            console.error('Failed to load user data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const updateUserData = (newData) => {
        setUser(prev => ({ ...prev, ...newData }));
    };

    const navigation = [
        { id: 'dashboard', label: 'Dashboard', icon: 'fas fa-home' },
        { id: 'quests', label: 'Quests', icon: 'fas fa-tasks' },
        { id: 'organizer', label: 'File Organizer', icon: 'fas fa-folder-open' },
        { id: 'duplicates', label: 'Duplicate Finder', icon: 'fas fa-copy' },
        { id: 'rewards', label: 'Rewards', icon: 'fas fa-trophy' }
    ];

    if (isLoading) {
        return (
            <div className="loading-screen">
                <div className="loading-spinner">
                    <i className="fas fa-cog fa-spin"></i>
                </div>
                <h2>Loading OrganizeX...</h2>
            </div>
        );
    }

    return (
        <div className="app">
            <header className="app-header">
                <div className="logo">
                    <i className="fas fa-gamepad"></i>
                    <h1>OrganizeX</h1>
                </div>
                <div className="user-stats">
                    <div className="stat">
                        <i className="fas fa-star"></i>
                        <span>Level {user.level}</span>
                    </div>
                    <div className="stat">
                        <i className="fas fa-fire"></i>
                        <span>{user.streak} day streak</span>
                    </div>
                    <div className="xp-bar">
                        <div className="xp-fill" style={{width: `${(user.xp / (user.level * 100)) * 100}%`}}></div>
                        <span>{user.xp}/{user.level * 100} XP</span>
                    </div>
                </div>
            </header>

            <nav className="app-nav">
                {navigation.map(item => (
                    <button 
                        key={item.id}
                        className={`nav-button ${activeTab === item.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(item.id)}
                    >
                        <i className={item.icon}></i>
                        {item.label}
                    </button>
                ))}
            </nav>

            <main className="app-main">
                {activeTab === 'dashboard' && <Dashboard user={user} updateUser={updateUserData} />}
                {activeTab === 'quests' && <QuestTracker user={user} updateUser={updateUserData} />}
                {activeTab === 'organizer' && <FileOrganizer user={user} updateUser={updateUserData} />}
                {activeTab === 'duplicates' && <DuplicateDetector user={user} updateUser={updateUserData} />}
                {activeTab === 'rewards' && <RewardsPanel user={user} />}
            </main>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));
