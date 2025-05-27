using UnityEngine;
using System.Collections;
using System.Collections.Generic;

[RequireComponent(typeof(AudioSource))]
public class MusicVisualizer3D : MonoBehaviour
{
    [Header("Audio Settings")]
    public AudioSource audioSource;
    public AudioClip[] songs; // Array of songs to choose from
    [Range(6, 13)]
    public int fftSize = 10; // 2^10 = 1024 samples
    
    [Header("Visualization Settings")]
    [Range(10, 50)]
    public int numberOfCubes = 35;
    public GameObject cubePrefab;
    public float cubeSpacing = 1f;
    public float minScale = 0.1f;
    public float maxScale = 100f;
    
    [Header("Animation Settings")]
    [Range(0.1f, 0.9f)]
    public float smoothingFactor = 0.7f;
    public float scaleMultiplier = 200f;
    public bool useLogarithmicScale = true;
    
    [Header("Frequency Settings")]
    public float minFrequency = 20f;    // 20 Hz
    public float maxFrequency = 20000f; // 20 kHz
    public bool showDebugInfo = false;
    
    // Private variables
    private float[] spectrumData;
    private float[] frequencyBands;
    private float[] smoothedBands;
    private GameObject[] cubes;
    private Vector3[] originalScales;
    private FrequencyRange[] frequencyRanges;
    private int sampleRate;
    private float[] previousFrame;
    
    [System.Serializable]
    public struct FrequencyRange
    {
        public float minFreq;
        public float maxFreq;
        public int startIndex;
        public int endIndex;
        public float weight;
        
        public FrequencyRange(float min, float max, int start, int end, float w = 1f)
        {
            minFreq = min;
            maxFreq = max;
            startIndex = start;
            endIndex = end;
            weight = w;
        }
    }
    
    void Start()
    {
        InitializeAudio();
        InitializeCubes();
        CalculateFrequencyRanges();
        
        if (showDebugInfo)
            PrintFrequencyRanges();
    }
    
    void InitializeAudio()
    {
        if (audioSource == null)
            audioSource = GetComponent<AudioSource>();
            
        // Get actual sample rate from Unity
        sampleRate = AudioSettings.outputSampleRate;
        
        // Initialize arrays
        int spectrumSize = (int)Mathf.Pow(2, fftSize);
        spectrumData = new float[spectrumSize];
        frequencyBands = new float[numberOfCubes];
        smoothedBands = new float[numberOfCubes];
        previousFrame = new float[numberOfCubes];
        
        Debug.Log($"Audio initialized - Sample Rate: {sampleRate}Hz, Spectrum Size: {spectrumSize}");
    }
    
    void InitializeCubes()
    {
        cubes = new GameObject[numberOfCubes];
        originalScales = new Vector3[numberOfCubes];
        
        // Get the position of this MusicVisualizer GameObject as the center point
        Vector3 centerPosition = transform.position;
        
        // Create cubes in a line relative to the MusicVisualizer position
        for (int i = 0; i < numberOfCubes; i++)
        {
            Vector3 position = centerPosition + new Vector3(
                (i - numberOfCubes / 2f) * cubeSpacing, 
                0, 
                0
            );
            
            GameObject cube = Instantiate(cubePrefab, position, Quaternion.identity);
            cube.name = $"FrequencyCube_{i}";
            cube.transform.parent = transform;
            
            cubes[i] = cube;
            originalScales[i] = cube.transform.localScale;
            
            // Optional: Color cubes differently
            Renderer renderer = cube.GetComponent<Renderer>();
            if (renderer != null)
            {
                Color cubeColor = Color.HSVToRGB((float)i / numberOfCubes, 0.8f, 1f);
                renderer.material.color = cubeColor;
            }
        }
    }
    
