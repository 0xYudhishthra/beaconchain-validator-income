import requests 
import csv
import time
from datetime import datetime
import logging
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import argparse
import json
import random

class Beaconchainfetchr:
    def __init__(self, api_key):
        self.session = requests.Session()
        self.api_key = api_key
        self.last_request_time = 0
        self.rate_limit = 10/60  # 10 requests per minute
        
        # Configure headers with API key
        self.session.headers.update({
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        })
        
        # Retry configuration
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retry))

        # Add duration mapping
        self.DURATION_MAP = {
            '1day': '1d',
            '7days': '7d', 
            '31days': '31d',
            '365days': '365d'
        }

    def fetch_leaderboard(self, pages=17973, per_page=100, duration='365days'):
        base_url = "https://beaconcha.in/api/v1/validator/leaderboard"
        total_income = 0.0
        total_validators_processed = 0
        page = 0
        
        duration_suffix = self.DURATION_MAP.get(duration, '365d')
        performance_field = f'performance{duration_suffix}'
        sort_field = performance_field  
        
        try:
            while page < pages:
                # Rate limiting
                elapsed = time.time() - self.last_request_time
                if elapsed < self.rate_limit:
                    sleep_time = self.rate_limit - elapsed
                    logging.debug(f"Sleeping {sleep_time:.2f}s for rate limit")
                    time.sleep(sleep_time)
                
                params = {
                    'limit': per_page,
                    'offset': page * per_page,
                    'sort': sort_field,  
                    'order': 'desc',
                    'currency': 'ETH'
                }
                
                response = self.session.get(base_url, params=params)
                self.last_request_time = time.time()
                
                # Add response validation
                if response.status_code != 200:
                    logging.error(f"API request failed: {response.status_code} - {response.text}")
                    raise ValueError(f"API returned {response.status_code}")
                
                # Add full response debugging
                logging.debug(f"Full API response: {json.dumps(response.json(), indent=2)}")
                
                # Handle rate limit errors
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logging.warning(f"Rate limited. Retrying after {retry_after}s")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                
                data = response.json().get('data', [])
                if not data:
                    break
                
                # Debug log to see actual response structure
                logging.debug(f"Sample validator data: {json.dumps(data[0], indent=2)}")
                
                if data:
                    first_validator = data[0]
                    logging.debug(f"First validator keys: {list(first_validator.keys())}")
                    logging.debug(f"Income fields: 1y={first_validator.get('performance365d')} | 1year={first_validator.get('performance1y')}")
                    logging.debug(f"Full validator data: {json.dumps(first_validator, indent=2)}")
                
                # Accumulate income using dynamic field
                for validator in data:
                    performance_gwei = validator.get(performance_field, 0)
                    income_eth = float(performance_gwei) / 10**9 if performance_gwei else 0.0
                    total_income += income_eth
                    total_validators_processed += 1
                
                page += 1
                logging.info(f"Processed page {page}/{pages} ({total_validators_processed} validators)")

            if total_validators_processed == 0:
                return 0.0
            
            average_income = total_income / total_validators_processed
            logging.info(f"Average {duration} income: {average_income:.6f} ETH (based on {total_validators_processed} validators)")
            return average_income

        except KeyboardInterrupt:
            logging.info("\nInterrupted by user. Returning partial results...")
            if total_validators_processed > 0:
                average_income = total_income / total_validators_processed
                logging.info(f"Partial {duration} income: {average_income:.6f} ETH (based on {total_validators_processed} validators)")
                return average_income
            return 0.0
        except Exception as e:
            logging.error(f"Scraping failed: {str(e)}")
            raise

    def fetch_random_sample(self, sample_size=1000, per_page=100, duration='365days'):
        base_url = "https://beaconcha.in/api/v1/validator/leaderboard"
        total_validators = 1797225
        total_income = 0.0
        sampled = 0
        
        # Get duration parameters
        duration_suffix = self.DURATION_MAP.get(duration, '365d')
        performance_field = f'performance{duration_suffix}'
        sort_field = performance_field
        
        # Generate unique random pages with caching
        unique_pages = set()
        random_indices = random.sample(range(total_validators), sample_size)
        for idx in random_indices:
            unique_pages.add(idx // per_page)
        
        try:
            # Process pages in random order
            for page in random.sample(sorted(unique_pages), len(unique_pages)):
                # Rate limiting
                elapsed = time.time() - self.last_request_time
                if elapsed < self.rate_limit:
                    time.sleep(self.rate_limit - elapsed)
                
                params = {
                    'limit': per_page,
                    'offset': page * per_page,
                    'sort': sort_field,  # Dynamic sort field
                    'order': 'desc',
                    'currency': 'ETH'
                }
                
                response = self.session.get(base_url, params=params)
                self.last_request_time = time.time()
                response.raise_for_status()
                
                data = response.json().get('data', [])
                if not data:
                    continue
                
                # Get all validators from this page that are in our sample
                page_start = page * per_page
                page_indices = [i - page_start for i in random_indices 
                              if page_start <= i < page_start + per_page]
                
                for pos in page_indices:
                    if pos < len(data):
                        performance_gwei = data[pos].get(performance_field, 0)
                        total_income += float(performance_gwei) / 10**9
                        sampled += 1
                
                logging.info(f"Sampled {sampled}/{sample_size} validators")
                if sampled >= sample_size:
                    break

            return total_income / sampled if sampled else 0.0

        except KeyboardInterrupt:
            logging.info("\nInterrupted by user. Returning partial sample...")
            if sampled > 0:
                average_income = total_income / sampled
                logging.info(f"Partial {duration} income: {average_income:.6f} ETH (based on {sampled} validators)")
                return average_income
            return 0.0
        except Exception as e:
            logging.error(f"Random sampling failed: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Beaconcha.in Validator Income fetchr')
    parser.add_argument('--api-key', required=True, help='Beaconcha.in API key')
    parser.add_argument('--pages', type=int, default=17973, 
                      help='Number of pages to fetch (default: all 17973)')
    parser.add_argument('--per-page', type=int, default=100,
                      help='Items per page (default: 100)')
    parser.add_argument('--output', type=str,
                      help='Output file to save average income')
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'], 
                      default='info', help='Set logging verbosity level')
    parser.add_argument('--sample-size', type=int,
                      help='Number of validators to sample randomly')
    parser.add_argument('--duration', choices=['1day', '7days', '31days', '365days'],
                      default='365days', help='Time period for income calculation')

    args = parser.parse_args()
    
    # Configure logging level
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=args.log_level.upper()
    )

    fetchr = Beaconchainfetchr(args.api_key)
    try:
        if args.sample_size:
            avg_income = fetchr.fetch_random_sample(
                sample_size=args.sample_size,
                per_page=args.per_page,
                duration=args.duration
            )
        else:
            avg_income = fetchr.fetch_leaderboard(
                pages=args.pages,
                per_page=args.per_page,
                duration=args.duration
            )
        result = f"Average {args.duration} income: {avg_income:.6f} ETH"
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"Results saved to {args.output}")
        else:
            print(result)
            
    except KeyboardInterrupt:
        logging.info("Interrupt received. Calculating partial results...")
        if fetchr.current_total_validators > 0:
            avg_income = fetchr.current_total_income / fetchr.current_total_validators
            result = f"Partial average {args.duration} income: {avg_income:.6f} ETH (based on {fetchr.current_total_validators} validators)"
        else:
            result = "No validators processed yet."
        print(result)
    except Exception as e:
        logging.error(f"CLI execution failed: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()


