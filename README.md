# Slack Bot with Buttons Plugin for Dify

**Author:** kaiadachi  
**Version:** 1.0.0  
**Type:** Plugin

## Overview

An enhanced Slack Bot plugin for Dify that builds upon the official slack_bot with three major improvements:

1. **Interactive Button Support** - Automatically converts HTML buttons to native Slack interactive components
2. **Conversation Context Persistence** - Maintains conversation state across messages using thread-based context management
3. **Thread-based Replies** - All responses are properly threaded for better conversation organization

This plugin enables rich, interactive conversational experiences between Slack and Dify applications (Chatflow/Chatbot/Agent).
<img width="1063" alt="スクリーンショット 2025-07-02 22 45 58" src="https://github.com/user-attachments/assets/c1824e1e-e641-4c96-8434-31e7e0c853a3" />


## Features

- 🤖 Receive and process Slack messages in Dify
- 💬 Send formatted responses back to Slack
- 🔘 Automatic conversion of HTML buttons to Slack Block Kit buttons
- 🔄 Handle button interactions seamlessly
- 🛡️ Secure request verification
- 🌐 Multi-language support (EN, JA, ZH, PT)

## Installation

### Method 1: Install from GitHub Repository (Recommended)

1. In your Dify instance, go to **Plugin Management**
2. Click **Install Plugin** → **Via GitHub**
3. Enter the repository URL: `https://github.com/kaiadachi/slack-bot-with-buttons-plugin`
4. Click **Install**

### Method 2: Install via Local File

