"""
Unity Integration Helper for Audio Visualization Comparison
============================================================
This script provides Unity-specific analysis and recommendations
for integrating audio visualization in Unity projects.
"""

import json
import os
from typing import Dict, List


class UnityIntegrationHelper:
    """Helper class for Unity-specific integration guidance"""
    
    def __init__(self):
        self.unity_implementations = {
            'MusicVisualizer3D': {
                'script': 'Assets/Scripts/MusicVisualizer3D.cs',
                'type': '3D Cube Array',
                'fft_size': '64-8192',
                'configurable': True,
                'performance': 'High',
                'use_cases': ['Music games', 'Rhythm games', 'Music visualizers']
            },
            'RippleMusicVisualizer': {
                'script': 'Assets/Scripts/RippleMusicVisualizer.cs',
                'type': 'Dynamic Mesh Ripple',
                'fft_size': '64-8192',
                'configurable': True,
                'performance': 'Medium-High',
                'use_cases': ['Artistic installations', 'Ambient effects', 'Music visualizers']
            },
            'AudioLoudnessDetection': {
                'script': 'Assets/Scripts/AudioLoudnessDetection.cs',
                'type': 'Microphone Input',
                'fft_size': 'N/A (time-domain)',
                'configurable': False,
                'performance': 'Very High',
                'use_cases': ['Voice-reactive games', 'Karaoke', 'Audio input']
            }
        }
    
    def generate_unity_settings_recommendations(self) -> Dict:
        """Generate recommended Unity audio settings"""
        return {
            'AudioSettings': {
                'DSP Buffer Size': 'Best Performance',
                'Sample Rate': 44100,
                'Default Speaker Mode': 'Stereo',
                'Virtualization': 'Enabled'
            },
            'Quality Settings': {
                'V Sync Count': 'Every V Blank (for 60 FPS)',
                'Anti Aliasing': '4x Multi Sampling (for visual quality)',
                'Anisotropic Textures': 'Per Texture'
            },
            'Player Settings': {
                'Scripting Backend': 'IL2CPP (for better performance)',
                'API Compatibility Level': '.NET 4.x',
                'Managed Stripping Level': 'Medium (balance size/features)'
            }
        }
    
    def generate_performance_optimization_tips(self) -> List[Dict]:
        """Generate performance optimization tips for Unity"""
        return [
            {
                'category': 'FFT Configuration',
                'tips': [
                    'Use FFT size 1024 for balanced quality/performance',
                    'Lower FFT size (256-512) for mobile devices',
                    'Higher FFT size (2048-4096) for detailed analysis',
                    'Avoid changing FFT size at runtime'
                ]
            },
            {
                'category': 'Smoothing',
                'tips': [
                    'Use smoothingFactor between 0.5-0.8 for responsive animations',
                    'Higher values (0.8-0.9) for smoother but slower response',
                    'Lower values (0.3-0.5) for twitchy but immediate response',
                    'Apply exponential moving average for better results'
                ]
            },
            {
                'category': 'Object Pooling',
                'tips': [
                    'Pre-instantiate visualization objects at Start()',
                    'Avoid Instantiate/Destroy during playback',
                    'Reuse GameObjects instead of creating new ones',
                    'Use object pooling for particle systems'
                ]
            },
            {
                'category': 'Update Loop',
                'tips': [
                    'Call GetSpectrumData() once per frame, not per object',
                    'Cache frequently accessed components',
                    'Use LateUpdate() for visual updates after audio processing',
                    'Consider FixedUpdate() for physics-based visualizations'
                ]
            },
            {
                'category': 'Rendering',
                'tips': [
                    'Use GPU instancing for multiple similar objects',
                    'Combine meshes when possible',
                    'Use simple shaders for real-time performance',
                    'Disable shadows on visualizer objects if not needed'
                ]
            },
            {
                'category': 'Memory',
                'tips': [
                    'Limit array allocations in Update()',
                    'Use fixed-size arrays instead of Lists when possible',
                    'Avoid boxing/unboxing in hot paths',
                    'Profile with Unity Profiler to find bottlenecks'
                ]
            }
        ]
    
    def generate_editor_integration_guide(self) -> str:
        """Generate Unity Editor integration guide"""
        guide = """
# Unity Editor Integration Guide

## Setup Steps

### 1. Import Audio Visualizers
1. Copy visualization scripts to `Assets/Scripts/`
2. Verify scripts compile without errors
3. Check Unity Console for any warnings

### 2. Create Visualization Prefabs
**For 3D Cube Visualizer:**
1. Create empty GameObject named "MusicVisualizer"
2. Add MusicVisualizer3D component
3. Create cube prefab (1x1x1 scale)
4. Assign cube prefab to MusicVisualizer3D
5. Configure parameters in Inspector:
   - FFT Size: 10 (1024 samples)
   - Number of Cubes: 35
   - Smoothing Factor: 0.7
   - Scale Multiplier: 200

**For Ripple Visualizer:**
1. Create empty GameObject named "RippleVisualizer"
2. Add RippleMusicVisualizer component
3. Create material for ripples
4. Configure parameters:
   - Max Radius: 25
   - Ripple Speed: 1.5
   - Circle Resolution: 64
   - Amplitude Multiplier: 8

### 3. Audio Source Setup
1. Add AudioSource component to visualizer GameObject
2. Assign audio clip
3. Configure AudioSource:
   - Play On Awake: True
   - Loop: True (for continuous playback)
   - Volume: 0.7-1.0

### 4. Testing in Editor
1. Enter Play Mode
2. Audio should play automatically
3. Watch visualization respond to audio
4. Adjust parameters in real-time
5. Use Scene view to inspect 3D visualization

## Python Tools Usage in Editor Workflow

### Pre-Production Analysis
```bash
# Analyze audio file before importing
python src/audioFile_matplotlib_visualiser.py

# This generates:
# - Frequency spectrum visualization
# - Time-domain waveform
# - Helps identify bass/treble content
```

### Comparison Analysis
```bash
# Run full comparison
python src/audio_visualization_comparison.py

# Review generated report:
# - comparison_output/COMPARISON_REPORT.md
# - comparison_output/performance_scores.png
```

### Integration Pattern
```
1. Analyze audio with Python tools
   ↓
2. Identify frequency characteristics
   ↓
3. Configure Unity visualizer parameters accordingly
   ↓
4. Test in Unity Editor
   ↓
5. Iterate based on results
```

## Editor Window Integration (Advanced)

### Option 1: External Process
- Run Python script in terminal
- Keep Unity Editor open
- Review Python output
- Apply findings to Unity

### Option 2: Python for Unity (PyU)
- Install Python for Unity package
- Call Python scripts from Editor scripts
- Automate analysis on audio import

### Option 3: Data Export/Import
```python
# Python: Export analysis data
import json
analysis = {
    'dominant_frequencies': [60, 250, 1000, 4000],
    'frequency_bands': [...],
    'recommended_settings': {
        'fft_size': 1024,
        'num_bands': 35
    }
}
with open('audio_analysis.json', 'w') as f:
    json.dump(analysis, f)
```

```csharp
// Unity: Import and use analysis data
[MenuItem("Audio/Import Python Analysis")]
static void ImportAnalysis() {
    string json = File.ReadAllText("audio_analysis.json");
    AudioAnalysis data = JsonUtility.FromJson<AudioAnalysis>(json);
    // Apply settings to visualizers
}
```

## Performance Profiling

### Unity Profiler
1. Window → Analysis → Profiler
2. Play audio visualization
3. Monitor:
   - CPU Usage (should be < 30%)
   - Rendering (should be < 10ms per frame)
   - Scripts (audio processing time)
   - Memory (check for leaks)

### Target Performance
- **Desktop**: 60 FPS consistent
- **Mobile**: 30 FPS minimum
- **VR**: 90 FPS required

### Optimization Checklist
- [ ] FFT size appropriate for platform
- [ ] Object pooling implemented
- [ ] GetSpectrumData() called once per frame
- [ ] No allocations in Update()
- [ ] GPU instancing enabled
- [ ] Profiler shows no bottlenecks

## Best Practices

### DO:
✓ Test with various audio types (bass-heavy, vocal, instrumental)
✓ Provide inspector controls for easy tuning
✓ Use coroutines for non-critical operations
✓ Cache component references in Start()
✓ Use object pooling for dynamic objects
✓ Profile on target platform

### DON'T:
✗ Call GetComponent() in Update()
✗ Use excessive GameObject creation/destruction
✗ Ignore mobile platform limitations
✗ Use high-poly meshes for real-time generation
✗ Forget to handle audio source end events
✗ Use synchronous file I/O in Update()

## Troubleshooting

### Issue: Visualization not responding
- Check AudioSource is playing
- Verify clip is assigned
- Check FFT size is valid (power of 2)
- Ensure Update() is being called

### Issue: Poor performance
- Reduce FFT size
- Lower number of visualizer objects
- Enable GPU instancing
- Profile with Unity Profiler

### Issue: Delayed response
- Reduce smoothing factor
- Check audio latency settings
- Verify DSP buffer size

### Issue: Choppy animation
- Increase smoothing factor
- Check frame rate is consistent
- Reduce computational load

## Example Editor Script

```csharp
#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;

public class VisualizerSetup : EditorWindow
{
    [MenuItem("Audio/Setup Visualizer")]
    static void ShowWindow() {
        GetWindow<VisualizerSetup>("Visualizer Setup");
    }
    
    void OnGUI() {
        GUILayout.Label("Audio Visualizer Setup", EditorStyles.boldLabel);
        
        if (GUILayout.Button("Create 3D Cube Visualizer")) {
            // Create visualizer GameObject
            GameObject viz = new GameObject("MusicVisualizer");
            viz.AddComponent<AudioSource>();
            viz.AddComponent<MusicVisualizer3D>();
            Selection.activeGameObject = viz;
        }
        
        if (GUILayout.Button("Run Python Analysis")) {
            // Execute Python comparison script
            System.Diagnostics.Process.Start("python", 
                "src/audio_visualization_comparison.py");
        }
    }
}
#endif
```

This creates a menu item: Audio → Setup Visualizer

## Resources
- Unity Audio Documentation: https://docs.unity3d.com/Manual/Audio.html
- Unity Profiler: https://docs.unity3d.com/Manual/Profiler.html
- Best Practices: https://docs.unity3d.com/Manual/BestPracticeUnderstandingPerformanceInUnity.html
"""
        return guide
    
    def export_to_json(self, output_dir: str = './comparison_output'):
        """Export Unity integration data to JSON"""
        os.makedirs(output_dir, exist_ok=True)
        
        data = {
            'unity_implementations': self.unity_implementations,
            'recommended_settings': self.generate_unity_settings_recommendations(),
            'optimization_tips': self.generate_performance_optimization_tips()
        }
        
        json_path = f'{output_dir}/unity_integration_guide.json'
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Unity integration guide saved to: {json_path}")
        
        # Also save markdown guide
        guide_path = f'{output_dir}/UNITY_EDITOR_INTEGRATION.md'
        with open(guide_path, 'w') as f:
            f.write(self.generate_editor_integration_guide())
        
        print(f"Unity editor integration guide saved to: {guide_path}")


def main():
    """Generate Unity integration guides"""
    print("\n" + "="*60)
    print("Unity Integration Helper")
    print("="*60 + "\n")
    
    helper = UnityIntegrationHelper()
    helper.export_to_json('./comparison_output')
    
    print("\n✅ Unity integration guides generated!")
    print("\nGenerated files:")
    print("  - comparison_output/unity_integration_guide.json")
    print("  - comparison_output/UNITY_EDITOR_INTEGRATION.md")
    print("\nOpen UNITY_EDITOR_INTEGRATION.md for detailed setup instructions.")


if __name__ == "__main__":
    main()