    void CalculateFrequencyRanges()
    {
        frequencyRanges = new FrequencyRange[numberOfCubes];
        int spectrumSize = spectrumData.Length;
        
        // Calculate frequency per bin
        float frequencyPerBin = (float)sampleRate / (spectrumSize * 2f);
        
        // Calculate logarithmic frequency distribution
        float logMin = Mathf.Log10(minFrequency);
        float logMax = Mathf.Log10(maxFrequency);
        float logStep = (logMax - logMin) / numberOfCubes;
        
        for (int i = 0; i < numberOfCubes; i++)
        {
            float logFreqMin = logMin + (i * logStep);
            float logFreqMax = logMin + ((i + 1) * logStep);
            
            float freqMin = Mathf.Pow(10, logFreqMin);
            float freqMax = Mathf.Pow(10, logFreqMax);
            
            // Convert frequencies to spectrum indices
            int startIndex = Mathf.FloorToInt(freqMin / frequencyPerBin);
            int endIndex = Mathf.FloorToInt(freqMax / frequencyPerBin);
            
            // Ensure indices are within bounds
            startIndex = Mathf.Clamp(startIndex, 0, spectrumSize / 2 - 1);
            endIndex = Mathf.Clamp(endIndex, startIndex + 1, spectrumSize / 2);
            
            // Calculate weight for frequency compensation (higher frequencies need boosting)
            float weight = useLogarithmicScale ? Mathf.Log10(freqMax / freqMin + 1) : 1f;
            
            frequencyRanges[i] = new FrequencyRange(freqMin, freqMax, startIndex, endIndex, weight);
        }
    }
    
    void Update()
    {
        if (audioSource != null && audioSource.isPlaying)
        {
            AnalyzeAudio();
            UpdateCubeScales();
        }
    }
    
    void AnalyzeAudio()
    {
        // Get spectrum data from AudioSource
        audioSource.GetSpectrumData(spectrumData, 0, FFTWindow.BlackmanHarris);
        
        // Process each frequency band
        for (int i = 0; i < numberOfCubes; i++)
        {
            FrequencyRange range = frequencyRanges[i];
            float bandValue = 0f;
            int binCount = 0;
            
            // Calculate RMS (Root Mean Square) for better amplitude representation
            for (int j = range.startIndex; j < range.endIndex; j++)
            {
                bandValue += spectrumData[j] * spectrumData[j];
                binCount++;
            }
            
            if (binCount > 0)
            {
                // Apply RMS and frequency weighting
                bandValue = Mathf.Sqrt(bandValue / binCount) * range.weight;
                
                // Apply logarithmic scaling if enabled
                if (useLogarithmicScale)
                {
                    bandValue = Mathf.Log10(bandValue * 1000f + 1f) / 3f; // Normalize log scale
                }
                
                frequencyBands[i] = bandValue * scaleMultiplier;
            }
            else
            {
                frequencyBands[i] = 0f;
            }
        }
        
        // Apply smoothing to reduce jitter
        ApplySmoothing();
    }
    
    void ApplySmoothing()
    {
        for (int i = 0; i < numberOfCubes; i++)
        {
            // Exponential moving average for smooth transitions
            smoothedBands[i] = (smoothingFactor * previousFrame[i]) + 
                              ((1f - smoothingFactor) * frequencyBands[i]);
            
            // Clamp to min/max scale
            smoothedBands[i] = Mathf.Clamp(smoothedBands[i], minScale, maxScale);
            
            // Store for next frame
            previousFrame[i] = smoothedBands[i];
        }
    }
    
    void UpdateCubeScales()
    {
        for (int i = 0; i < numberOfCubes; i++)
        {
            if (cubes[i] != null)
            {
                Vector3 newScale = originalScales[i];
                
                // Scale only in Y direction (up) - change to Z if you prefer
                newScale.y = originalScales[i].y * (1f + smoothedBands[i]);
                
                cubes[i].transform.localScale = newScale;
                
                // Optional: Move cube up so it grows from the ground
                Vector3 newPosition = cubes[i].transform.position;
                newPosition.y = (newScale.y - originalScales[i].y) / 2f;
                cubes[i].transform.position = new Vector3(
                    cubes[i].transform.position.x,
                    newPosition.y,
                    cubes[i].transform.position.z
                );
            }
        }
    }
    
