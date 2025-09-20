# 📊 US Economic Analysis Dashboard

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.46.1-red.svg)
![Plotly](https://img.shields.io/badge/Plotly-6.2.0-purple.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.3.1-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Open Source](https://img.shields.io/badge/Open%20Source-Yes-brightgreen.svg)

*A comprehensive economic data visualization and analysis platform powered by FRED API and Streamlit*

</div>

---

## 📌 Introduction

The **US Economic Analysis Dashboard** is a powerful, interactive web application that provides real-time economic insights through beautiful visualizations and comprehensive data analysis. Built with modern Python technologies, this dashboard leverages the Federal Reserve Economic Data (FRED) API to deliver up-to-date economic indicators, unemployment rates, labor force participation data, and S&P 500 market trends.

Whether you're an economist, researcher, student, or data enthusiast, this dashboard offers an intuitive interface to explore complex economic data through interactive charts, state-by-state comparisons, and AI-powered economic insights.

## 🚀 Features

### 📈 **Comprehensive Economic Data**
- **S&P 500 Analysis** - Historical trends with moving averages and comparison tools
- **Unemployment Tracking** - State-by-state unemployment rates with seasonal adjustments
- **Labor Force Participation** - Detailed participation rate analysis across all US states
- **Interactive Visualizations** - Dynamic charts with hover details and trend analysis

### 🗺️ **Advanced Analytics**
- **State Comparison Tools** - Side-by-side economic indicator comparisons
- **Custom Date Ranges** - Flexible time period selection (2010-present)
- **Export Capabilities** - Download data as CSV, Excel, or PNG formats
- **Real-time Data** - Live updates from FRED API with intelligent caching

### 🤖 **AI-Powered Insights**
- **Economic Chatbot** - Interactive AI assistant for economic questions
- **World Bank Integration** - Global economic data access
- **Smart Data Interpretation** - Automated insights and trend analysis

### 📊 **User Experience**
- **Dark Theme UI** - Modern, professional interface design
- **Responsive Layout** - Optimized for desktop and mobile viewing
- **CSV Upload** - Custom data visualization capabilities
- **Performance Optimized** - Fast loading with intelligent caching

## 🛠️ Tech Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Frontend** | Streamlit | 1.46.1 | Web application framework |
| **Visualization** | Plotly | 6.2.0 | Interactive charts and graphs |
| **Data Processing** | Pandas | 2.3.1 | Data manipulation and analysis |
| **Data Source** | FRED API | Latest | Economic data retrieval |
| **AI/ML** | Google Gemini | 2.0-flash | Economic chatbot |
| **Export** | Kaleido | 1.0.0 | Chart image generation |
| **Styling** | Custom CSS | - | Dark theme UI design |

### Additional Dependencies
- **Matplotlib** - Statistical plotting
- **NumPy** - Numerical computations
- **Requests** - API communication
- **OpenPyXL** - Excel file handling
- **TheFuzz** - Fuzzy string matching

## ⚙️ Installation

### Prerequisites
- Python 3.8 or higher
- FRED API key (free registration at [fred.stlouisfed.org](https://fred.stlouisfed.org))
- Optional: Google Gemini API key for chatbot features

### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/us-economic-dashboard.git
   cd us-economic-dashboard
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   FRED_API_KEY=your_fred_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here  # Optional
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Access the dashboard**
   Open your browser and navigate to `http://localhost:8501`

## 📖 Usage

### Getting Started
1. **Launch the Application** - Run `streamlit run app.py` and open the provided URL
2. **Select Your View** - Choose from the sidebar navigation:
   - S&P 500 Index analysis
   - Unemployment rate tracking
   - Labor force participation rates
   - State-by-state comparisons
   - Custom CSV upload
   - AI Economic Chatbot

### Key Features Usage

#### 📊 **S&P 500 Analysis**
- Select date ranges and chart types
- Add moving averages (30-day, 90-day)
- Compare with other indicators (CPI, Unemployment)
- Export data in multiple formats

#### 🗺️ **State Economic Data**
- Filter by specific states or view all states
- Toggle between unemployment and participation rates
- Use interactive legends to show/hide specific states
- Download filtered datasets

#### 🤖 **Economic Chatbot**
- Ask questions about global economics
- Query specific country data (GDP, inflation, etc.)
- Get AI-powered economic insights
- Access World Bank data through natural language

#### 📂 **Custom Data Upload**
- Upload your own CSV files
- Create custom visualizations
- Export charts as PNG images
- Analyze any time-series data

## 🤝 Contributing

We welcome contributions to improve the US Economic Analysis Dashboard! Here's how you can help:

### How to Contribute
1. **Fork the repository** on GitHub
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** and test thoroughly
4. **Commit your changes** (`git commit -m 'Add amazing feature'`)
5. **Push to the branch** (`git push origin feature/amazing-feature`)
6. **Open a Pull Request** with a detailed description

### Areas for Contribution
- 🐛 **Bug Fixes** - Report and fix issues
- ✨ **New Features** - Add new economic indicators or visualizations
- 📊 **Data Sources** - Integrate additional data APIs
- 🎨 **UI/UX** - Improve the user interface and experience
- 📚 **Documentation** - Enhance guides and examples
- 🧪 **Testing** - Add unit tests and improve reliability

### Development Guidelines
- Follow PEP 8 Python style guidelines
- Add docstrings to new functions
- Test your changes thoroughly
- Update documentation as needed
- Ensure compatibility with existing features

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 US Economic Analysis Dashboard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## ⭐ Support

### Getting Help
- 📖 **Documentation** - Check this README and inline code comments
- 🐛 **Issues** - Report bugs on the [GitHub Issues](https://github.com/KahafSameer/us-economic-dashboard/issues) page
- 💬 **Discussions** - Join community discussions for questions and ideas
- 📧 **Contact** - Reach out to the maintainers for direct support

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **FRED API Key Error** | Ensure your API key is correctly set in the `.env` file |
| **Missing Dependencies** | Run `pip install -r requirements.txt` to install all packages |
| **Port Already in Use** | Use `streamlit run app.py --server.port 8502` to specify a different port |
| **Slow Loading** | The app caches data for performance; first load may be slower |
| **Chart Not Displaying** | Check your internet connection for FRED API access |

### Performance Tips
- Use the sidebar filters to limit data ranges for faster loading
- Enable browser caching for better performance
- Close unused browser tabs to free up memory
- Use the export features to save data locally for offline analysis

---

<div align="center">

**Built with ❤️ for the economic data community**

[⭐ Star this repo](https://github.com/kahafsameer/us-economic-dashboard) • [🐛 Report Bug](https://github.com/kahafsameer/us-economic-dashboard/issues) • [💡 Request Feature](https://github.com/kahafsameer/us-economic-dashboard/issues)

</div>
