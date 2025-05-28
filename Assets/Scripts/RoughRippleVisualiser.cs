using UnityEngine;
using System.Collections.Generic;
using System.Collections;

[RequireComponent(typeof(AudioSource))]
public class RoughRippleVisualiser : MonoBehaviour
{
    [Header("Audio Settings")]
    public AudioSource audioSource;
    public AudioClip[] songs;
    [Range(6, 13)]
    public int fftSize = 10; // 2^10 = 1024 samples

    [Header("Ripple Settings")]
    [Range(5.0f, 50.0f)]
    public float maxRadius = 25f; // Maximum radius for ripples
    [Range(0.5f, 3.0f)]
    public float rippleSpeed = 1.5f; // Speed of ripple propagation
    [Range(0.1f, 2.0f)]
    public float rippleLifetime = 1.0f; // How long ripples last
    [Range(3, 8)]
    public int maxConcurrentRipples = 5; // Maximum number of ripples

    [Header("Waveform Settings")]
    [Range(16, 128)]
    public int circleResolution = 64; // Points around the circle
    [Range(8, 64)]
    public int radialSegments = 32; // Radial segments for mesh detail
    [Range(0.1f, 10.0f)]
    public float amplitudeMultiplier = 5.0f;
    [Range(0.1f, 5.0f)]
    public float baseRadius = 2.0f; // Fixed base radius

    [Header("Visual Settings")]
    public Material rippleMaterial;
    public Gradient rippleColorGradient;
    [Range(0.1f, 1.0f)]
    public float rippleInterval = 0.2f; // Time between new ripples
    public bool useWireframe = false;

    [Header("Audio Analysis")]
    [Range(0.1f, 0.9f)]
    public float smoothingFactor = 0.7f;
    [Range(1.0f, 20.0f)]
    public float sensitivityMultiplier = 8.0f;

    // Private variables
    private float[] spectrumData;
    private float currentAmplitude;
    private float smoothedAmplitude;
    private List<Ripple> activeRipples;
    private float lastRippleTime;
    private int sampleRate;

    // Ripple class to track individual ripples
    [System.Serializable]
    public class Ripple
    {
        public GameObject meshObject;
        public MeshFilter meshFilter;
        public MeshRenderer meshRenderer;
        public Mesh mesh;
        public float birthTime;
        public float birthAmplitude;
        public float currentRadius;
        public Vector3[] vertices;
        public Color originalColor;

        public Ripple(float amplitude, Color color)
        {
            birthTime = Time.time;
            birthAmplitude = amplitude;
            currentRadius = 0f;
            originalColor = color;
        }

        public float GetAge()
        {
            return Time.time - birthTime;
        }

        public float GetLifeProgress(float maxLifetime)
        {
            return Mathf.Clamp01(GetAge() / maxLifetime);
        }
    }

    void Start()
    {
        InitializeAudio();
        InitializeRippleSystem();

        // Auto-play first song if available
        if (songs != null && songs.Length > 0)
        {
            PlaySong(0);
        }
    }

    void InitializeAudio()
    {
        if (audioSource == null)
            audioSource = GetComponent<AudioSource>();

        sampleRate = AudioSettings.outputSampleRate;
        int spectrumSize = (int)Mathf.Pow(2, fftSize);
        spectrumData = new float[spectrumSize];

        Debug.Log($"Audio initialized - Sample Rate: {sampleRate}Hz, Spectrum Size: {spectrumSize}");
    }

