# 🔍 DeFi Monitor - Ethereum Suspicious Transaction Detector

A real-time monitoring system that scans Ethereum blocks for suspicious transactions and displays them in an elegant web interface. Perfect for detecting high-value transfers, transactions to flagged addresses, and unusual gas price patterns.

## ✨ Features

- **Real-time Monitoring**: Continuously scans new Ethereum blocks as they're mined
- **Multi-criteria Detection**: Identifies suspicious transactions based on:
  - High ETH value transfers (configurable threshold)
  - Transactions to flagged/blacklisted addresses
  - Abnormally high gas prices
- **Web Dashboard**: Clean, dark-themed interface with live updates
- **Data Persistence**: Automatically saves findings to JSON file
- **Rate Limit Handling**: Intelligent API rate limiting to respect Etherscan limits
- **Live Statistics**: Real-time ETH totals and transaction counts

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Frontend**: Bootstrap 5 + DataTables + Server-Sent Events
- **API**: Etherscan API for blockchain data
- **Storage**: JSON file persistence
- **Threading**: Multi-threaded architecture for continuous monitoring

## 📋 Prerequisites

- Python 3.7+
- Etherscan API key (free at [etherscan.io](https://etherscan.io/apis))
- Internet connection for API calls

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd defiMonitor
   ```

2. **Install dependencies**
   ```bash
   pip install flask requests
   ```

3. **Configure API Key**
   
   Edit `defi-monitor.py` and replace the API key:
   ```python
   ETHERSCAN_API_KEY = 'YOUR_API_KEY_HERE'
   ```

4. **Customize Detection Parameters** (optional)
   ```python
   THRESHOLD_ETHER = 100        # Minimum ETH value to flag
   HIGH_GAS_GWEI = 200         # High gas price threshold
   FLAGGED_ADDRESSES = {       # Addresses to monitor
       '0x1234...',
   }
   ```

## 🏃‍♂️ Usage

1. **Start the application**
   ```bash
   python defi-monitor.py
   ```

2. **Open your browser**
   
   Navigate to `http://localhost:5001`

3. **Monitor transactions**
   
   The dashboard will start displaying suspicious transactions in real-time.

## 🎛️ Configuration

### Detection Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `THRESHOLD_ETHER` | 100 | Minimum ETH value to flag as suspicious |
| `HIGH_GAS_GWEI` | 200 | Gas price threshold in Gwei |
| `POLL_INTERVAL` | 2 | Seconds between block checks |

### Flagged Addresses

Add addresses to monitor in the `FLAGGED_ADDRESSES` set:

```python
FLAGGED_ADDRESSES = {
    '0x0000000000000000000000000000000000000001',
    '0x1234567890123456789012345678901234567890',
    # Add more addresses...
}
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/stream` | GET | Server-sent events stream |
| `/stats` | GET | JSON statistics |
| `/clear` | GET | Clear all stored data |

## 🎨 Dashboard Features

- **🔴 Red rows**: Transactions to flagged addresses
- **🔵 Blue rows**: High-value transactions
- **🟡 Yellow rows**: High gas price transactions
- **⏸️ Pause/▶️ Resume**: Control live updates
- **🔗 Clickable links**: Direct links to Etherscan

## 💾 Data Storage

Transactions are automatically saved to `suspicious_transactions.json` with:
- Periodic saves (every 10 new transactions)
- Timed saves (every 5 minutes)
- Graceful shutdown saves
- Duplicate prevention

## 📈 Performance

- **Rate Limiting**: Respects Etherscan's 2 requests/second limit
- **Memory Efficient**: Processes blocks sequentially
- **Error Handling**: Robust error recovery and logging
- **Thread Safe**: Concurrent monitoring and web serving

## 🚨 Rate Limiting

The application automatically handles Etherscan API rate limits:
- Detects rate limit responses
- Implements appropriate delays
- Logs rate limit encounters
- Continues monitoring seamlessly

## 📝 Logging

Comprehensive logging includes:
- Block processing status
- Transaction detection events
- API errors and rate limits
- Data persistence operations

## 🛡️ Security Considerations

- **API Key**: Keep your Etherscan API key secure
- **Network Access**: Application binds to all interfaces (0.0.0.0)
- **Data Privacy**: Transaction data is stored locally

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. Feel free to use and modify as needed.

## ⚠️ Disclaimer

This tool is for educational and monitoring purposes only. Always verify suspicious activity through official channels. The authors are not responsible for any actions taken based on the information provided by this tool.

## 🆘 Support

If you encounter issues:

1. Check the console logs for error messages
2. Verify your Etherscan API key is valid
3. Ensure you have a stable internet connection
4. Review the rate limiting settings

---

**Happy monitoring! 🚀**