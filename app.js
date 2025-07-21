// Multi-Agent Customer Sentiment Watchdog Dashboard
class SentimentWatchdog {
    constructor() {
        this.messages = [];
        this.alerts = [];
        this.config = {
            refreshInterval: 5000,
            alertThreshold: 40,
            batchSize: 10,
            autoProcessing: true,
            realTimeAlerts: true
        };
        
        // Sample data from the provided JSON
        this.sampleMessages = [
            {
                id: "msg001",
                source: "Email",
                sender: "john.doe@example.com",
                subject: "Account Access Issue",
                message: "I've been trying to access my account for hours and keep getting error messages. This is extremely frustrating!",
                sentiment: "anger",
                confidence: 0.92,
                keywords: ["frustrated", "error", "access", "hours"],
                timestamp: new Date("2024-01-15T14:30:00Z")
            },
            {
                id: "msg002", 
                source: "Form_Contact",
                sender: "sarah.smith@company.com",
                subject: "Thank you for great service",
                message: "I just wanted to thank your team for the excellent support. The response was quick and very helpful!",
                sentiment: "delight",
                confidence: 0.95,
                keywords: ["thank", "excellent", "quick", "helpful"],
                timestamp: new Date("2024-01-15T13:45:00Z")
            },
            {
                id: "msg003",
                source: "Form_Support", 
                sender: "mike.johnson@tech.com",
                subject: "Setup Confusion",
                message: "I'm not sure how to configure the new features. The documentation seems unclear to me.",
                sentiment: "confusion",
                confidence: 0.87,
                keywords: ["not sure", "configure", "unclear", "documentation"],
                timestamp: new Date("2024-01-15T12:20:00Z")
            },
            {
                id: "msg004",
                source: "Email",
                sender: "info@business.com", 
                subject: "Invoice Question",
                message: "Could you please send me a copy of last month's invoice? I need it for our records.",
                sentiment: "neutral",
                confidence: 0.78,
                keywords: ["invoice", "copy", "records"],
                timestamp: new Date("2024-01-15T11:15:00Z")
            }
        ];

        this.formTemplates = {
            contact: {
                angry: "I am extremely disappointed with the service quality. My issue has not been resolved for weeks!",
                confused: "I'm having trouble understanding how to use the new dashboard. Could someone help me?",
                happy: "Your team did an amazing job helping me solve my problem. Thank you so much!",
                neutral: "I would like to inquire about your pricing plans for enterprise customers."
            },
            feedback: {
                angry: "The recent update has made the application much slower. This is very frustrating!",
                confused: "I can't find the export feature anymore. Where did it go?", 
                happy: "Love the new interface! It's much more intuitive and user-friendly.",
                neutral: "The system works as expected. No major issues to report."
            },
            support: {
                angry: "My data was lost during the sync process. This is completely unacceptable!",
                confused: "I don't understand why my reports are showing different numbers now.",
                happy: "The new backup feature saved me a lot of time. Great addition!",
                neutral: "I need help setting up the API integration for our system."
            }
        };

        this.emailTemplates = [
            {
                from: "customer@company.com",
                subject: "Billing Discrepancy",
                message: "There seems to be an error in my latest bill. I was charged twice for the same service.",
                sentiment: "confusion"
            },
            {
                from: "support@client.org",
                subject: "Service Outage",
                message: "Our entire team has been unable to access the platform for 2 hours. This is costing us money!",
                sentiment: "anger"
            },
            {
                from: "manager@startup.io", 
                subject: "Excellent Support",
                message: "I wanted to commend your support team. They resolved our complex integration issue in record time!",
                sentiment: "delight"
            }
        ];

        this.sentimentColors = {
            anger: '#ff4444',
            confusion: '#ff8800', 
            delight: '#44ff44',
            neutral: '#888888'
        };

        this.charts = {};
        this.refreshTimer = null;
        this.currentTab = 'dashboard';

        this.init();
    }

    init() {
        // Initialize with sample data
        this.messages = [...this.sampleMessages];
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize charts
        this.initializeCharts();
        
        // Update dashboard
        this.updateDashboard();
        
        // Start auto-refresh
        this.startAutoRefresh();

        // Generate some historical data for better charts
        this.generateHistoricalData();

        // Load configuration values into form
        this.loadConfigurationForm();

        // Ensure dashboard tab is shown initially
        this.switchTab('dashboard');
    }