    void InitializeRippleSystem()
    {
        activeRipples = new List<Ripple>();

        // Create default material if none assigned
        if (rippleMaterial == null)
        {
            rippleMaterial = new Material(Shader.Find("Standard"));
            rippleMaterial.color = Color.cyan;
            rippleMaterial.SetFloat("_Metallic", 0.5f);
            rippleMaterial.SetFloat("_Smoothness", 0.8f);
        }

        // Setup default gradient if not configured
        if (rippleColorGradient == null)
        {
            rippleColorGradient = new Gradient();
            GradientColorKey[] colorKeys = new GradientColorKey[3];
            colorKeys[0] = new GradientColorKey(Color.red, 0.0f);
            colorKeys[1] = new GradientColorKey(Color.yellow, 0.5f);
            colorKeys[2] = new GradientColorKey(Color.blue, 1.0f);

            GradientAlphaKey[] alphaKeys = new GradientAlphaKey[2];
            alphaKeys[0] = new GradientAlphaKey(1.0f, 0.0f);
            alphaKeys[1] = new GradientAlphaKey(0.0f, 1.0f);

            rippleColorGradient.SetKeys(colorKeys, alphaKeys);
        }
    }

    void Update()
    {
        if (audioSource != null && audioSource.isPlaying)
        {
            AnalyzeAudio();
            UpdateRipples();
            CheckForNewRipple();
        }

        CleanupOldRipples();
    }

    void AnalyzeAudio()
    {
        // Get spectrum data
        audioSource.GetSpectrumData(spectrumData, 0, FFTWindow.BlackmanHarris);

        // Calculate total amplitude (focusing on lower frequencies for better bass response)
        currentAmplitude = 0f;
        int bassRange = Mathf.Min(spectrumData.Length / 4, 256); // Focus on bass frequencies

        for (int i = 0; i < bassRange; i++)
        {
            // Weight lower frequencies more heavily
            float weight = 1f - (float)i / bassRange;
            weight = weight * weight; // Square for more emphasis on bass
            currentAmplitude += spectrumData[i] * weight;
        }

        // Apply sensitivity and smoothing
        currentAmplitude *= sensitivityMultiplier;
        smoothedAmplitude = (smoothingFactor * smoothedAmplitude) +
                           ((1f - smoothingFactor) * currentAmplitude);
    }

    void CheckForNewRipple()
    {
        // Create new ripple based on time interval and amplitude threshold
        if (Time.time - lastRippleTime >= rippleInterval && smoothedAmplitude > 0.05f)
        {
            // Color based on amplitude
            Color rippleColor = rippleColorGradient.Evaluate(Mathf.Clamp01(smoothedAmplitude));

            CreateNewRipple(smoothedAmplitude, rippleColor);
            lastRippleTime = Time.time;
        }
    }

    void CreateNewRipple(float amplitude, Color color)
    {
        // Remove oldest ripple if we're at the limit
        if (activeRipples.Count >= maxConcurrentRipples)
        {
            Ripple oldestRipple = activeRipples[0];
            if (oldestRipple.meshObject != null)
                DestroyImmediate(oldestRipple.meshObject);
            activeRipples.RemoveAt(0);
        }

        // Create new ripple
        Ripple newRipple = new Ripple(amplitude, color);

        // Create GameObject and components
        newRipple.meshObject = new GameObject($"Ripple_{Time.time:F2}");
        newRipple.meshObject.transform.parent = transform;
        newRipple.meshObject.transform.localPosition = Vector3.zero;

        newRipple.meshFilter = newRipple.meshObject.AddComponent<MeshFilter>();
        newRipple.meshRenderer = newRipple.meshObject.AddComponent<MeshRenderer>();

        // Create and assign material
        Material instanceMaterial = new Material(rippleMaterial);
        instanceMaterial.color = color;
        if (useWireframe)
        {
            instanceMaterial.SetFloat("_Mode", 1); // Transparent mode for wireframe effect
            instanceMaterial.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            instanceMaterial.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        }
        newRipple.meshRenderer.material = instanceMaterial;

        // Create initial mesh
        newRipple.mesh = CreateParaboloidMesh(0f, amplitude);
        newRipple.meshFilter.mesh = newRipple.mesh;

        activeRipples.Add(newRipple);
    }