    void PrintFrequencyRanges()
    {
        Debug.Log("=== Frequency Ranges ===");
        for (int i = 0; i < frequencyRanges.Length; i++)
        {
            FrequencyRange range = frequencyRanges[i];
            Debug.Log($"Cube {i}: {range.minFreq:F0}Hz - {range.maxFreq:F0}Hz " +
                     $"(bins {range.startIndex}-{range.endIndex}, weight: {range.weight:F2})");
        }
    }
    
    // Public methods for runtime control
    
    /// <summary>
    /// Play a specific song by index from the songs array
    /// </summary>
    /// <param name="songIndex">Index of the song in the songs array</param>
    public void PlaySong(int songIndex)
    {
        if (songs != null && songIndex >= 0 && songIndex < songs.Length)
        {
            audioSource.Stop();
            audioSource.clip = songs[songIndex];
            audioSource.Play();
            ResetVisualization();
            Debug.Log($"Playing song: {songs[songIndex].name}");
        }
        else
        {
            Debug.LogWarning($"Invalid song index: {songIndex}. Available songs: {(songs?.Length ?? 0)}");
        }
    }
    
    /// <summary>
    /// Play a random song from the songs array
    /// </summary>
    public void PlayRandomSong()
    {
        if (songs != null && songs.Length > 0)
        {
            int randomIndex = Random.Range(0, songs.Length);
            PlaySong(randomIndex);
        }
        else
        {
            Debug.LogWarning("No songs available to play!");
        }
    }
    
    /// <summary>
    /// Play the first song in the array (convenience method)
    /// </summary>
    public void PlayFirstSong()
    {
        PlaySong(0);
    }
    
    /// <summary>
    /// Stop current song and reset visualization
    /// </summary>
    public void StopSong()
    {
        audioSource.Stop();
        ResetVisualization();
        Debug.Log("Song stopped");
    }
    
    /// <summary>
    /// Pause/Resume current song
    /// </summary>
    public void TogglePlayPause()
    {
        if (audioSource.isPlaying)
        {
            audioSource.Pause();
            Debug.Log("Song paused");
        }
        else
        {
            audioSource.UnPause();
            Debug.Log("Song resumed");
        }
    }
    
    public void SetSmoothingFactor(float factor)
    {
        smoothingFactor = Mathf.Clamp01(factor);
    }
    
    public void SetScaleMultiplier(float multiplier)
    {
        scaleMultiplier = Mathf.Max(0.1f, multiplier);
    }
    
    public void ResetVisualization()
    {
        for (int i = 0; i < numberOfCubes; i++)
        {
            previousFrame[i] = 0f;
            smoothedBands[i] = 0f;
            if (cubes[i] != null)
            {
                cubes[i].transform.localScale = originalScales[i];
            }
        }
    }
    
    // Context menu for easy testing in editor
    [ContextMenu("Play First Song")]
    void PlayFirstSongContext()
    {
        PlayFirstSong();
    }
    
    [ContextMenu("Play Random Song")]
    void PlayRandomSongContext()
    {
        PlayRandomSong();
    }
    
    [ContextMenu("Stop Song")]
    void StopSongContext()
    {
        StopSong();
    }
    
    // Gizmos for debugging
    void OnDrawGizmosSelected()
    {
        if (cubes != null)
        {
            Gizmos.color = Color.yellow;
            for (int i = 0; i < cubes.Length; i++)
            {
                if (cubes[i] != null)
                {
                    Vector3 pos = cubes[i].transform.position;
                    Vector3 size = cubes[i].transform.localScale;
                    Gizmos.DrawWireCube(pos, size);
                }
            }
        }
    }
}