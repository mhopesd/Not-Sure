import pyaudio
import os
from google import genai

# 1. DEBUG AUDIO DEVICES
print("\n" + "="*40)
print("🎧 AUDIO DEVICE DIAGNOSTIC")
print("="*40)
p = pyaudio.PyAudio()
found_blackhole = False

print(f"Total Devices Detected: {p.get_device_count()}\n")

for i in range(p.get_device_count()):
    try:
        info = p.get_device_info_by_index(i)
        name = info.get('name')
        inputs = info.get('maxInputChannels')
        
        # Mark BlackHole if found
        is_bh = "blackhole" in name.lower()
        if is_bh: found_blackhole = True
        
        marker = "✅" if is_bh else "  "
        print(f"{marker} [{i}] {name} (Inputs: {inputs})")
    except Exception as e:
        print(f"   [{i}] Error reading device: {e}")

p.terminate()

if not found_blackhole:
    print("\n❌ BlackHole NOT detected by Python.")
    print("   Fix: Open 'System Settings > Privacy & Security > Microphone'.")
    print("   Ensure 'Terminal' or 'VS Code' has access.")
else:
    print("\n✅ BlackHole is VISIBLE to Python.")

# 2. DEBUG GEMINI API
print("\n" + "="*40)
print("✨ GEMINI API DIAGNOSTIC")
print("="*40)

# Replace this if your env var isn't set, or ensure config.ini is read
# We will try to grab the key from your existing config logic or env var
api_key = os.environ.get("GEMINI_API_KEY")

# If not in env, let's look for the config file in the current folder
if not api_key:
    import configparser
    config = configparser.ConfigParser()
    if os.path.exists("audio_config.ini"):
        config.read("audio_config.ini")
        api_key = config['API_KEYS'].get('gemini')

if not api_key:
    print("❌ No API Key found in Environment or audio_config.ini")
else:
    print(f"🔑 Key found: {api_key[:5]}...{api_key[-4:]}")
    try:
        client = genai.Client(api_key=api_key)
        print("   Connecting to Google to list available models...")
        
        # List models
        models = list(client.models.list())
        
        print(f"\n   ✅ FOUND {len(models)} MODELS. These are valid for you:")
        found_flash = False
        for m in models:
            # We only care about generateContent capable models
            if "generateContent" in m.supported_actions:
                print(f"      - {m.name}")
                if "flash" in m.name: found_flash = True
        
        if not found_flash:
            print("\n   ⚠️  WARNING: No 'Flash' model found. Use one of the names listed above.")
            
    except Exception as e:
        print(f"\n❌ API CONNECTION FAILED: {e}")
        print("   (This usually means the Key is invalid, expired, or the Project doesn't have the Generative Language API enabled)")
