function Dashboard({ user, updateUser }) {
    const [recentActivity, setRecentActivity] = useState([]);
    const [todaysQuests, setTodaysQuests] = useState([]);
    const [stats, setStats] = useState({
        filesOrganized: 0,
        duplicatesRemoved: 0,
        questsCompleted: 0
    });

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            const [activity, quests, userStats] = await Promise.all([
                API.getRecentActivity(),
                API.getTodaysQuests(),
                API.getUserStats()
            ]);
            setRecentActivity(activity);
            setTodaysQuests(quests);
            setStats(userStats);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    };

    const quickActions = [
        {
            title: 'Quick Sort Downloads',
            description: 'Organize your Downloads folder',
            icon: 'fas fa-download',
            action: () => API.quickSortFolder('downloads'),
            xp: 50
        },
        {
            title: 'Scan for Duplicates',
            description: 'Find duplicate files on your system',
            icon: 'fas fa-search',
            action: () => API.scanDuplicates(),
            xp: 30
        },
        {
            title: 'Clean Desktop',
            description: 'Organize files on your desktop',
            icon: 'fas fa-desktop',
            action: () => API.quickSortFolder('desktop'),
            xp: 40
        }
    ];

    const handleQuickAction = async (action) => {
        try {
            const result = await action.action();
            if (result.success) {
                updateUser({
                    xp: user.xp + action.xp,
                    totalXp: user.totalXp + action.xp
                });
                setRecentActivity(prev => [{
                    type: 'quick_action',
                    description: action.title,
                    xp: action.xp,
                    timestamp: new Date().toISOString()
                }, ...prev.slice(0, 4)]);
            }
        } catch (error) {
            console.error('Quick action failed:', error);
        }
    };

    return (
        <div className="dashboard">
            <div className="dashboard-grid">
                <div className="welcome-card">
                    <h2>Welcome back, Organizer!</h2>
                    <p>Ready to level up your file management game?</p>
                    <div className="level-progress">
                        <div className="level-info">
                            <span className="current-level">Level {user.level}</span>
                            <span className="next-level">Level {user.level + 1}</span>
                        </div>
                        <div className="progress-bar">
                            <div 
                                className="progress-fill" 
                                style={{width: `${(user.xp / (user.level * 100)) * 100}%`}}
                            ></div>
                        </div>
                        <div className="xp-info">
                            {user.xp} / {user.level * 100} XP
                        </div>
                    </div>
                </div>

                <div className="stats-card">
                    <h3>Your Stats</h3>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <i className="fas fa-folder-open"></i>
                            <div>
                                <span className="stat-number">{stats.filesOrganized}</span>
                                <span className="stat-label">Files Organized</span>
                            </div>
                        </div>
                        <div className="stat-item">
                            <i className="fas fa-trash"></i>
                            <div>
                                <span className="stat-number">{stats.duplicatesRemoved}</span>
                                <span className="stat-label">Duplicates Removed</span>
                            </div>
                        </div>
                        <div className="stat-item">
                            <i className="fas fa-trophy"></i>
                            <div>
                                <span className="stat-number">{stats.questsCompleted}</span>
                                <span className="stat-label">Quests Completed</span>
                            </div>
                        </div>
                        <div className="stat-item">
                            <i className="fas fa-fire"></i>
                            <div>
                                <span className="stat-number">{user.streak}</span>
                                <span className="stat-label">Day Streak</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="quick-actions-card">
                    <h3>Quick Actions</h3>
                    <div className="quick-actions">
                        {quickActions.map((action, index) => (
                            <button 
                                key={index}
                                className="quick-action-btn"
                                onClick={() => handleQuickAction(action)}
                            >
                                <i className={action.icon}></i>
                                <div>
                                    <h4>{action.title}</h4>
                                    <p>{action.description}</p>
                                    <span className="xp-reward">+{action.xp} XP</span>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="todays-quests-card">
                    <h3>Today's Quests</h3>
                    {todaysQuests.length > 0 ? (
                        <div className="quest-preview">
                            {todaysQuests.slice(0, 3).map(quest => (
                                <div key={quest.id} className="quest-item-small">
                                    <i className={quest.icon}></i>
                                    <div>
                                        <span className="quest-title">{quest.title}</span>
                                        <span className="quest-reward">+{quest.xpReward} XP</span>
                                    </div>
                                    <div className={`quest-status ${quest.status}`}>
                                        {quest.status === 'completed' && <i className="fas fa-check"></i>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="no-quests">No active quests today. Check back tomorrow!</p>
                    )}
                </div>

                <div className="recent-activity-card">
                    <h3>Recent Activity</h3>
                    {recentActivity.length > 0 ? (
                        <div className="activity-list">
                            {recentActivity.map((activity, index) => (
                                <div key={index} className="activity-item">
                                    <i className="fas fa-star"></i>
                                    <div>
                                        <span>{activity.description}</span>
                                        <span className="activity-xp">+{activity.xp} XP</span>
                                    </div>
                                    <span className="activity-time">
                                        {new Date(activity.timestamp).toLocaleDateString()}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="no-activity">Start organizing files to see your activity here!</p>
                    )}
                </div>
            </div>
        </div>
    );
}
