# Wizard Voice Assistant - Troubleshooting Guide

## Table of Contents

1. [Common Issues](#common-issues)
2. [Installation Problems](#installation-problems)
3. [Audio Issues](#audio-issues)
4. [Voice Recognition Problems](#voice-recognition-problems)
5. [Command Execution Issues](#command-execution-issues)
6. [Performance Problems](#performance-problems)
7. [Configuration Issues](#configuration-issues)
8. [Platform-Specific Issues](#platform-specific-issues)
9. [Diagnostic Tools](#diagnostic-tools)
10. [Getting Help](#getting-help)

---

## Common Issues

### Wizard Won't Start

**Symptoms**: Application fails to launch or crashes immediately

**Possible Causes & Solutions**:

1. **Missing Dependencies**
   ```bash
   # Check if all dependencies are installed
   pip install -r requirements.txt
   
   # Verify specific packages
   python -c "import pyttsx3, speech_recognition, pyaudio"
   ```

2. **Python Version Incompatibility**
   ```bash
   # Check Python version (requires 3.8+)
   python --version
   
   # If using wrong version, create virtual environment with correct Python
   python3.8 -m venv wizard_env
   ```

3. **Configuration File Issues**
   ```bash
   # Reset configuration to defaults
   python configure.py
   
   # Or delete and recreate config
   rm config/wizard_config.json
   python setup.py
   ```

4. **Permission Issues**
   - **Windows**: Run as administrator
   - **macOS/Linux**: Check file permissions
   ```bash
   chmod +x start_wizard.py
   ```

### Wake Word Not Detected

**Symptoms**: Wizard doesn't respond to wake words

**Solutions**:

1. **Check Microphone**
   ```bash
   # Test microphone access
   python -c "
   import pyaudio
   p = pyaudio.PyAudio()
   print('Audio devices:', p.get_device_count())
   p.terminate()
   "
   ```

2. **Adjust Sensitivity**
   - Open configuration: `python configure.py`
   - Increase wake word sensitivity
   - Try different wake words

3. **Background Noise**
   - Move to quieter environment
   - Adjust microphone position
   - Use noise-canceling microphone

4. **Audio Device Selection**
   ```python
   # Check available audio devices
   import pyaudio
   p = pyaudio.PyAudio()
   for i in range(p.get_device_count()):
       info = p.get_device_info_by_index(i)
       print(f"Device {i}: {info['name']}")
   ```

### Commands Not Recognized

**Symptoms**: Wizard hears you but doesn't understand commands

**Solutions**:

1. **Speak Clearly**
   - Speak at normal pace
   - Reduce background noise
   - Face the microphone

2. **Check Command Syntax**
   - Use exact command phrases from documentation
   - Try alternative phrasings
   - Check if application names are correct

3. **Language Settings**
   - Verify language configuration matches your speech
   - Update speech recognition models

---

## Installation Problems

### Dependency Installation Failures

**PyAudio Installation Issues**:

**Windows**:
```bash
# Install Visual Studio Build Tools first
# Then install PyAudio
pip install pipwin
pipwin install pyaudio
```

**macOS**:
```bash
# Install portaudio first
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian)**:
```bash
# Install system dependencies
sudo apt-get install python3-dev python3-pip
sudo apt-get install portaudio19-dev
pip install pyaudio
```

**Alternative PyAudio Installation**:
```bash
# Use conda instead of pip
conda install pyaudio

# Or use pre-compiled wheels
pip install --upgrade pip
pip install pyaudio --force-reinstall
```

### Speech Recognition Issues

**Vosk Model Download**:
```bash
# Manual model download
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip -d wizard/data/
mv wizard/data/vosk-model-en-us-0.22 wizard/data/vosk_model
```

**NLTK Data Download**:
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

### Permission Errors

**Windows**:
- Run Command Prompt as Administrator
- Check Windows Defender exclusions
- Verify user account permissions

**macOS**:
```bash
# Grant microphone permissions
# System Preferences > Security & Privacy > Privacy > Microphone
# Add Terminal or Python to allowed apps

# Fix file permissions
sudo chown -R $(whoami) /path/to/wizard
```

**Linux**:
```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Set file permissions
chmod +x wizard/main.py
chmod -R 755 wizard/
```

---

## Audio Issues

### No Audio Input Detected

**Diagnosis**:
```python
# Test microphone
import pyaudio
import wave

def test_microphone():
    p = pyaudio.PyAudio()
    
    # List input devices
    print("Input devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"  {i}: {info['name']}")
    
    # Test recording
    try:
        stream = p.open(format=pyaudio.paInt16,
                       channels=1,
                       rate=44100,
                       input=True,
                       frames_per_buffer=1024)
        print("Recording test... (speak now)")
        data = stream.read(1024)
        print(f"Recorded {len(data)} bytes")
        stream.close()
    except Exception as e:
        print(f"Recording failed: {e}")
    
    p.terminate()

test_microphone()
```

**Solutions**:

1. **Check Default Audio Device**
   - **Windows**: Control Panel > Sound > Recording
   - **macOS**: System Preferences > Sound > Input
   - **Linux**: `alsamixer` or `pavucontrol`

2. **Update Audio Drivers**
   - Download latest drivers from manufacturer
   - Restart after installation

3. **USB Microphone Issues**
   - Try different USB ports
   - Check USB power management settings
   - Test with different USB cable

### No Audio Output

**Text-to-Speech Not Working**:

```python
# Test TTS engines
import pyttsx3

def test_tts():
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"Available voices: {len(voices)}")
        for i, voice in enumerate(voices):
            print(f"  {i}: {voice.name}")
        
        engine.say("Testing text to speech")
        engine.runAndWait()
        print("TTS test completed")
    except Exception as e:
        print(f"TTS test failed: {e}")

test_tts()
```

**Solutions**:

1. **Check System Volume**
   - Ensure system volume is not muted
   - Check application-specific volume

2. **Audio Output Device**
   - Verify correct output device selected
   - Test with different audio devices

3. **TTS Engine Issues**
   ```bash
   # Reinstall TTS engine
   pip uninstall pyttsx3
   pip install pyttsx3
   
   # Try alternative TTS
   pip install gTTS
   ```

### Audio Quality Issues

**Poor Recognition Accuracy**:

1. **Microphone Quality**
   - Use dedicated microphone instead of built-in
   - Position microphone 6-12 inches from mouth
   - Use pop filter if available

2. **Environment Optimization**
   - Reduce echo (soft furnishings help)
   - Minimize background noise
   - Avoid air conditioning/fan noise

3. **Audio Settings**
   ```python
   # Adjust audio parameters
   CHUNK = 1024
   FORMAT = pyaudio.paInt16
   CHANNELS = 1
   RATE = 16000  # Try different sample rates
   ```

---

## Voice Recognition Problems

### Low Recognition Accuracy

**Diagnosis Script**:
```python
# Test recognition accuracy
import speech_recognition as sr

def test_recognition():
    r = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        r.adjust_for_ambient_noise(source)
        print("Say something:")
        audio = r.listen(source, timeout=5)
    
    try:
        text = r.recognize_google(audio)  # Test with Google
        print(f"Google recognized: {text}")
    except:
        print("Google recognition failed")
    
    try:
        text = r.recognize_sphinx(audio)  # Test with Sphinx
        print(f"Sphinx recognized: {text}")
    except:
        print("Sphinx recognition failed")

test_recognition()
```

**Solutions**:

1. **Calibrate Microphone**
   ```python
   # Add to Wizard startup
   recognizer.adjust_for_ambient_noise(microphone, duration=2)
   ```

2. **Improve Speech Patterns**
   - Speak clearly and at moderate pace
   - Use consistent volume
   - Avoid mumbling or trailing off

3. **Update Recognition Models**
   - Download latest Vosk models
   - Train custom models if needed
   - Use language-specific models

### Recognition Timeout Issues

**Symptoms**: Wizard stops listening too quickly or waits too long

**Configuration Adjustments**:
```json
{
  "speech_recognition": {
    "timeout": 5,
    "phrase_timeout": 2,
    "energy_threshold": 300,
    "dynamic_energy_threshold": true
  }
}
```

**Solutions**:

1. **Adjust Timeout Settings**
   - Increase timeout for slower speakers
   - Decrease for faster interaction

2. **Energy Threshold Tuning**
   ```python
   # Auto-adjust energy threshold
   recognizer.dynamic_energy_threshold = True
   recognizer.energy_threshold = 300  # Adjust based on environment
   ```

### Language and Accent Issues

**Multi-language Support**:
```python
# Configure language
recognizer = sr.Recognizer()
# For Spanish
text = recognizer.recognize_google(audio, language='es-ES')
# For French
text = recognizer.recognize_google(audio, language='fr-FR')
```

**Accent Adaptation**:
1. Use region-specific language models
2. Train with your voice samples
3. Adjust recognition parameters for accent

---

## Command Execution Issues

### Applications Won't Launch

**Diagnosis**:
```python
# Test application paths
import subprocess
import shutil

def test_app_launch(app_name):
    # Check if app is in PATH
    if shutil.which(app_name):
        print(f"{app_name} found in PATH")
        return True
    
    # Try common locations
    common_paths = [
        f"C:\\Program Files\\{app_name}\\{app_name}.exe",
        f"C:\\Program Files (x86)\\{app_name}\\{app_name}.exe",
        f"/Applications/{app_name}.app",
        f"/usr/bin/{app_name}"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"{app_name} found at {path}")
            return True
    
    print(f"{app_name} not found")
    return False

# Test common applications
test_app_launch("notepad")
test_app_launch("calculator")
```

**Solutions**:

1. **Update Application Paths**
   ```bash
   # Configure application paths
   python configure.py
   # Add full paths to applications
   ```

2. **Check Application Names**
   - Use exact executable names
   - Include file extensions on Windows
   - Check case sensitivity on Linux/macOS

3. **Permission Issues**
   - Run Wizard with appropriate permissions
   - Check application execution permissions

### File Operations Fail

**Common File Issues**:

1. **Path Problems**
   ```python
   # Use absolute paths
   import os
   file_path = os.path.abspath("document.txt")
   
   # Handle spaces in paths
   file_path = '"' + file_path + '"'
   ```

2. **Permission Errors**
   ```bash
   # Check file permissions
   ls -la filename
   
   # Fix permissions
   chmod 644 filename  # Read/write for owner
   ```

3. **File Locks**
   - Close applications using the file
   - Check for background processes
   - Restart if necessary

### System Commands Fail

**Windows-specific Issues**:
```python
# Use proper Windows commands
import subprocess

# Correct way to shutdown on Windows
subprocess.run(["shutdown", "/s", "/t", "0"])

# Use cmd for complex commands
subprocess.run(["cmd", "/c", "dir"], shell=True)
```

**Cross-platform Solutions**:
```python
import platform

def shutdown_system():
    system = platform.system()
    if system == "Windows":
        subprocess.run(["shutdown", "/s", "/t", "0"])
    elif system == "Darwin":  # macOS
        subprocess.run(["sudo", "shutdown", "-h", "now"])
    elif system == "Linux":
        subprocess.run(["sudo", "shutdown", "-h", "now"])
```

---

## Performance Problems

### High CPU Usage

**Diagnosis**:
```python
import psutil
import time

def monitor_performance():
    process = psutil.Process()
    
    for i in range(10):
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        print(f"CPU: {cpu_percent}%, Memory: {memory_info.rss / 1024 / 1024:.1f} MB")
        time.sleep(1)

monitor_performance()
```

**Solutions**:

1. **Optimize Wake Word Detection**
   ```python
   # Reduce wake word sensitivity
   # Use smaller audio chunks
   CHUNK = 512  # Smaller chunks
   
   # Implement sleep between checks
   time.sleep(0.1)
   ```

2. **Limit Background Processing**
   - Disable unused features
   - Reduce logging verbosity
   - Optimize audio processing

3. **Resource Management**
   ```python
   # Proper resource cleanup
   def cleanup_resources():
       if hasattr(self, 'audio_stream'):
           self.audio_stream.close()
       if hasattr(self, 'recognizer'):
           del self.recognizer
   ```

### Memory Leaks

**Detection**:
```python
import tracemalloc

# Start tracing
tracemalloc.start()

# Your code here

# Get memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
```

**Prevention**:
```python
# Proper cleanup in classes
class AudioProcessor:
    def __del__(self):
        self.cleanup()
    
    def cleanup(self):
        if hasattr(self, 'stream'):
            self.stream.close()
```

### Slow Response Times

**Optimization Strategies**:

1. **Preload Models**
   ```python
   # Load models at startup
   class WizardApp:
       def __init__(self):
           self.preload_models()
       
       def preload_models(self):
           # Load speech recognition model
           # Load TTS engine
           # Cache common responses
   ```

2. **Async Processing**
   ```python
   import asyncio
   
   async def process_command_async(command):
       # Non-blocking command processing
       result = await some_async_operation(command)
       return result
   ```

3. **Caching**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def get_weather_data(city):
       # Cache weather data
       return fetch_weather(city)
   ```

---

## Configuration Issues

### Configuration File Corruption

**Symptoms**: Wizard fails to start with config errors

**Recovery**:
```bash
# Backup current config
cp config/wizard_config.json config/wizard_config.json.backup

# Reset to defaults
python configure.py

# Or manually create minimal config
cat > config/wizard_config.json << EOF
{
  "assistant_name": "Wizard",
  "wake_words": ["Hey Wizard", "Wizard"],
  "voice": {
    "gender": "female",
    "speed": 1.0,
    "volume": 0.8
  }
}
EOF
```

### Invalid Settings

**Validation Script**:
```python
import json

def validate_config(config_path):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ['assistant_name', 'wake_words', 'voice']
        for field in required_fields:
            if field not in config:
                print(f"Missing required field: {field}")
        
        # Validate voice settings
        voice = config.get('voice', {})
        if 'speed' in voice:
            speed = voice['speed']
            if not 0.5 <= speed <= 2.0:
                print(f"Invalid voice speed: {speed} (must be 0.5-2.0)")
        
        print("Configuration validation complete")
        
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config file: {e}")
    except Exception as e:
        print(f"Config validation error: {e}")

validate_config("config/wizard_config.json")
```

---

## Platform-Specific Issues

### Windows Issues

**Windows Defender Interference**:
```bash
# Add exclusions to Windows Defender
# Go to: Windows Security > Virus & threat protection > Exclusions
# Add folder: C:\path\to\wizard-voice-assistant
```

**Audio Driver Issues**:
- Update audio drivers from manufacturer
- Check Windows Audio service is running
- Try different audio formats in device properties

**Permission Problems**:
```cmd
# Run as administrator
# Right-click Command Prompt > Run as administrator
cd C:\path\to\wizard-voice-assistant
python wizard\main.py
```

### macOS Issues

**Microphone Permissions**:
```bash
# Grant microphone access
# System Preferences > Security & Privacy > Privacy > Microphone
# Check Terminal and Python
```

**Gatekeeper Issues**:
```bash
# Allow unsigned applications
sudo spctl --master-disable

# Or sign the application
codesign -s "Developer ID" wizard/main.py
```

**Audio Unit Issues**:
```bash
# Reset Core Audio
sudo killall coreaudiod
```

### Linux Issues

**Audio System Problems**:
```bash
# Check audio system
pulseaudio --check -v

# Restart PulseAudio
pulseaudio -k
pulseaudio --start

# Check ALSA
aplay -l  # List playback devices
arecord -l  # List recording devices
```

**Permission Issues**:
```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Check device permissions
ls -la /dev/snd/
```

**Dependencies**:
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev portaudio19-dev

# CentOS/RHEL
sudo yum install python3-devel portaudio-devel

# Arch Linux
sudo pacman -S python portaudio
```

---

## Diagnostic Tools

### Built-in Diagnostics

**System Check Script**:
```python
#!/usr/bin/env python3
"""Wizard Voice Assistant Diagnostic Tool"""

import sys
import platform
import subprocess
import importlib

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version >= (3, 8):
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False

def check_dependencies():
    """Check required Python packages"""
    required_packages = [
        'pyttsx3', 'speech_recognition', 'pyaudio',
        'nltk', 'psutil', 'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_audio_devices():
    """Check audio input/output devices"""
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        input_devices = 0
        output_devices = 0
        
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices += 1
            if device_info['maxOutputChannels'] > 0:
                output_devices += 1
        
        p.terminate()
        
        print(f"✅ Audio devices: {input_devices} input, {output_devices} output")
        return input_devices > 0 and output_devices > 0
        
    except Exception as e:
        print(f"❌ Audio device check failed: {e}")
        return False

def check_configuration():
    """Check configuration file"""
    import json
    from pathlib import Path
    
    config_file = Path("config/wizard_config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print("✅ Configuration file valid")
            return True
        except json.JSONDecodeError:
            print("❌ Configuration file corrupted")
            return False
    else:
        print("⚠️  Configuration file not found")
        return False

def run_diagnostics():
    """Run all diagnostic checks"""
    print("🔍 Wizard Voice Assistant Diagnostics")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Audio Devices", check_audio_devices),
        ("Configuration", check_configuration)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        result = check_func()
        results.append((name, result))
    
    print("\n📊 Summary:")
    print("-" * 20)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All checks passed! Wizard should work correctly.")
    else:
        print("\n⚠️  Some checks failed. Please address the issues above.")
    
    return all_passed

if __name__ == "__main__":
    run_diagnostics()
```

### Log Analysis

**Enable Debug Logging**:
```python
import logging

# Configure debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/wizard_debug.log'),
        logging.StreamHandler()
    ]
)
```

**Log Analysis Script**:
```python
def analyze_logs(log_file):
    """Analyze Wizard log files for common issues"""
    
    error_patterns = {
        'audio_error': r'audio.*error|microphone.*error',
        'recognition_error': r'recognition.*failed|speech.*error',
        'command_error': r'command.*failed|unknown.*command',
        'config_error': r'config.*error|configuration.*failed'
    }
    
    with open(log_file, 'r') as f:
        logs = f.read()
    
    for error_type, pattern in error_patterns.items():
        matches = re.findall(pattern, logs, re.IGNORECASE)
        if matches:
            print(f"Found {len(matches)} {error_type} occurrences")
```

---

## Getting Help

### Self-Help Resources

1. **Documentation**
   - Read the User Manual thoroughly
   - Check Command Reference for syntax
   - Review FAQ for common questions

2. **Log Files**
   - Check `logs/wizard.log` for general information
   - Review `logs/wizard_errors.log` for error details
   - Enable debug mode for verbose logging

3. **Configuration**
   - Try resetting configuration to defaults
   - Test with minimal configuration
   - Verify all paths and settings

### Community Support

1. **Issue Tracker**
   - Search existing issues before creating new ones
   - Provide detailed information when reporting bugs
   - Include system information and log files

2. **Discussion Forums**
   - Ask questions in community forums
   - Share solutions and tips
   - Help other users with similar issues

### Bug Reports

**Information to Include**:

1. **System Information**
   ```bash
   python --version
   pip list | grep -E "(pyttsx3|speech_recognition|pyaudio)"
   uname -a  # Linux/macOS
   systeminfo  # Windows
   ```

2. **Error Details**
   - Complete error messages
   - Steps to reproduce
   - Expected vs actual behavior
   - Log file excerpts

3. **Configuration**
   - Sanitized configuration file
   - Audio device information
   - Environment variables

**Bug Report Template**:
```markdown
## Bug Report

### Environment
- OS: [Windows 10/macOS 12/Ubuntu 20.04]
- Python Version: [3.9.7]
- Wizard Version: [1.0.0]

### Description
[Clear description of the issue]

### Steps to Reproduce
1. [First step]
2. [Second step]
3. [Third step]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Error Messages
```
[Paste error messages here]
```

### Additional Information
[Any other relevant information]
```

### Professional Support

For enterprise users or complex deployments:

1. **Consulting Services**
   - Custom implementation assistance
   - Performance optimization
   - Integration support

2. **Training**
   - User training sessions
   - Developer workshops
   - Best practices guidance

3. **Maintenance**
   - Regular health checks
   - Proactive monitoring
   - Update management

---

## Prevention Tips

### Regular Maintenance

1. **Keep Updated**
   - Update Wizard regularly
   - Update Python dependencies
   - Update system audio drivers

2. **Monitor Performance**
   - Check resource usage periodically
   - Review log files for warnings
   - Test functionality regularly

3. **Backup Configuration**
   ```bash
   # Create configuration backup
   cp config/wizard_config.json config/wizard_config.json.backup
   
   # Backup user data
   tar -czf wizard_backup.tar.gz config/ logs/ wizard/data/
   ```

### Best Practices

1. **Environment Setup**
   - Use dedicated microphone
   - Minimize background noise
   - Ensure stable power supply

2. **Usage Patterns**
   - Speak clearly and consistently
   - Use standard command phrases
   - Allow processing time between commands

3. **System Health**
   - Keep system resources available
   - Close unnecessary applications
   - Restart Wizard periodically

---

This troubleshooting guide covers the most common issues encountered with Wizard Voice Assistant. If you encounter problems not covered here, please consult the community resources or file a detailed bug report.