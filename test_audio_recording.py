import pyaudio
import wave
import os

def list_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    
    print("--- Available Audio Devices ---")
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print(f"Input Device id {i} - {p.get_device_info_by_host_api_device_index(0, i).get('name')}")
    print("-------------------------------")
    p.terminate()

def test_recording(device_index):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000 # Whisper default
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "test_output.wav"

    p = pyaudio.PyAudio()

    print(f"\nAttempting to record for {RECORD_SECONDS} seconds on Device {device_index}...")
    
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=CHUNK)

        print("* recording start")

        frames = []

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        print("* recording done")

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        file_size = os.path.getsize(WAVE_OUTPUT_FILENAME)
        print(f"File saved: {WAVE_OUTPUT_FILENAME}, Size: {file_size} bytes")
        if file_size < 1000:
            print("WARNING: File seems too small, recording might have failed invisibly.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    list_devices()
    # We will try to record from default first (no index) then specific
    print("\n--- Testing Default Device ---")
    try:
        test_recording(None)
    except:
        pass
