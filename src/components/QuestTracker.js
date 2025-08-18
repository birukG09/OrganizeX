function QuestTracker({ user, updateUser }) {
    const [quests, setQuests] = useState({
        daily: [],
        weekly: [],
        achievements: []
    });
    const [activeCategory, setActiveCategory] = useState('daily');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadQuests();
    }, []);

    const loadQuests = async () => {
        try {
            const questData = await API.getQuests();
            setQuests(questData);
        } catch (error) {
            console.error('Failed to load quests:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const completeQuest = async (questId, category) => {
        try {
            const result = await API.completeQuest(questId);
            if (result.success) {
                // Update quest status
                setQuests(prev => ({
                    ...prev,
                    [category]: prev[category].map(quest => 
                        quest.id === questId 
                            ? { ...quest, status: 'completed', completedAt: new Date().toISOString() }
                            : quest
                    )
                }));

                // Update user XP and level
                updateUser({
                    xp: user.xp + result.xpGained,
                    totalXp: user.totalXp + result.xpGained,
                    completedQuests: user.completedQuests + 1,
                    level: result.newLevel || user.level,
                    badges: result.newBadges ? [...user.badges, ...result.newBadges] : user.badges
                });
            }
        } catch (error) {
            console.error('Failed to complete quest:', error);
        }
    };

    const getQuestIcon = (type) => {
        const icons = {
            organize: 'fas fa-folder',
            clean: 'fas fa-broom',
            duplicate: 'fas fa-copy',
            sort: 'fas fa-sort',
            backup: 'fas fa-save',
            rename: 'fas fa-edit'
        };
        return icons[type] || 'fas fa-tasks';
    };

    const getQuestDifficulty = (difficulty) => {
        const colors = {
            easy: '#27AE60',
            medium: '#F1C40F',
            hard: '#E74C3C'
        };
        return colors[difficulty] || '#27AE60';
    };

    const categories = [
        { id: 'daily', label: 'Daily Quests', icon: 'fas fa-calendar-day' },
        { id: 'weekly', label: 'Weekly Quests', icon: 'fas fa-calendar-week' },
        { id: 'achievements', label: 'Achievements', icon: 'fas fa-trophy' }
    ];

    if (isLoading) {
        return <div className="loading">Loading quests...</div>;
    }

    return (
        <div className="quest-tracker">
            <div className="quest-header">
                <h2>Quest Tracker</h2>
                <p>Complete quests to earn XP and unlock achievements!</p>
            </div>

            <div className="quest-categories">
                {categories.map(category => (
                    <button
                        key={category.id}
                        className={`category-btn ${activeCategory === category.id ? 'active' : ''}`}
                        onClick={() => setActiveCategory(category.id)}
                    >
                        <i className={category.icon}></i>
                        {category.label}
                        <span className="quest-count">
                            {quests[category.id]?.length || 0}
                        </span>
                    </button>
                ))}
            </div>

            <div className="quest-list">
                {quests[activeCategory]?.length > 0 ? (
                    quests[activeCategory].map(quest => (
                        <div key={quest.id} className={`quest-card ${quest.status}`}>
                            <div className="quest-icon">
                                <i className={getQuestIcon(quest.type)}></i>
                            </div>
                            <div className="quest-content">
                                <h3>{quest.title}</h3>
                                <p>{quest.description}</p>
                                <div className="quest-meta">
                                    <span 
                                        className="quest-difficulty"
                                        style={{ color: getQuestDifficulty(quest.difficulty) }}
                                    >
                                        {quest.difficulty?.toUpperCase()}
                                    </span>
                                    <span className="quest-reward">+{quest.xpReward} XP</span>
                                    {quest.deadline && (
                                        <span className="quest-deadline">
                                            Due: {new Date(quest.deadline).toLocaleDateString()}
                                        </span>
                                    )}
                                </div>
                                {quest.progress !== undefined && (
                                    <div className="quest-progress">
                                        <div className="progress-bar">
                                            <div 
                                                className="progress-fill"
                                                style={{ width: `${(quest.progress / quest.target) * 100}%` }}
                                            ></div>
                                        </div>
                                        <span>{quest.progress}/{quest.target}</span>
                                    </div>
                                )}
                            </div>
                            <div className="quest-actions">
                                {quest.status === 'available' && (
                                    <button 
                                        className="quest-action-btn"
                                        onClick={() => completeQuest(quest.id, activeCategory)}
                                    >
                                        Start Quest
                                    </button>
                                )}
                                {quest.status === 'in_progress' && (
                                    <button 
                                        className="quest-action-btn"
                                        onClick={() => completeQuest(quest.id, activeCategory)}
                                    >
                                        Complete
                                    </button>
                                )}
                                {quest.status === 'completed' && (
                                    <div className="quest-completed">
                                        <i className="fas fa-check"></i>
                                        Completed
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="no-quests">
                        <i className="fas fa-scroll"></i>
                        <h3>No {activeCategory} quests available</h3>
                        <p>Check back later for new challenges!</p>
                    </div>
                )}
            </div>
        </div>
    );
}
