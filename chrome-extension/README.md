# Product Launch Planner Chrome Extension

A Chrome extension for scraping and analyzing Amazon products to help with product launches.

## Features

- 🔐 Secure authentication with JWT
- 📦 Project management (create, select, view)
- 🛍️ Automatic product data scraping from Amazon
- 📊 Real-time product data display
- 🤖 AI-powered product analysis
- 🔄 Persistent session management

## Installation

1. Clone this repository
2. Open Chrome and go to `chrome://extensions/`
3. Enable "Developer mode" in the top right
4. Click "Load unpacked" and select the `chrome-extension` directory

## Development

The extension is built with:
- Manifest V3
- Vanilla JavaScript
- Tailwind CSS for styling
- Chrome Extension APIs

### Project Structure

```
chrome-extension/
├── manifest.json          # Extension configuration
├── src/
│   ├── popup.html        # Popup UI
│   ├── popup.js          # Popup logic
│   ├── content.js        # Content script for scraping
│   ├── background.js     # Background script
│   └── assets/           # Icons and images
└── README.md             # Documentation
```

### API Integration

The extension integrates with the Product Launch Planner backend API:

- Authentication: `/auth/login/json`
- Projects: `/projects`
- Products: `/products`
- Analysis: `/products/project/{project_id}/master-recipe`

## Usage

1. Click the extension icon to open the popup
2. Log in with your credentials
3. Select an existing project or create a new one
4. Browse Amazon product pages
5. The extension will automatically scrape product data
6. Once 10 products are collected, click "Analyze Products"
7. View the analysis results in the admin panel

## Security

- JWT tokens are securely stored in `chrome.storage.local`
- All API requests include proper authentication headers
- Sensitive data is never stored in plain text

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details 