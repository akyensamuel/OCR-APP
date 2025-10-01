"""Quick test to check if Poppler is accessible from Python"""
import subprocess
import sys

print("Testing Poppler accessibility from Python...")
print("-" * 50)

try:
    # Try with shell=True (uses system PATH)
    result = subprocess.run(
        ['pdftoppm', '-v'], 
        capture_output=True, 
        text=True,
        shell=True,
        timeout=5
    )
    
    output = result.stdout + result.stderr
    if output and 'poppler' in output.lower():
        print("✅ SUCCESS: Poppler is accessible!")
        print(f"Output: {output.strip()}")
    else:
        print("⚠️  Command ran but unexpected output:")
        print(f"Output: {output}")
        print(f"Return code: {result.returncode}")
        
except FileNotFoundError:
    print("❌ FAILED: pdftoppm not found")
    print("Poppler is not accessible from Python")
except subprocess.TimeoutExpired:
    print("⚠️  Command timed out")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("-" * 50)
print("\nThis is what Django will see when trying to process PDFs.")
