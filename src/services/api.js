// API service for communicating with the backend
const API_BASE_URL = 'http://localhost:8000';

class APIService {
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options,
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // User data endpoints
    async getUserData() {
        try {
            return await this.request('/api/user');
        } catch (error) {
            // Return default user data if API fails
            return {
                level: 1,
                xp: 0,
                totalXp: 0,
                streak: 0,
                badges: [],
                completedQuests: 0
            };
        }
    }

    async updateUserData(userData) {
        return await this.request('/api/user', {
            method: 'PUT',
            body: userData
        });
    }

    async getUserStats() {
        try {
            return await this.request('/api/user/stats');
        } catch (error) {
            return {
                filesOrganized: 0,
                duplicatesRemoved: 0,
                questsCompleted: 0
            };
        }
    }

    // Quest endpoints
    async getQuests() {
        try {
            return await this.request('/api/quests');
        } catch (error) {
            return {
                daily: [],
                weekly: [],
                achievements: []
            };
        }
    }

    async getTodaysQuests() {
        try {
            return await this.request('/api/quests/today');
        } catch (error) {
            return [];
        }
    }

    async completeQuest(questId) {
        return await this.request(`/api/quests/${questId}/complete`, {
            method: 'POST'
        });
    }

    // File organization endpoints
    async scanFolder(folderPath) {
        return await this.request('/api/files/scan', {
            method: 'POST',
            body: { path: folderPath }
        });
    }

    async organizeFiles(folderPath, rules) {
        return await this.request('/api/files/organize', {
            method: 'POST',
            body: { 
                path: folderPath,
                rules: rules
            }
        });
    }

    async quickSortFolder(folderType) {
        return await this.request(`/api/files/quick-sort/${folderType}`, {
            method: 'POST'
        });
    }

    // Duplicate detection endpoints
    async scanDuplicates(path = '') {
        return await this.request('/api/duplicates/scan', {
            method: 'POST',
            body: { path: path || '/' }
        });
    }

    async deleteDuplicateFiles(filePaths) {
        return await this.request('/api/duplicates/delete', {
            method: 'DELETE',
            body: { files: filePaths }
        });
    }

    // Rewards endpoints
    async getBadges() {
        try {
            return await this.request('/api/rewards/badges');
        } catch (error) {
            return [
                {
                    id: 'clean_desk_novice',
                    name: 'Clean Desk Novice',
                    description: 'Organize your first folder',
                    requirements: 'Complete 1 organization quest'
                },
                {
                    id: 'download_slayer',
                    name: 'Download Slayer',
                    description: 'Master of the Downloads folder',
                    requirements: 'Clean Downloads folder 5 times'
                },
                {
                    id: 'duplicate_destroyer',
                    name: 'Duplicate Destroyer',
                    description: 'Remove 100 duplicate files',
                    requirements: 'Delete 100 duplicate files'
                },
                {
                    id: 'file_master',
                    name: 'File Master',
                    description: 'Organize 1000 files',
                    requirements: 'Organize 1000 files total'
                },
                {
                    id: 'organization_guru',
                    name: 'Organization Guru',
                    description: 'Reach level 20',
                    requirements: 'Achieve level 20'
                },
                {
                    id: 'speed_sorter',
                    name: 'Speed Sorter',
                    description: 'Complete 10 quests in one day',
                    requirements: 'Complete 10 quests in a single day'
                },
                {
                    id: 'streak_master',
                    name: 'Streak Master',
                    description: 'Maintain a 30-day streak',
                    requirements: 'Keep organizing for 30 days straight'
                },
                {
                    id: 'quest_completer',
                    name: 'Quest Completer',
                    description: 'Complete 100 quests',
                    requirements: 'Finish 100 quests total'
                }
            ];
        }
    }

    async getAchievements() {
        try {
            return await this.request('/api/rewards/achievements');
        } catch (error) {
            return [
                {
                    id: 'first_organization',
                    name: 'First Steps',
                    description: 'Complete your first file organization',
                    icon: 'fas fa-baby',
                    progress: 0,
                    target: 1,
                    xpReward: 100
                },
                {
                    id: 'file_organizer',
                    name: 'File Organizer',
                    description: 'Organize 100 files',
                    icon: 'fas fa-folder',
                    progress: 0,
                    target: 100,
                    xpReward: 500
                },
                {
                    id: 'duplicate_hunter',
                    name: 'Duplicate Hunter',
                    description: 'Find and remove 50 duplicate files',
                    icon: 'fas fa-search',
                    progress: 0,
                    target: 50,
                    xpReward: 300
                },
                {
                    id: 'quest_master',
                    name: 'Quest Master',
                    description: 'Complete 50 quests',
                    icon: 'fas fa-crown',
                    progress: 0,
                    target: 50,
                    xpReward: 1000
                },
                {
                    id: 'storage_saver',
                    name: 'Storage Saver',
                    description: 'Free up 1GB of space',
                    icon: 'fas fa-hdd',
                    progress: 0,
                    target: 1024, // MB
                    xpReward: 750
                }
            ];
        }
    }

    // Activity endpoints
    async getRecentActivity() {
        try {
            return await this.request('/api/activity/recent');
        } catch (error) {
            return [];
        }
    }

    async addActivity(activity) {
        return await this.request('/api/activity', {
            method: 'POST',
            body: activity
        });
    }
}

// Export singleton instance
const API = new APIService();
