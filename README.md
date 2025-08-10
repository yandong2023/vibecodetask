# VibeCodeTask - Real-time Version

[中文版](README_zh.md)

## Overview

VibeCodeTask is an intelligent task automation platform powered by Claude Code CLI. It provides real-time token monitoring and automated task execution with scheduling capabilities.

## Features

### 🌍 Internationalization
- **Multi-language Support**: English and Chinese interface
- **Language Switcher**: Easy toggle between languages
- **Automatic Detection**: Default English with persistent language preference

### 💰 Real-time Token Monitoring
- **Live Usage Tracking**: Real-time token consumption monitoring
- **Cost Analysis**: Detailed cost breakdown and projections
- **Usage Statistics**: Daily, weekly, and monthly usage trends
- **Smart Alerts**: Notifications for high usage and budget limits

### 🚀 Task Automation
- **Immediate Execution**: Run tasks instantly
- **Scheduled Tasks**: Set specific execution times
- **Smart Scheduling**: AI-powered optimal timing
- **Queue Management**: Task priority and dependency handling

### 📊 Analytics & History
- **Usage Trends**: Visual charts and graphs
- **Historical Data**: 7/15/30-day usage analysis  
- **Performance Metrics**: Task completion rates and execution times
- **Export Capabilities**: Data export for reporting

### 🔧 Technical Features
- **Claude Code Integration**: Direct CLI integration for code generation
- **File Management**: Automatic workspace organization
- **Error Handling**: Robust error recovery and logging
- **Responsive Design**: Mobile-friendly interface

## Quick Start

### Prerequisites
- Python 3.7+ with required packages
- Claude Code CLI installed and configured
- Modern web browser

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/vibecodetask.git
   cd vibecodetask
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Claude Code**
   ```bash
   claude --configure
   # Follow prompts to set up API keys
   ```

4. **Start the Server**
   ```bash
   python realtime_server.py
   ```

5. **Access the Interface**
   Open `http://localhost:8080` in your browser

## Usage Guide

### Creating Tasks

1. **Enter Task Description**: Describe what you want Claude to build
   - Example: "Create a snake game with HTML+JS"
   - Example: "Build a data analysis script in Python"

2. **Choose Execution Type**:
   - **Immediate**: Execute right away
   - **Scheduled**: Set a specific time
   - **Smart**: AI-optimized scheduling

3. **Monitor Progress**: Track task status in real-time

### Language Switching

Click the language switcher in the top-right corner to toggle between English and Chinese. Your preference is automatically saved.

### Token Management

- Monitor real-time usage in the dashboard
- Set up alerts for budget management
- Analyze historical patterns
- Export usage data for accounting

## API Endpoints

### Task Management
- `POST /api/add-task` - Create new task
- `GET /api/tasks` - List all tasks
- `POST /api/execute-task` - Execute specific task
- `POST /api/delete-task` - Delete task

### Monitoring
- `GET /api/token-status` - Current token usage
- `GET /api/history/{days}` - Historical usage data

### Internationalization
- `GET /i18n/en.json` - English translations
- `GET /i18n/zh.json` - Chinese translations

## Configuration

### Environment Variables
```bash
# Server Configuration
VIBE_PORT=8080
VIBE_HOST=localhost

# Claude Configuration
CLAUDE_API_KEY=your_api_key_here

# Workspace
WORKSPACE_DIR=~/vibecodetask-workspace
```

### Language Settings
Language preferences are stored in localStorage and can be configured in `i18n.js`.

## File Structure

```
vibecodetask/
├── realtime_server.py          # Main server
├── realtime_interface.html     # Frontend interface
├── claude_executor.py          # Task execution engine
├── i18n.js                    # Internationalization
├── i18n/
│   ├── en.json               # English translations
│   └── zh.json               # Chinese translations
├── tasks.db                  # Task database
└── README.md                 # This file
```

## Development

### Adding New Languages

1. Create translation file in `i18n/` folder
2. Update available languages in `i18n.js`
3. Add language button to interface

### Extending Features

The system is modular and extensible:
- Add new task types in `claude_executor.py`
- Extend API endpoints in `realtime_server.py`
- Customize UI in `realtime_interface.html`

## Troubleshooting

### Common Issues

**Claude CLI Not Found**
```bash
# Install Claude Code
npm install -g @anthropics/claude-code
# Or check installation path
which claude
```

**Database Locked**
```bash
# Find and kill blocking processes
ps aux | grep sqlite
kill [process_id]
```

**Connection Issues**
- Check if server is running on correct port
- Verify firewall settings
- Ensure Claude API keys are configured

### Debug Mode

Enable detailed logging:
```bash
export VIBE_DEBUG=true
python realtime_server.py
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add internationalization for new features
4. Test with both languages
5. Submit pull request

## License

MIT License - see LICENSE file for details

## Support

- Issues: [GitHub Issues](https://github.com/your-repo/vibecodetask/issues)
- Documentation: [Wiki](https://github.com/your-repo/vibecodetask/wiki)
- Community: [Discussions](https://github.com/your-repo/vibecodetask/discussions)

---

**Built with ❤️ using Claude Code**