    void UpdateRipples()
    {
        foreach (Ripple ripple in activeRipples)
        {
            if (ripple.meshObject == null) continue;

            float age = ripple.GetAge();
            float lifeProgress = ripple.GetLifeProgress(rippleLifetime);

            // Update ripple radius
            ripple.currentRadius = (age * rippleSpeed * maxRadius / rippleLifetime);

            // Calculate amplitude decay (paraboloid height decreases over time)
            float amplitudeDecay = 1f - lifeProgress;
            amplitudeDecay = Mathf.Pow(amplitudeDecay, 2); // Quadratic decay for natural look
            float currentHeight = ripple.birthAmplitude * amplitudeDecay;

            // Update mesh
            if (ripple.currentRadius <= maxRadius)
            {
                UpdateParaboloidMesh(ripple.mesh, ripple.currentRadius, currentHeight);

                // Update material color with fade
                Color currentColor = ripple.originalColor;
                currentColor.a = amplitudeDecay;
                ripple.meshRenderer.material.color = currentColor;

                // Update transparency for fade effect
                if (lifeProgress > 0.7f)
                {
                    ripple.meshRenderer.material.SetFloat("_Mode", 3); // Transparent
                    ripple.meshRenderer.material.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                    ripple.meshRenderer.material.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                    ripple.meshRenderer.material.SetInt("_ZWrite", 0);
                    ripple.meshRenderer.material.DisableKeyword("_ALPHATEST_ON");
                    ripple.meshRenderer.material.EnableKeyword("_ALPHABLEND_ON");
                    ripple.meshRenderer.material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
                    ripple.meshRenderer.material.renderQueue = 3000;
                }
            }
        }
    }

    void CleanupOldRipples()
    {
        for (int i = activeRipples.Count - 1; i >= 0; i--)
        {
            Ripple ripple = activeRipples[i];

            if (ripple.GetAge() > rippleLifetime || ripple.currentRadius > maxRadius)
            {
                if (ripple.meshObject != null)
                    DestroyImmediate(ripple.meshObject);
                activeRipples.RemoveAt(i);
            }
        }
    }

    Mesh CreateParaboloidMesh(float radius, float amplitude)
    {
        Mesh mesh = new Mesh();
        mesh.name = "ParaboloidRipple";

        // Calculate vertices
        List<Vector3> vertices = new List<Vector3>();
        List<int> triangles = new List<int>();
        List<Vector2> uvs = new List<Vector2>();

        // Center vertex
        vertices.Add(Vector3.zero);
        uvs.Add(new Vector2(0.5f, 0.5f));

        // Create concentric circles
        for (int ring = 1; ring <= radialSegments; ring++)
        {
            float ringRadius = (float)ring / radialSegments * radius;
            if (ringRadius < baseRadius) ringRadius = baseRadius;

            for (int i = 0; i < circleResolution; i++)
            {
                float angle = (float)i / circleResolution * 2f * Mathf.PI;
                float x = Mathf.Cos(angle) * ringRadius;
                float z = Mathf.Sin(angle) * ringRadius;

                // Paraboloid height calculation: y = amplitude * (1 - (r/radius)^2)
                float normalizedRadius = ringRadius / Mathf.Max(radius, baseRadius);
                float y = amplitude * (1f - normalizedRadius * normalizedRadius);
                if (y < 0) y = 0;

                vertices.Add(new Vector3(x, y, z));

                // UV mapping
                float u = (x / maxRadius + 1f) * 0.5f;
                float v = (z / maxRadius + 1f) * 0.5f;
                uvs.Add(new Vector2(u, v));
            }
        }

        // Create triangles
        CreateParaboloidTriangles(triangles, circleResolution, radialSegments);

        mesh.vertices = vertices.ToArray();
        mesh.triangles = triangles.ToArray();
        mesh.uv = uvs.ToArray();
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        return mesh;
    }

