#!/usr/bin/env python3
"""
Test AI endpoints to verify model integration is working correctly.
Helps debug issues with OpenAI/Anthropic API calls.
"""

import requests
import json
import os
import time
from datetime import datetime

class AIEndpointTester:
    def __init__(self, base_url=None):
        self.base_url = base_url or self.get_deployment_url()
        self.results = []
        
    def get_deployment_url(self):
        """Get deployment URL from Vercel or use localhost."""
        try:
            import subprocess
            result = subprocess.run(
                ["vercel", "list", "--json", "--count", "1"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data:
                    return f"https://{data[0]['url']}"
        except:
            pass
        
        # Fallback to localhost
        return "http://localhost:3000"
    
    def test_model_list(self):
        """Test model listing endpoints."""
        print("\n🔍 Testing Model List Endpoints...")
        
        endpoints = [
            "/api/models",
            "/api/benchmark/models"
        ]
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            print(f"\nTesting: {url}")
            
            try:
                response = requests.get(url, timeout=10)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Models found: {len(data.get('models', []))}")
                    
                    # Check for each provider
                    providers = {}
                    for model in data.get('models', []):
                        provider = model.get('provider', 'unknown')
                        providers[provider] = providers.get(provider, 0) + 1
                    
                    for provider, count in providers.items():
                        print(f"  - {provider}: {count} models")
                else:
                    print(f"Error: {response.text[:200]}")
                    
            except Exception as e:
                print(f"Exception: {str(e)}")
    
    def test_evaluation(self, provider, model):
        """Test a single evaluation."""
        print(f"\n🧪 Testing {provider}/{model}...")
        
        url = f"{self.base_url}/api/benchmark/run"
        payload = {
            "game": "minesweeper",
            "provider": provider,
            "model": model,
            "difficulty": "easy",
            "num_games": 1
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                url,
                json=payload,
                timeout=60,
                stream=True
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                # Handle streaming response
                events = []
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            try:
                                event = json.loads(line[6:])
                                events.append(event)
                                if event.get('type') == 'move':
                                    print(f"  Move {event.get('moveNumber')}: {event.get('action')}")
                            except:
                                pass
                
                duration = time.time() - start_time
                print(f"✅ Success! Duration: {duration:.2f}s, Moves: {len(events)}")
                
                self.results.append({
                    'provider': provider,
                    'model': model,
                    'status': 'success',
                    'duration': duration,
                    'moves': len(events)
                })
            else:
                error_text = response.text[:500]
                print(f"❌ Error: {error_text}")
                
                self.results.append({
                    'provider': provider,
                    'model': model,
                    'status': 'error',
                    'error': error_text
                })
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            self.results.append({
                'provider': provider,
                'model': model,
                'status': 'exception',
                'error': str(e)
            })
    
    def test_sdk_endpoint(self):
        """Test Vercel AI SDK endpoint."""
        print("\n🔍 Testing SDK Endpoint...")
        
        url = f"{self.base_url}/api/evaluate-sdk"
        payload = {
            "gameType": "minesweeper",
            "provider": "openai",
            "model": "gpt-4",
            "difficulty": "easy",
            "numGames": 1,
            "streaming": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30, stream=True)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                event_count = 0
                for line in response.iter_lines():
                    if line and line.decode('utf-8').startswith('data: '):
                        event_count += 1
                
                print(f"✅ SDK endpoint working! Events: {event_count}")
            else:
                print(f"❌ SDK endpoint error: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ SDK exception: {str(e)}")
    
    def check_api_keys(self):
        """Check if API keys are configured."""
        print("\n🔑 Checking API Keys...")
        
        # Check environment variables
        keys = {
            'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
            'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY', '')
        }
        
        for key_name, key_value in keys.items():
            if key_value:
                masked = key_value[:7] + '...' + key_value[-4:] if len(key_value) > 15 else 'INVALID'
                print(f"✅ {key_name}: {masked}")
            else:
                print(f"❌ {key_name}: Not set")
    
    def run_full_test(self):
        """Run complete test suite."""
        print(f"🚀 AI Endpoint Test Suite")
        print(f"Target: {self.base_url}")
        print("="*50)
        
        # Check API keys
        self.check_api_keys()
        
        # Test model listing
        self.test_model_list()
        
        # Test SDK endpoint
        self.test_sdk_endpoint()
        
        # Test specific models
        test_cases = [
            ("openai", "gpt-4"),
            ("openai", "gpt-3.5-turbo"),
            ("anthropic", "claude-3-opus-20240229"),
            ("anthropic", "claude-3-haiku-20240307")
        ]
        
        print("\n🧪 Testing Individual Models...")
        for provider, model in test_cases:
            self.test_evaluation(provider, model)
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*50)
        print("📊 Test Summary")
        print("="*50)
        
        success_count = sum(1 for r in self.results if r['status'] == 'success')
        error_count = sum(1 for r in self.results if r['status'] == 'error')
        exception_count = sum(1 for r in self.results if r['status'] == 'exception')
        
        print(f"Total tests: {len(self.results)}")
        print(f"✅ Success: {success_count}")
        print(f"❌ Errors: {error_count}")
        print(f"⚠️  Exceptions: {exception_count}")
        
        if error_count > 0 or exception_count > 0:
            print("\n🚨 Failed Tests:")
            for result in self.results:
                if result['status'] != 'success':
                    print(f"  - {result['provider']}/{result['model']}: {result.get('error', 'Unknown error')[:100]}")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"ai_test_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Test AI endpoints')
    parser.add_argument('--url', help='Base URL to test', default=None)
    parser.add_argument('--provider', help='Test specific provider', default=None)
    parser.add_argument('--model', help='Test specific model', default=None)
    
    args = parser.parse_args()
    
    tester = AIEndpointTester(args.url)
    
    if args.provider and args.model:
        # Test specific model
        tester.check_api_keys()
        tester.test_evaluation(args.provider, args.model)
        tester.print_summary()
    else:
        # Run full test suite
        tester.run_full_test()

if __name__ == "__main__":
    main()