    setupEventListeners() {
        // Tab navigation - Robust implementation
        document.querySelectorAll('[data-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const tabName = e.currentTarget.getAttribute('data-tab');
                if (tabName) {
                    this.switchTab(tabName);
                }
            });
        });

        // Form submission simulator
        const formSimulator = document.getElementById('formSimulator');
        if (formSimulator) {
            formSimulator.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitForm();
            });
        }

        // Template buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('template-btn')) {
                e.preventDefault();
                const sentiment = e.target.getAttribute('data-sentiment');
                if (sentiment) {
                    this.useTemplate(sentiment);
                }
            }
        });

        // Email simulator buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('email-sim-btn')) {
                e.preventDefault();
                const sentiment = e.target.getAttribute('data-sentiment');
                if (sentiment) {
                    this.simulateEmail(sentiment);
                }
            }
        });

        const randomEmailBtn = document.getElementById('randomEmailBtn');
        if (randomEmailBtn) {
            randomEmailBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.simulateRandomEmail();
            });
        }

        // Configuration form
        const configForm = document.getElementById('configForm');
        if (configForm) {
            configForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveConfiguration();
            });
        }

        // Refresh button
        const refreshBtn = document.getElementById('refreshMessages');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.updateDashboard();
            });
        }

        // Alert close button
        const closeAlertBtn = document.getElementById('closeAlert');
        if (closeAlertBtn) {
            closeAlertBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.closeAlert();
            });
        }

        // Clear alerts button
        const clearAlertsBtn = document.getElementById('clearAlerts');
        if (clearAlertsBtn) {
            clearAlertsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearAlerts();
            });
        }
    }

    switchTab(tabName) {
        console.log('Switching to tab:', tabName);
        
        // Update nav items - remove active class from all
        document.querySelectorAll('.nav__item').forEach(item => {
            item.classList.remove('nav__item--active');
        });
        
        // Add active class to selected tab
        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('nav__item--active');
        }

        // Hide all tab content by adding hidden class
        const allTabs = ['dashboard', 'simulators', 'config', 'alerts'];
        allTabs.forEach(tab => {
            const tabElement = document.getElementById(tab);
            if (tabElement) {
                tabElement.style.display = 'none';
                tabElement.classList.add('hidden');
            }
        });

        // Show selected tab content
        const selectedContent = document.getElementById(tabName);
        if (selectedContent) {
            selectedContent.style.display = 'block';
            selectedContent.classList.remove('hidden');
            console.log(`Tab content shown for: ${tabName}`);
        } else {
            console.error(`Tab content not found for: ${tabName}`);
        }

        this.currentTab = tabName;

        // Update specific tab content when switching
        if (tabName === 'alerts') {
            this.updateAlertsTab();
        } else if (tabName === 'config') {
            this.loadConfigurationForm();
        } else if (tabName === 'dashboard') {
            this.updateDashboard();
        }
    }

    loadConfigurationForm() {
        // Load current configuration values into the form
        setTimeout(() => {
            const refreshIntervalEl = document.getElementById('refreshInterval');
            const alertThresholdEl = document.getElementById('alertThreshold');
            const batchSizeEl = document.getElementById('batchSize');
            const autoProcessingEl = document.getElementById('autoProcessing');
            const realTimeAlertsEl = document.getElementById('realTimeAlerts');

            if (refreshIntervalEl) refreshIntervalEl.value = this.config.refreshInterval / 1000;
            if (alertThresholdEl) alertThresholdEl.value = this.config.alertThreshold;
            if (batchSizeEl) batchSizeEl.value = this.config.batchSize;
            if (autoProcessingEl) autoProcessingEl.checked = this.config.autoProcessing;
            if (realTimeAlertsEl) realTimeAlertsEl.checked = this.config.realTimeAlerts;
        }, 100);
    }

    generateHistoricalData() {
        const now = new Date();
        const oneHourAgo = new Date(now.getTime() - (60 * 60 * 1000));
        const twoHoursAgo = new Date(now.getTime() - (2 * 60 * 60 * 1000));
        
        const additionalMessages = [
            {
                id: "hist001",
                source: "Email",
                sender: "user1@example.com",
                subject: "Great experience",
                message: "Everything worked perfectly!",
                sentiment: "delight",
                confidence: 0.9,
                timestamp: twoHoursAgo
            },
            {
                id: "hist002",
                source: "Form_Feedback",
                sender: "user2@example.com",
                subject: "System issues",
                message: "The system keeps crashing when I try to save my work!",
                sentiment: "anger",
                confidence: 0.88,
                timestamp: oneHourAgo
            },
            {
                id: "hist003",
                source: "Form_Support",
                sender: "user3@example.com",
                subject: "How to use feature X?",
                message: "I can't figure out how to use the new feature. Can you help?",
                sentiment: "confusion",
                confidence: 0.85,
                timestamp: oneHourAgo
            }
        ];

        this.messages.push(...additionalMessages);
    }

    initializeCharts() {
        // Wait a bit for DOM to be ready
        setTimeout(() => {
            // Pie chart for sentiment distribution
            const pieCanvas = document.getElementById('sentimentPieChart');
            if (pieCanvas) {
                const pieCtx = pieCanvas.getContext('2d');
                this.charts.pie = new Chart(pieCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Anger', 'Confusion', 'Delight', 'Neutral'],
                        datasets: [{
                            data: [0, 0, 0, 0],
                            backgroundColor: [
                                this.sentimentColors.anger,
                                this.sentimentColors.confusion,
                                this.sentimentColors.delight,
                                this.sentimentColors.neutral
                            ],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    padding: 20,
                                    usePointStyle: true
                                }
                            }
                        }
                    }
                });
            }

            // Line chart for sentiment trends
            const lineCanvas = document.getElementById('sentimentLineChart');
            if (lineCanvas) {
                const lineCtx = lineCanvas.getContext('2d');
                this.charts.line = new Chart(lineCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [
                            {
                                label: 'Anger',
                                data: [],
                                borderColor: this.sentimentColors.anger,
                                backgroundColor: this.sentimentColors.anger + '20',
                                tension: 0.4,
                                fill: false
                            },
                            {
                                label: 'Confusion',
                                data: [],
                                borderColor: this.sentimentColors.confusion,
                                backgroundColor: this.sentimentColors.confusion + '20',
                                tension: 0.4,
                                fill: false
                            },
                            {
                                label: 'Delight',
                                data: [],
                                borderColor: this.sentimentColors.delight,
                                backgroundColor: this.sentimentColors.delight + '20',
                                tension: 0.4,
                                fill: false
                            },
                            {
                                label: 'Neutral',
                                data: [],
                                borderColor: this.sentimentColors.neutral,
                                backgroundColor: this.sentimentColors.neutral + '20',
                                tension: 0.4,
                                fill: false
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                position: 'top'
                            }
                        }
                    }
                });
            }
        }, 500);
    }

    updateDashboard() {
        this.updateMetrics();
        this.updateCharts();
        this.updateMessages();
        this.checkForAlerts();
    }

    updateMetrics() {
        const total = this.messages.length;
        const processed = this.messages.filter(m => m.sentiment).length;
        const pending = total - processed;
        const activeAlerts = this.alerts.filter(a => !a.dismissed).length;

        const totalEl = document.getElementById('totalTickets');
        const processedEl = document.getElementById('processedTickets');
        const pendingEl = document.getElementById('pendingTickets');
        const alertsEl = document.getElementById('alertCount');

        if (totalEl) totalEl.textContent = total;
        if (processedEl) processedEl.textContent = processed;
        if (pendingEl) pendingEl.textContent = pending;
        if (alertsEl) alertsEl.textContent = activeAlerts;
    }

    updateCharts() {
        // Update pie chart
        const sentimentCounts = {
            anger: 0,
            confusion: 0,
            delight: 0,
            neutral: 0
        };

        this.messages.forEach(msg => {
            if (msg.sentiment && sentimentCounts.hasOwnProperty(msg.sentiment)) {
                sentimentCounts[msg.sentiment]++;
            }
        });

        if (this.charts.pie) {
            this.charts.pie.data.datasets[0].data = [
                sentimentCounts.anger,
                sentimentCounts.confusion,
                sentimentCounts.delight,
                sentimentCounts.neutral
            ];
            this.charts.pie.update();
        }

        // Update line chart with hourly data
        const now = new Date();
        const hoursBack = 6;
        const hourlyData = {};

        for (let i = hoursBack; i >= 0; i--) {
            const hour = new Date(now.getTime() - (i * 60 * 60 * 1000));
            const hourKey = hour.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            hourlyData[hourKey] = { anger: 0, confusion: 0, delight: 0, neutral: 0 };
        }

        this.messages.forEach(msg => {
            if (msg.sentiment && msg.timestamp) {
                const msgHour = msg.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                const closestHour = Object.keys(hourlyData).find(h => {
                    const timeDiff = Math.abs(new Date(`1970/01/01 ${h}`).getTime() - new Date(`1970/01/01 ${msgHour}`).getTime());
                    return timeDiff < 30 * 60 * 1000; // Within 30 minutes
                });
                if (closestHour && hourlyData[closestHour] && hourlyData[closestHour].hasOwnProperty(msg.sentiment)) {
                    hourlyData[closestHour][msg.sentiment]++;
                }
            }
        });

        if (this.charts.line) {
            this.charts.line.data.labels = Object.keys(hourlyData);
            this.charts.line.data.datasets[0].data = Object.values(hourlyData).map(h => h.anger);
            this.charts.line.data.datasets[1].data = Object.values(hourlyData).map(h => h.confusion);
            this.charts.line.data.datasets[2].data = Object.values(hourlyData).map(h => h.delight);
            this.charts.line.data.datasets[3].data = Object.values(hourlyData).map(h => h.neutral);
            this.charts.line.update();
        }
    }

    updateMessages() {
        const container = document.getElementById('messagesTable');
        if (!container) return;

        const recentMessages = [...this.messages]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 10);

        container.innerHTML = recentMessages.map(msg => `
            <div class="message-item">
                <div class="message-sentiment message-sentiment--${msg.sentiment || 'neutral'}">
                    ${this.getSentimentEmoji(msg.sentiment)}
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <div class="message-source">${msg.source}</div>
                        <div class="message-sender">${msg.sender}</div>
                        <div class="message-time">${this.formatTime(msg.timestamp)}</div>
                    </div>
                    <div class="message-subject">${msg.subject}</div>
                    <div class="message-text">${msg.message}</div>
                </div>
            </div>
        `).join('');
    }

    getSentimentEmoji(sentiment) {
        const emojis = {
            anger: '😡',
            confusion: '🤔',
            delight: '😊',
            neutral: '😐'
        };
        return emojis[sentiment] || '❓';
    }

    formatTime(timestamp) {
        if (!timestamp) return 'Unknown';
        const now = new Date();
        const diff = now - new Date(timestamp);
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) return `${hours}h ago`;
        if (minutes > 0) return `${minutes}m ago`;
        return 'Just now';
    }

    submitForm() {
        const formType = document.getElementById('formType').value;
        const name = document.getElementById('customerName').value || 'Anonymous User';
        const email = document.getElementById('customerEmail').value || 'user@example.com';
        const subject = document.getElementById('messageSubject').value || 'No Subject';
        const message = document.getElementById('messageText').value;

        if (!message) {
            alert('Please enter a message');
            return;
        }

        // Simple sentiment analysis based on keywords
        const sentiment = this.analyzeSentiment(message);

        const newMessage = {
            id: 'msg' + Date.now(),
            source: `Form_${formType.charAt(0).toUpperCase() + formType.slice(1)}`,
            sender: email,
            subject: subject,
            message: message,
            sentiment: sentiment,
            confidence: 0.85,
            timestamp: new Date()
        };

        this.messages.push(newMessage);
        this.updateDashboard();

        // Reset form
        document.getElementById('formSimulator').reset();

        // Show success message
        this.showNotification(`Form submitted successfully! Sentiment: ${sentiment}`, 'success');
        
        // Switch to dashboard to show results
        this.switchTab('dashboard');
    }

    useTemplate(sentimentType) {
        const formTypeEl = document.getElementById('formType');
        const messageTextEl = document.getElementById('messageText');
        
        if (formTypeEl && messageTextEl) {
            const formType = formTypeEl.value;
            const template = this.formTemplates[formType][sentimentType];
            if (template) {
                messageTextEl.value = template;
            }
        }
    }

    analyzeSentiment(message) {
        const lowerMessage = message.toLowerCase();
        
        const angerWords = ['angry', 'furious', 'frustrated', 'unacceptable', 'terrible', 'worst', 'hate', 'awful', 'disappointed'];
        const confusionWords = ['confused', 'unclear', 'don\'t understand', 'not sure', 'how to', 'help me', 'can\'t find'];
        const delightWords = ['great', 'excellent', 'amazing', 'wonderful', 'love', 'perfect', 'thank you', 'fantastic'];
        
        const angerScore = angerWords.filter(word => lowerMessage.includes(word)).length;
        const confusionScore = confusionWords.filter(word => lowerMessage.includes(word)).length;
        const delightScore = delightWords.filter(word => lowerMessage.includes(word)).length;
        
        if (angerScore > confusionScore && angerScore > delightScore) return 'anger';
        if (confusionScore > delightScore) return 'confusion';
        if (delightScore > 0) return 'delight';
        return 'neutral';
    }

    simulateEmail(sentiment) {
        const templates = this.emailTemplates.filter(t => t.sentiment === sentiment);
        const template = templates[Math.floor(Math.random() * templates.length)];

        if (!template) return;

        const newMessage = {
            id: 'email' + Date.now(),
            source: 'Email',
            sender: template.from,
            subject: template.subject,
            message: template.message,
            sentiment: template.sentiment,
            confidence: 0.9,
            timestamp: new Date()
        };

        this.messages.push(newMessage);
        this.updateDashboard();

        this.showEmailStatus(`Email received from ${template.from}`);
    }

    simulateRandomEmail() {
        const sentiments = ['anger', 'confusion', 'delight'];
        const randomSentiment = sentiments[Math.floor(Math.random() * sentiments.length)];
        this.simulateEmail(randomSentiment);
    }

    showEmailStatus(message) {
        const statusEl = document.getElementById('emailStatus');
        const statusText = document.getElementById('emailStatusText');
        
        if (statusText) statusText.textContent = message;
        if (statusEl) {
            statusEl.style.display = 'block';
            setTimeout(() => {
                statusEl.style.display = 'none';
            }, 3000);
        }
    }

    checkForAlerts() {
        if (!this.config.realTimeAlerts) return;

        const recentMessages = this.messages
            .filter(msg => new Date() - new Date(msg.timestamp) < 10 * 60 * 1000) // Last 10 minutes
            .slice(-5); // Last 5 messages

        if (recentMessages.length === 0) return;

        const negativeCount = recentMessages.filter(msg => 
            msg.sentiment === 'anger' || msg.sentiment === 'confusion'
        ).length;

        const negativePercentage = (negativeCount / recentMessages.length) * 100;

        if (negativePercentage >= this.config.alertThreshold) {
            const alert = {
                id: 'alert' + Date.now(),
                type: 'negative_spike',
                title: 'High Negative Sentiment Detected',
                description: `${negativePercentage.toFixed(1)}% of recent messages show negative sentiment`,
                timestamp: new Date(),
                dismissed: false
            };

            this.alerts.unshift(alert);
            this.showAlert(alert);
            
            if (this.currentTab === 'alerts') {
                this.updateAlertsTab();
            }
        }
    }

    showAlert(alert) {
        const banner = document.getElementById('alertBanner');
        const message = document.getElementById('alertMessage');
        
        if (message) message.textContent = alert.description;
        if (banner) banner.style.display = 'block';
    }

    closeAlert() {
        const banner = document.getElementById('alertBanner');
        if (banner) banner.style.display = 'none';
    }

    updateAlertsTab() {
        const container = document.getElementById('alertsList');
        if (!container) return;
        
        if (this.alerts.length === 0) {
            container.innerHTML = '<div class="text-secondary" style="text-align: center; padding: 2rem;">No alerts to display</div>';
            return;
        }

        container.innerHTML = this.alerts.map(alert => `
            <div class="alert-item">
                <div class="alert-icon">⚠️</div>
                <div class="alert-content">
                    <div class="alert-title">${alert.title}</div>
                    <div class="alert-description">${alert.description}</div>
                    <div class="alert-time">${this.formatTime(alert.timestamp)}</div>
                </div>
            </div>
        `).join('');
    }

    saveConfiguration() {
        const refreshIntervalEl = document.getElementById('refreshInterval');
        const alertThresholdEl = document.getElementById('alertThreshold');
        const batchSizeEl = document.getElementById('batchSize');
        const autoProcessingEl = document.getElementById('autoProcessing');
        const realTimeAlertsEl = document.getElementById('realTimeAlerts');

        if (refreshIntervalEl) this.config.refreshInterval = parseInt(refreshIntervalEl.value) * 1000;
        if (alertThresholdEl) this.config.alertThreshold = parseInt(alertThresholdEl.value);
        if (batchSizeEl) this.config.batchSize = parseInt(batchSizeEl.value);
        if (autoProcessingEl) this.config.autoProcessing = autoProcessingEl.checked;
        if (realTimeAlertsEl) this.config.realTimeAlerts = realTimeAlertsEl.checked;

        this.showNotification('Configuration saved successfully!', 'success');
        
        // Restart auto-refresh with new interval
        this.startAutoRefresh();
    }

    clearAlerts() {
        this.alerts = [];
        this.updateAlertsTab();
        this.closeAlert();
        this.showNotification('All alerts cleared', 'info');
    }

    showNotification(message, type = 'info') {
        // Create a simple notification
        const notification = document.createElement('div');
        notification.className = `status status--${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 1000;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideInRight 0.3s ease-out;
            max-width: 300px;
        `;
        notification.innerHTML = `<span class="status__indicator"></span>${message}`;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in forwards';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(() => {
            if (this.config.autoProcessing) {
                // Simulate occasional new messages
                if (Math.random() < 0.15) { // 15% chance every refresh
                    this.simulateRandomEmail();
                }
                this.updateDashboard();
            }
        }, this.config.refreshInterval);
    }
}

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing Sentiment Watchdog...');
    window.sentimentWatchdog = new SentimentWatchdog();
});

// Add CSS animations via JavaScript
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);