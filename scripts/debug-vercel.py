#!/usr/bin/env python3
"""
Automated Vercel debugging script for Tilts platform.
Uses Vercel CLI and API endpoints to diagnose common issues.
"""

import subprocess
import json
import requests
import sys
import time
from datetime import datetime
import os

class VercelDebugger:
    def __init__(self):
        self.deployment_url = None
        self.issues = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_command(self, cmd):
        """Execute command and return output."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return None, str(e), 1
    
    def check_vercel_cli(self):
        """Verify Vercel CLI is installed and authenticated."""
        print("🔍 Checking Vercel CLI...")
        stdout, stderr, code = self.run_command("vercel --version")
        if code != 0:
            self.issues.append("Vercel CLI not installed. Run: npm i -g vercel")
            return False
        
        stdout, stderr, code = self.run_command("vercel whoami")
        if code != 0:
            self.issues.append("Not authenticated. Run: vercel login")
            return False
        
        print(f"✅ Authenticated as: {stdout.strip()}")
        return True
    
    def get_latest_deployment(self):
        """Get the latest deployment URL."""
        print("\n🔍 Getting latest deployment...")
        stdout, stderr, code = self.run_command("vercel list --json --count 1")
        if code == 0:
            try:
                deployments = json.loads(stdout)
                if deployments and len(deployments) > 0:
                    self.deployment_url = deployments[0]['url']
                    print(f"✅ Latest deployment: {self.deployment_url}")
                    return True
            except:
                pass
        
        self.issues.append("Could not get latest deployment")
        return False
    
    def check_environment_variables(self):
        """Verify all required environment variables are set."""
        print("\n🔍 Checking environment variables...")
        required_vars = [
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY'
        ]
        
        stdout, stderr, code = self.run_command("vercel env list")
        if code == 0:
            for var in required_vars:
                if var in stdout:
                    print(f"✅ {var}: Set")
                else:
                    self.issues.append(f"Missing env var: {var}")
                    print(f"❌ {var}: Missing")
    
    def test_endpoints(self):
        """Test all API endpoints."""
        print("\n🔍 Testing API endpoints...")
        
        if not self.deployment_url:
            print("❌ No deployment URL available")
            return
        
        endpoints = [
            ('/health', 'GET', None),
            ('/api/models', 'GET', None),
            ('/api/benchmark/models', 'GET', None),
            ('/api/leaderboard', 'GET', None),
            ('/api/sessions', 'GET', None),
        ]
        
        for path, method, data in endpoints:
            url = f"https://{self.deployment_url}{path}"
            try:
                if method == 'GET':
                    response = requests.get(url, timeout=10)
                else:
                    response = requests.post(url, json=data, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ {method} {path}: {response.status_code}")
                else:
                    print(f"❌ {method} {path}: {response.status_code}")
                    self.issues.append(f"{method} {path} returned {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {method} {path}: {str(e)}")
                self.issues.append(f"{method} {path} failed: {str(e)}")
    
    def check_recent_logs(self):
        """Check recent function logs for errors."""
        print("\n🔍 Checking recent logs for errors...")
        stdout, stderr, code = self.run_command("vercel logs --since 1h --search ERROR")
        
        if code == 0 and stdout:
            error_count = len(stdout.strip().split('\n'))
            if error_count > 0:
                print(f"⚠️  Found {error_count} errors in the last hour")
                self.issues.append(f"Found {error_count} errors in logs")
                
                # Save error logs
                with open(f"debug_errors_{self.timestamp}.log", "w") as f:
                    f.write(stdout)
                print(f"   Saved to: debug_errors_{self.timestamp}.log")
        else:
            print("✅ No errors found in recent logs")
    
    def check_function_performance(self):
        """Check function execution times."""
        print("\n🔍 Checking function performance...")
        
        # Get function list
        stdout, stderr, code = self.run_command("vercel functions list")
        if code == 0:
            # Parse function names and check each
            functions = []
            for line in stdout.strip().split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if parts:
                        functions.append(parts[0])
            
            for func in functions[:5]:  # Check top 5 functions
                stdout, stderr, code = self.run_command(f"vercel logs {func} --since 1h")
                if code == 0 and stdout:
                    # Look for timeout patterns
                    if "Task timed out" in stdout or "FUNCTION_INVOCATION_TIMEOUT" in stdout:
                        self.issues.append(f"Function {func} has timeout issues")
                        print(f"⚠️  {func}: Timeout issues detected")
                    else:
                        print(f"✅ {func}: No timeout issues")
    
    def test_ai_integration(self):
        """Test AI model integration."""
        print("\n🔍 Testing AI integration...")
        
        if not self.deployment_url:
            return
        
        # Test OpenAI
        test_payload = {
            "game": "minesweeper",
            "provider": "openai",
            "model": "gpt-4",
            "difficulty": "easy",
            "num_games": 1,
            "test_mode": True
        }
        
        url = f"https://{self.deployment_url}/api/benchmark/run"
        try:
            response = requests.post(url, json=test_payload, timeout=30)
            if response.status_code == 200:
                print("✅ OpenAI integration working")
            else:
                print(f"❌ OpenAI integration failed: {response.status_code}")
                self.issues.append(f"OpenAI integration returned {response.status_code}")
        except Exception as e:
            print(f"❌ OpenAI integration error: {str(e)}")
            self.issues.append(f"OpenAI integration error: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive debug report."""
        print("\n📋 Generating debug report...")
        
        report = f"""
=== Vercel Debug Report ===
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Deployment: {self.deployment_url or 'Unknown'}

Issues Found: {len(self.issues)}
{'='*50}
"""
        
        if self.issues:
            report += "\n🚨 Issues:\n"
            for i, issue in enumerate(self.issues, 1):
                report += f"{i}. {issue}\n"
        else:
            report += "\n✅ No issues found!\n"
        
        report += "\n" + "="*50 + "\n"
        
        # Save report
        report_file = f"debug_report_{self.timestamp}.txt"
        with open(report_file, "w") as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Report saved to: {report_file}")
        
        return len(self.issues) == 0
    
    def run_full_diagnostic(self):
        """Run complete diagnostic suite."""
        print("🚀 Starting Vercel diagnostic for Tilts platform...\n")
        
        # Run all checks
        if not self.check_vercel_cli():
            print("\n❌ Cannot continue without Vercel CLI")
            return False
        
        self.get_latest_deployment()
        self.check_environment_variables()
        self.test_endpoints()
        self.check_recent_logs()
        self.check_function_performance()
        self.test_ai_integration()
        
        # Generate report
        success = self.generate_report()
        
        if success:
            print("\n✅ All diagnostics passed!")
        else:
            print(f"\n⚠️  Found {len(self.issues)} issues that need attention")
        
        return success

def main():
    debugger = VercelDebugger()
    success = debugger.run_full_diagnostic()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()