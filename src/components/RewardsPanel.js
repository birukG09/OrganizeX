function RewardsPanel({ user }) {
    const [badges, setBadges] = useState([]);
    const [achievements, setAchievements] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadRewardsData();
    }, []);

    const loadRewardsData = async () => {
        try {
            const [badgeData, achievementData] = await Promise.all([
                API.getBadges(),
                API.getAchievements()
            ]);
            setBadges(badgeData);
            setAchievements(achievementData);
        } catch (error) {
            console.error('Failed to load rewards data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const getBadgeIcon = (badgeType) => {
        const icons = {
            'Clean Desk Novice': 'fas fa-desktop',
            'Download Slayer': 'fas fa-download',
            'Duplicate Destroyer': 'fas fa-copy',
            'File Master': 'fas fa-crown',
            'Organization Guru': 'fas fa-chart-line',
            'Speed Sorter': 'fas fa-bolt',
            'Streak Master': 'fas fa-fire',
            'Quest Completer': 'fas fa-tasks'
        };
        return icons[badgeType] || 'fas fa-medal';
    };

    const getLevelRewards = (level) => {
        const rewards = {
            1: 'Welcome Badge',
            5: 'Organization Novice Title',
            10: 'File Sorter Badge',
            15: 'Clutter Buster Title',
            20: 'Organization Expert Badge',
            25: 'Master Organizer Title',
            30: 'File Management Legend Badge'
        };
        return rewards[level] || null;
    };

    if (isLoading) {
        return <div className="loading">Loading rewards...</div>;
    }

    return (
        <div className="rewards-panel">
            <div className="rewards-header">
                <h2>Your Rewards</h2>
                <div className="user-level-info">
                    <div className="level-badge">
                        <i className="fas fa-star"></i>
                        <span>Level {user.level}</span>
                    </div>
                    <div className="total-xp">
                        <i className="fas fa-coins"></i>
                        <span>{user.totalXp} Total XP</span>
                    </div>
                </div>
            </div>

            <div className="rewards-content">
                <section className="badges-section">
                    <h3>
                        <i className="fas fa-medal"></i>
                        Badges ({user.badges?.length || 0})
                    </h3>
                    <div className="badges-grid">
                        {badges.map(badge => {
                            const isUnlocked = user.badges?.includes(badge.id);
                            return (
                                <div key={badge.id} className={`badge-card ${isUnlocked ? 'unlocked' : 'locked'}`}>
                                    <div className="badge-icon">
                                        <i className={getBadgeIcon(badge.name)}></i>
                                    </div>
                                    <h4>{badge.name}</h4>
                                    <p>{badge.description}</p>
                                    <div className="badge-requirements">
                                        {badge.requirements}
                                    </div>
                                    {isUnlocked && (
                                        <div className="badge-unlocked">
                                            <i className="fas fa-check"></i>
                                            Unlocked
                                        </div>
                                    )}
                                    {!isUnlocked && (
                                        <div className="badge-locked">
                                            <i className="fas fa-lock"></i>
                                            Locked
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </section>

                <section className="achievements-section">
                    <h3>
                        <i className="fas fa-trophy"></i>
                        Achievements
                    </h3>
                    <div className="achievements-list">
                        {achievements.map(achievement => {
                            const isCompleted = achievement.progress >= achievement.target;
                            return (
                                <div key={achievement.id} className={`achievement-card ${isCompleted ? 'completed' : ''}`}>
                                    <div className="achievement-icon">
                                        <i className={achievement.icon}></i>
                                    </div>
                                    <div className="achievement-content">
                                        <h4>{achievement.name}</h4>
                                        <p>{achievement.description}</p>
                                        <div className="achievement-progress">
                                            <div className="progress-bar">
                                                <div 
                                                    className="progress-fill"
                                                    style={{ width: `${Math.min((achievement.progress / achievement.target) * 100, 100)}%` }}
                                                ></div>
                                            </div>
                                            <span>{achievement.progress}/{achievement.target}</span>
                                        </div>
                                    </div>
                                    <div className="achievement-reward">
                                        +{achievement.xpReward} XP
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </section>

                <section className="level-rewards-section">
                    <h3>
                        <i className="fas fa-gift"></i>
                        Level Rewards
                    </h3>
                    <div className="level-rewards">
                        {[1, 5, 10, 15, 20, 25, 30].map(level => {
                            const reward = getLevelRewards(level);
                            const isUnlocked = user.level >= level;
                            
                            return reward && (
                                <div key={level} className={`level-reward ${isUnlocked ? 'unlocked' : 'locked'}`}>
                                    <div className="reward-level">
                                        Level {level}
                                    </div>
                                    <div className="reward-name">
                                        {reward}
                                    </div>
                                    <div className={`reward-status ${isUnlocked ? 'unlocked' : 'locked'}`}>
                                        <i className={isUnlocked ? 'fas fa-check' : 'fas fa-lock'}></i>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </section>

                <section className="stats-summary">
                    <h3>
                        <i className="fas fa-chart-bar"></i>
                        Your Journey
                    </h3>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <i className="fas fa-calendar-check"></i>
                            <h4>{user.streak}</h4>
                            <p>Day Streak</p>
                        </div>
                        <div className="stat-card">
                            <i className="fas fa-tasks"></i>
                            <h4>{user.completedQuests}</h4>
                            <p>Quests Completed</p>
                        </div>
                        <div className="stat-card">
                            <i className="fas fa-medal"></i>
                            <h4>{user.badges?.length || 0}</h4>
                            <p>Badges Earned</p>
                        </div>
                        <div className="stat-card">
                            <i className="fas fa-star"></i>
                            <h4>{user.level}</h4>
                            <p>Current Level</p>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
