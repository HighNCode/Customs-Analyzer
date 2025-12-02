# test_llm.py - Run this to test if LLM streaming works
import sys
sys.path.append('.')

from llm import stream_llm_analysis, ANALYSIS_MODEL
import time

print(f"🧪 Testing LLM Streaming")
print(f"📱 Model: {ANALYSIS_MODEL}")
print("="*60)

test_prompt = """Analyze this simple data:

Total Records: 2764
Columns: GD_NO_Complete, Declared Unit PRICE, ASSD UNIT PRICE

Provide a brief analysis with:
📊 KEY COUNTS
📈 PATTERNS OBSERVED
💡 RECOMMENDATIONS

Keep it under 10 lines."""

print("\n🔄 Starting stream...\n")

token_count = 0
start_time = time.time()

try:
    for token in stream_llm_analysis(test_prompt):
        token_count += 1
        print(token, end='', flush=True)
    
    elapsed = time.time() - start_time
    
    print(f"\n\n{'='*60}")
    print(f"✅ Success!")
    print(f"📊 Tokens received: {token_count}")
    print(f"⏱️  Time elapsed: {elapsed:.2f}s")
    
    if token_count == 0:
        print("\n❌ WARNING: No tokens received!")
        print("Possible issues:")
        print("1. API key invalid")
        print("2. Model not available")
        print("3. Content filtering")
        
except Exception as e:
    print(f"\n\n❌ Error: {e}")
    print("Check your OPENAI_API_KEY in .env file")