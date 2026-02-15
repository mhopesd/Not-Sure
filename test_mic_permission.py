import AVFoundation
from AVFoundation import AVCaptureDevice, AVMediaTypeAudio
import time

def check_mic_permission():
    status = AVCaptureDevice.authorizationStatusForMediaType_(AVMediaTypeAudio)
    # 0: NotDetermined, 1: Restricted, 2: Denied, 3: Authorized
    print(f"Current Authorization Status: {status}")
    
    if status == 3:
        print("Authorized via AVFoundation.")
        return True
    elif status == 0:
        print("Not determined. Requesting access...")
        # Note: This async request might not work fully in a CLI script depending on runloop,
        # but verifies the API exists.
        def handler(granted):
             print(f"Access granted: {granted}")
        
        AVCaptureDevice.requestAccessForMediaType_completionHandler_(AVMediaTypeAudio, handler)
        time.sleep(1) # wait a bit for callback
        return False
    else:
        print("Permission Denied or Restricted.")
        return False

if __name__ == "__main__":
    check_mic_permission()
