# Product Launch Planner Chrome Extension

A Chrome extension that helps you scrape and analyze Amazon products for your product launch planning.

## Features

- Scrape product data from Amazon product pages
- Extract detailed product information including:
  - Title, description, and brand
  - Price and ratings
  - Best sellers rank
  - Bullet points and features
  - Category hierarchy
  - Product images
- Save products to your projects
- Analyze products using AI-powered insights
- Generate success recipes based on product analysis

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/product-launch-planner.git
cd product-launch-planner/chrome-extension
```

2. Install dependencies:
```bash
npm install
```

3. Build the extension:
```bash
npm run build
```

4. Load the extension in Chrome:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" in the top right
   - Click "Load unpacked" and select the `chrome-extension` directory

## Usage

1. **Authentication**
   - Click the extension icon in your Chrome toolbar
   - Sign in with your Product Launch Planner account
   - If you don't have an account, create one at [your-website.com](https://your-website.com)

2. **Project Management**
   - Create a new project or select an existing one
   - Each project can contain multiple products for analysis

3. **Product Scraping**
   - Navigate to any Amazon product page
   - Click the extension icon
   - Click "Scrape Product Data"
   - The product data will be automatically saved to your current project

4. **Analysis**
   - View scraped products in your project
   - Run AI analysis on products
   - Generate success recipes based on product insights

## Development

### Project Structure

```
chrome-extension/
├── src/
│   ├── content.js      # Content script for product scraping
│   ├── background.js   # Background script for extension logic
│   ├── popup.html      # Extension popup UI
│   ├── popup.js        # Popup UI logic
│   └── css/
│       ├── tailwind.min.css  # Tailwind CSS framework
│       └── styles.css        # Custom styles
├── manifest.json       # Extension configuration
└── README.md          # Documentation
```

### Building

1. Install dependencies:
```bash
npm install
```

2. Build the extension:
```bash
npm run build
```

3. Watch for changes during development:
```bash
npm run watch
```

### Testing

1. Load the extension in Chrome:
   - Go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `chrome-extension` directory

2. Test the extension:
   - Navigate to an Amazon product page
   - Click the extension icon
   - Verify that product data is scraped correctly
   - Check that data is saved to your project

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -am 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 