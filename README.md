# Beaconchain Validator Income Analyzer

A simple tool for collecting and analyzing Ethereum validator income data from Beaconcha.in's API across multiple time frames.

## Project Description

This tool helps researchers and validators:

- Calculate average validator earnings for 1d/7d/31d/365d periods
- Analyze income distribution across 1.7M+ validators
- Perform full dataset analysis or statistical sampling
- Handle API rate limits and resume interrupted operations

Key technical features:
⌛ Adjustable time frames (1 day to 1 year)
📊 Full dataset processing or random sampling
⚡ Rate limiting with exponential backoff
🛑 Graceful interruption handling (saves partial results)
📁 Configurable output formatting and file saving

## Installation

```bash
# Install dependencies only
pip install -r requirements.txt
```

## Basic Usage

```bash
# Full analysis (1 year default)
python3 beaconchain_scraper.py --api-key YOUR_API_KEY

# 7-day analysis with sampling
python3 beaconchain_scraper.py --api-key YOUR_KEY --duration 7days --sample-size 5000

# Save results to file
python3 beaconchain_scraper.py --api-key YOUR_KEY --output earnings.txt
```

## Advanced Options

```bash
# Custom time frames
--duration [1day|7days|31days|365days]

# Data collection modes
--pages 1000        # Limit to first 1000 pages (100k validators)
--sample-size 5000  # Random sample of 5000 validators

# Output control
--log-level debug   # Show detailed processing information
--output results.txt # Save results to file
```

## Configuration Tips

1. Get API key from [Beaconcha.in](https://beaconcha.in/api)
2. For full analysis (~1.7M validators):
   - Expect 4-6 hours runtime
   - Use `nohup` for background processing
3. For quick estimates:
   - Use `--sample-size 10000` for 1% sample
   - Combine with `--duration 7days` for weekly analysis

Example output:

```
Average 7days income: 0.014159 ETH (based on 10000 validators)
Results saved to weekly_earnings.txt
```

## License

MIT Licensed - See LICENSE file for details