    void UpdateParaboloidMesh(Mesh mesh, float radius, float amplitude)
    {
        Vector3[] vertices = mesh.vertices;

        // Update vertex positions
        int vertexIndex = 1; // Skip center vertex

        for (int ring = 1; ring <= radialSegments; ring++)
        {
            float ringRadius = (float)ring / radialSegments * radius;
            if (ringRadius < baseRadius) ringRadius = baseRadius;

            for (int i = 0; i < circleResolution; i++)
            {
                float angle = (float)i / circleResolution * 2f * Mathf.PI;
                float x = Mathf.Cos(angle) * ringRadius;
                float z = Mathf.Sin(angle) * ringRadius;

                // Paraboloid height calculation
                float normalizedRadius = ringRadius / Mathf.Max(radius, baseRadius);
                float y = amplitude * (1f - normalizedRadius * normalizedRadius);
                if (y < 0) y = 0;

                vertices[vertexIndex] = new Vector3(x, y, z);
                vertexIndex++;
            }
        }

        mesh.vertices = vertices;
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
    }

    void CreateParaboloidTriangles(List<int> triangles, int resolution, int segments)
    {
        // Connect center to first ring
        for (int i = 0; i < resolution; i++)
        {
            int next = (i + 1) % resolution;
            triangles.Add(0); // Center
            triangles.Add(i + 1);
            triangles.Add(next + 1);
        }

        // Connect rings
        for (int ring = 0; ring < segments - 1; ring++)
        {
            int currentRingStart = ring * resolution + 1;
            int nextRingStart = (ring + 1) * resolution + 1;

            for (int i = 0; i < resolution; i++)
            {
                int next = (i + 1) % resolution;

                // First triangle
                triangles.Add(currentRingStart + i);
                triangles.Add(nextRingStart + i);
                triangles.Add(currentRingStart + next);

                // Second triangle
                triangles.Add(currentRingStart + next);
                triangles.Add(nextRingStart + i);
                triangles.Add(nextRingStart + next);
            }
        }
    }

    // Song control methods
    public void PlaySong(int songIndex)
    {
        if (songs != null && songIndex >= 0 && songIndex < songs.Length)
        {
            audioSource.Stop();
            audioSource.clip = songs[songIndex];
            audioSource.Play();
            ClearAllRipples();
            Debug.Log($"Playing song: {songs[songIndex].name}");
        }
        else
        {
            Debug.LogWarning($"Invalid song index: {songIndex}. Available songs: {(songs?.Length ?? 0)}");
        }
    }

    public void PlayRandomSong()
    {
        if (songs != null && songs.Length > 0)
        {
            int randomIndex = Random.Range(0, songs.Length);
            PlaySong(randomIndex);
        }
    }

    public void StopSong()
    {
        audioSource.Stop();
        ClearAllRipples();
    }

    void ClearAllRipples()
    {
        foreach (Ripple ripple in activeRipples)
        {
            if (ripple.meshObject != null)
                DestroyImmediate(ripple.meshObject);
        }
        activeRipples.Clear();
    }

    // Context menu for testing
    [ContextMenu("Play First Song")]
    void PlayFirstSongContext()
    {
        if (songs != null && songs.Length > 0)
            PlaySong(0);
    }

    [ContextMenu("Clear All Ripples")]
    void ClearRipplesContext()
    {
        ClearAllRipples();
    }

    // Gizmos for visualization
    void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.yellow;
        DrawWireCircle(transform.position, baseRadius);

        Gizmos.color = Color.red;
        DrawWireCircle(transform.position, maxRadius);

        // Draw ripple positions
        if (activeRipples != null)
        {
            Gizmos.color = Color.cyan;
            foreach (Ripple ripple in activeRipples)
            {
                if (ripple.currentRadius > 0)
                {
                    DrawWireCircle(transform.position, ripple.currentRadius);
                }
            }
        }
    }

    // Helper for drawing a wire circle in the Scene view
    void DrawWireCircle(Vector3 center, float radius, int segments = 64)
    {
        float angleStep = 360f / segments;
        Vector3 prevPoint = center + new Vector3(Mathf.Cos(0), 0, Mathf.Sin(0)) * radius;
        for (int i = 1; i <= segments; i++)
        {
            float angle = i * angleStep * Mathf.Deg2Rad;
            Vector3 nextPoint = center + new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * radius;
            Gizmos.DrawLine(prevPoint, nextPoint);
            prevPoint = nextPoint;
        }
    }
}