1. Download the latest `.difypkg` file from the [Releases](https://github.com/kaiadachi/slack-bot-with-buttons-plugin/releases) page
2. In Dify Plugin Management, click **Install Plugin** → **Via Local File**
3. Upload the `.difypkg` file or drag and drop it

## Setup Guide

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App**
3. Choose **From scratch**
4. Enter your app name (e.g., "Dify Bot with Buttons")
5. Select your target workspace
6. Click **Create App**

### 2. Configure OAuth & Permissions

1. Navigate to **OAuth & Permissions** in the left sidebar
2. Scroll down to **Scopes** → **Bot Token Scopes**
3. Add the following Bot Token Scopes:
   - `app_mentions:read` - Read @mention events directed at the bot
   - `chat:write` - Send messages as the bot
   - `channels:history` - View messages in public channels
   - `groups:history` - View messages in private channels
   - `im:history` - View messages in direct messages
   - `mpim:history` - View messages in group direct messages
4. Click **Install to Workspace** (or **Reinstall to Workspace** if updating)
5. Authorize the app in your workspace
6. Copy the **Bot User OAuth Token** (starts with `xoxb-`) - you'll need this for Dify

### 3. Set Up Dify Endpoint

1. In your Dify workspace, go to **Plugin Management**
2. Find the **Slack Bot with Buttons** plugin
3. Click **Settings** or **Configure**
4. Create a new endpoint:
   - **Endpoint Name**: Choose a descriptive name (e.g., "Slack Bot Endpoint")
   - **Bot Token**: Paste your Bot User OAuth Token from step 2
   - **Allow Retry**: Set to `false` (recommended to prevent duplicate messages)
5. **Link to Application**: Select your Dify chatflow/chatbot/agent
6. Click **Save**
7. **Copy the generated endpoint URL** - you'll need this for Slack configuration

### 4. Configure Slack Event Subscriptions

1. Return to your Slack app settings at [api.slack.com/apps](https://api.slack.com/apps)
2. Go to **Event Subscriptions** in the left sidebar
3. Toggle **Enable Events** to ON
4. **Request URL**: Paste the Dify endpoint URL from step 3
   - Slack will verify the URL (you should see a green checkmark)
5. Scroll down to **Subscribe to bot events**
6. Add the following bot events:
   - `app_mention` - When someone mentions your bot with @
7. Click **Save Changes**

**Note**: The bot will only respond to @mentions, not all messages in channels.

### 5. Enable Interactivity (CRITICAL for Button Support)

⚠️ **This step is MANDATORY for button functionality**

1. Go to **Interactivity & Shortcuts** in the left sidebar
2. Toggle **Interactivity** to ON
3. **Request URL**: Use the **exact same Dify endpoint URL** from step 3
   - This must be identical to the Event Subscriptions URL
   - Slack will verify this URL as well
4. Click **Save Changes**

**Critical**: Without this configuration, HTML buttons in Dify responses will display as raw HTML text instead of interactive Slack buttons.

### 6. Final Steps

1. **Reinstall App** (if prompted):
   - Go back to **OAuth & Permissions**
   - Click **Reinstall to Workspace** if you see this option
   - Authorize any new permissions

2. **Add Bot to Channel**:
   - Go to your desired Slack channel
   - Type `/invite @your-bot-name` (replace with your actual bot name)
   - Or go to channel settings → Integrations → Add apps

3. **Test the Bot**:
   - In the channel, type `@your-bot-name hello` to mention the bot
   - The bot should respond through your Dify application
   - Test button functionality by having your Dify app return HTML buttons

## Usage Examples

### Basic Conversation
```
User: @bot What can you help me with?
Bot: I can assist you with various tasks. What would you like help with?
```

### Interactive Buttons

#### How to Create Buttons in Dify

In your Dify app (Chatflow/Chatbot/Agent), include HTML button tags in your responses with the following format:

```html
<button data-message="value_to_send">Display Text</button>
```

**Important**: 
- `data-message` attribute: The value that will be sent to Dify when clicked
- Button text: What users see in Slack

#### Example Implementation

```html
<!-- Dify Response -->
Please select an option:
<button data-message="billing inquiry">Billing Questions</button>
<button data-message="technical support">Technical Support</button>
<button data-message="general info">General Information</button>
```

When displayed in Slack:
- Users see buttons labeled: "Billing Questions", "Technical Support", "General Information"
- When clicked, Dify receives: "billing inquiry", "technical support", or "general info"

#### Best Practices

1. **Use meaningful data-message values** that your Dify workflow can process:
   ```html
   <button data-message="action:billing">料金について</button>
   <button data-message="action:support">サポート</button>
   ```

2. **Mix buttons with regular text**:
   ```html
   I can help you with the following:
   <button data-message="new_ticket">Create Ticket</button>
   <button data-message="check_status">Check Status</button>
   Or type your question directly.
   ```

### Real-World Example
```
User: "I need help"
Bot: "What type of help do you need?"
     [Billing] [Technical] [Account]
User: *clicks Technical*
Bot: "I'll connect you with technical support. What's your issue?"
```

## Technical Details

### Key Improvements over Official Plugin

1. **Button Conversion**
   - Automatically detects `<button data-message="...">Text</button>` in Dify responses
   - Converts to Slack Block Kit interactive buttons
   - Supports multiple buttons per message
   - Handles complex HTML mixed with buttons

2. **Conversation Context Management**
   - Uses thread timestamp as conversation identifier
   - Maintains Dify conversation_id across thread messages
   - 24-hour TTL cache for active conversations
   - Enables stateful multi-turn conversations

3. **Thread Organization**
   - All bot responses use thread_ts for proper threading
   - Button clicks maintain thread context
   - User mentions preserved in button responses

### Security
- Verifies all Slack requests
- Secure token storage
- HTTPS-only communication
- No permanent message storage

## Development

### Local Development Setup

1. Clone the repository
```bash
git clone https://github.com/kaiadachi/slack-bot-with-buttons-plugin.git
cd slack-bot-with-buttons-plugin
```

2. Set up Python environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment
```bash
cp .env.example .env
# Edit .env with your development settings
```

4. Install Dify plugin development tools
```bash
pip install dify-plugin
```

5. Debug the plugin
```bash
dify plugin run
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Privacy

See [PRIVACY_POLICY.md](PRIVACY_POLICY.md) for information on how this plugin handles data.

## Support

- Report issues on [GitHub Issues](https://github.com/kaiadachi/slack-bot-with-buttons-plugin/issues)
- For Dify-specific questions, visit [Dify Documentation](https://docs.dify.ai)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for [Dify](https://dify.ai) plugin ecosystem
- Based on the [official slack_bot plugin](https://github.com/langgenius/dify-official-plugins/tree/main/extensions/slack_bot) with enhanced features
- Uses Slack Block Kit for interactive components
- Inspired by the need for stateful, interactive Slack-Dify conversations
