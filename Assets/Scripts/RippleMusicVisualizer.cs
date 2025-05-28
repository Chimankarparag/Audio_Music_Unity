using UnityEngine;
using System.Collections.Generic;

[RequireComponent(typeof(AudioSource))]
public class RippleMusicVisualiser : MonoBehaviour
{
    [Header("Audio Settings")]
    public AudioSource audioSource;
    public AudioClip[] songs;
    [Range(6, 13)]
    public int fftSize = 10; // 2^10 = 1024 samples

    [Header("Ripple Settings")]
    [Range(5.0f, 50.0f)]
    public float maxRadius = 25f;
    [Range(0.5f, 3.0f)]
    public float rippleSpeed = 1.5f;
    [Range(0.1f, 2.0f)]
    public float rippleLifetime = 1.0f;
    [Range(3, 8)]
    public int maxConcurrentRipples = 5;

    [Header("Waveform Settings")]
    [Range(16, 128)]
    public int circleResolution = 64;
    [Range(8, 64)]
    public int radialSegments = 32;
    [Range(0.1f, 10.0f)]
    public float amplitudeMultiplier = 8.0f;
    [Range(0.1f, 10.0f)]
    public float baseRadius = 2.0f;
    [Range(1, 5)]
    public int waveComplexity = 3;
    [Range(0.1f, 2f)]
    public float waveFrequency = 1f;
    [Range(0.1f, 1f)]
    public float waveDepth = 0.5f;

    [Header("Visual Settings")]
    public Material rippleMaterial;
    public Gradient rippleColorGradient;
    [Range(0.1f, 1.0f)]
    public float rippleInterval = 0.2f;
    public bool useWireframe = false;

    [Header("Audio Analysis")]
    [Range(0.1f, 0.9f)]
    public float smoothingFactor = 0.7f;
    [Range(1.0f, 20.0f)]
    public float sensitivityMultiplier = 8.0f;

    private float[] spectrumData;
    private float currentAmplitude;
    private float smoothedAmplitude;
    private List<Ripple> activeRipples;
    private float lastRippleTime;
    private int sampleRate;

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

        public float GetAge() => Time.time - birthTime;
        public float GetLifeProgress(float maxLifetime) => Mathf.Clamp01(GetAge() / maxLifetime);
    }

    void Start()
    {
        InitializeAudio();
        InitializeRippleSystem();
        if (songs != null && songs.Length > 0) PlaySong(0);
    }

    void InitializeAudio()
    {
        if (audioSource == null) audioSource = GetComponent<AudioSource>();
        sampleRate = AudioSettings.outputSampleRate;
        spectrumData = new float[(int)Mathf.Pow(2, fftSize)];
    }

    void InitializeRippleSystem()
    {
        activeRipples = new List<Ripple>();
        
        if (rippleMaterial == null)
        {
            rippleMaterial = new Material(Shader.Find("Standard"));
            rippleMaterial.color = Color.cyan;
            rippleMaterial.SetFloat("_Metallic", 0.5f);
            rippleMaterial.SetFloat("_Smoothness", 0.8f);
        }

        if (rippleColorGradient == null)
        {
            rippleColorGradient = new Gradient();
            rippleColorGradient.SetKeys(
                new GradientColorKey[] {
                    new GradientColorKey(Color.red, 0.0f),
                    new GradientColorKey(Color.yellow, 0.5f),
                    new GradientColorKey(Color.blue, 1.0f)
                },
                new GradientAlphaKey[] {
                    new GradientAlphaKey(1.0f, 0.0f),
                    new GradientAlphaKey(0.0f, 1.0f)
                }
            );
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
        audioSource.GetSpectrumData(spectrumData, 0, FFTWindow.BlackmanHarris);
        currentAmplitude = 0f;
        int bassRange = Mathf.Min(spectrumData.Length / 4, 256);

        for (int i = 0; i < bassRange; i++)
        {
            float weight = 1f - (float)i / bassRange;
            weight *= weight;
            currentAmplitude += spectrumData[i] * weight;
        }

        currentAmplitude *= sensitivityMultiplier;
        smoothedAmplitude = (smoothingFactor * smoothedAmplitude) + ((1f - smoothingFactor) * currentAmplitude);
    }

    void CheckForNewRipple()
    {
        if (Time.time - lastRippleTime >= rippleInterval && smoothedAmplitude > 0.05f)
        {
            Color rippleColor = rippleColorGradient.Evaluate(Mathf.Clamp01(smoothedAmplitude));
            CreateNewRipple(smoothedAmplitude, rippleColor);
            lastRippleTime = Time.time;
        }
    }

    void CreateNewRipple(float amplitude, Color color)
    {
        if (activeRipples.Count >= maxConcurrentRipples)
        {
            Ripple oldestRipple = activeRipples[0];
            if (oldestRipple.meshObject != null) DestroyImmediate(oldestRipple.meshObject);
            activeRipples.RemoveAt(0);
        }

        Ripple newRipple = new Ripple(amplitude, color);
        newRipple.meshObject = new GameObject($"Ripple_{Time.time:F2}");
        newRipple.meshObject.transform.SetParent(transform, false);

        newRipple.meshFilter = newRipple.meshObject.AddComponent<MeshFilter>();
        newRipple.meshRenderer = newRipple.meshObject.AddComponent<MeshRenderer>();

        Material instanceMaterial = new Material(rippleMaterial) { color = color };
        if (useWireframe) ConfigureWireframeMaterial(instanceMaterial);
        newRipple.meshRenderer.material = instanceMaterial;

        newRipple.mesh = CreateWaveformMesh(0f, amplitude);
        newRipple.meshFilter.mesh = newRipple.mesh;

        activeRipples.Add(newRipple);
    }

    void ConfigureWireframeMaterial(Material mat)
    {
        mat.SetFloat("_Mode", 1);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3000;
    }

    Mesh CreateWaveformMesh(float radius, float amplitude)
    {
        Mesh mesh = new Mesh { name = "WaveformRipple" };
        List<Vector3> vertices = new List<Vector3>();
        List<int> triangles = new List<int>();
        List<Vector2> uvs = new List<Vector2>();

        // Center vertex
        vertices.Add(Vector3.zero);
        uvs.Add(new Vector2(0.5f, 0.5f));

        for (int ring = 1; ring <= radialSegments; ring++)
        {
            float ringProgress = (float)ring / radialSegments;
            float ringRadius = Mathf.Lerp(baseRadius, radius, ringProgress);

            for (int i = 0; i < circleResolution; i++)
            {
                float angle = i * Mathf.PI * 2f / circleResolution;
                Vector3 pos = new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * ringRadius;
                
                // Waveform calculation
                float normalizedRadius = ringRadius / Mathf.Max(radius, baseRadius);
                float baseHeight = amplitude * (1f - normalizedRadius * normalizedRadius);
                float wavePattern = Mathf.Sin(normalizedRadius * waveFrequency * waveComplexity * Mathf.PI);
                wavePattern = Mathf.Clamp(wavePattern, -waveDepth, 1f);
                pos.y = baseHeight * (0.5f + 0.5f * wavePattern);
                pos.y = Mathf.Max(0, pos.y);

                vertices.Add(pos);
                uvs.Add(new Vector2(pos.x / maxRadius + 0.5f, pos.z / maxRadius + 0.5f));
            }
        }

        CreateWaveformTriangles(triangles, circleResolution, radialSegments);

        mesh.SetVertices(vertices);
        mesh.SetTriangles(triangles, 0);
        mesh.SetUVs(0, uvs);
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        return mesh;
    }

    void CreateWaveformTriangles(List<int> triangles, int resolution, int segments)
    {
        // Center to first ring
        for (int i = 0; i < resolution; i++)
        {
            triangles.Add(0);
            triangles.Add(i + 1);
            triangles.Add((i + 1) % resolution + 1);
        }

        // Between rings
        for (int ring = 0; ring < segments - 1; ring++)
        {
            int currentStart = ring * resolution + 1;
            int nextStart = (ring + 1) * resolution + 1;

            for (int i = 0; i < resolution; i++)
            {
                int next = (i + 1) % resolution;

                triangles.Add(currentStart + i);
                triangles.Add(nextStart + i);
                triangles.Add(currentStart + next);

                triangles.Add(currentStart + next);
                triangles.Add(nextStart + i);
                triangles.Add(nextStart + next);
            }
        }
    }

    void UpdateRipples()
    {
        foreach (Ripple ripple in activeRipples)
        {
            if (ripple.meshObject == null) continue;

            float lifeProgress = ripple.GetLifeProgress(rippleLifetime);
            ripple.currentRadius = lifeProgress * rippleSpeed * maxRadius;

            if (ripple.currentRadius <= maxRadius)
            {
                UpdateWaveformMesh(ripple.mesh, ripple.currentRadius, ripple.birthAmplitude * (1f - lifeProgress));
                UpdateRippleAppearance(ripple, lifeProgress);
            }
        }
    }

    void UpdateWaveformMesh(Mesh mesh, float radius, float amplitude)
    {
        Vector3[] vertices = mesh.vertices;
        int vertexIndex = 1;

        for (int ring = 1; ring <= radialSegments; ring++)
        {
            float ringProgress = (float)ring / radialSegments;
            float ringRadius = Mathf.Lerp(baseRadius, radius, ringProgress);

            for (int i = 0; i < circleResolution; i++)
            {
                float angle = i * Mathf.PI * 2f / circleResolution;
                Vector3 pos = new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * ringRadius;
                
                float normalizedRadius = ringRadius / Mathf.Max(radius, baseRadius);
                float baseHeight = amplitude * (1f - normalizedRadius * normalizedRadius);
                float wavePattern = Mathf.Sin(normalizedRadius * waveFrequency * waveComplexity * Mathf.PI);
                wavePattern = Mathf.Clamp(wavePattern, -waveDepth, 1f);
                pos.y = baseHeight * (0.5f + 0.5f * wavePattern);
                pos.y = Mathf.Max(0, pos.y);

                vertices[vertexIndex++] = pos;
            }
        }

        mesh.vertices = vertices;
        mesh.RecalculateNormals();
    }

    void UpdateRippleAppearance(Ripple ripple, float lifeProgress)
    {
        Color currentColor = ripple.originalColor;
        currentColor.a = 1f - lifeProgress;
        ripple.meshRenderer.material.color = currentColor;

        if (lifeProgress > 0.7f)
        {
            Material mat = ripple.meshRenderer.material;
            mat.SetFloat("_Mode", 3);
            mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            mat.SetInt("_ZWrite", 0);
            mat.DisableKeyword("_ALPHATEST_ON");
            mat.EnableKeyword("_ALPHABLEND_ON");
            mat.renderQueue = 3000;
        }
    }

    void CleanupOldRipples()
    {
        for (int i = activeRipples.Count - 1; i >= 0; i--)
        {
            Ripple ripple = activeRipples[i];
            if (ripple.GetAge() > rippleLifetime || ripple.currentRadius > maxRadius)
            {
                if (ripple.meshObject != null) DestroyImmediate(ripple.meshObject);
                activeRipples.RemoveAt(i);
            }
        }
    }

    public void PlaySong(int songIndex)
    {
        if (songs != null && songIndex >= 0 && songIndex < songs.Length)
        {
            audioSource.Stop();
            audioSource.clip = songs[songIndex];
            audioSource.Play();
            ClearAllRipples();
        }
    }

    public void PlayRandomSong()
    {
        if (songs != null && songs.Length > 0)
            PlaySong(Random.Range(0, songs.Length));
    }

    public void StopSong()
    {
        audioSource.Stop();
        ClearAllRipples();
    }

    void ClearAllRipples()
    {
        foreach (Ripple ripple in activeRipples)
            if (ripple.meshObject != null) DestroyImmediate(ripple.meshObject);
        activeRipples.Clear();
    }

    [ContextMenu("Play First Song")]
    void PlayFirstSongContext() { if (songs != null && songs.Length > 0) PlaySong(0); }

    [ContextMenu("Clear All Ripples")]
    void ClearRipplesContext() { ClearAllRipples(); }

    void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.yellow;
        DrawWireCircle(transform.position, baseRadius);
        Gizmos.color = Color.red;
        DrawWireCircle(transform.position, maxRadius);

        if (activeRipples != null)
        {
            Gizmos.color = Color.cyan;
            foreach (Ripple ripple in activeRipples)
                if (ripple.currentRadius > 0)
                    DrawWireCircle(transform.position, ripple.currentRadius);
        }
    }

    void DrawWireCircle(Vector3 center, float radius, int segments = 64)
    {
        Vector3 prevPoint = center + new Vector3(Mathf.Cos(0), 0, Mathf.Sin(0)) * radius;
        for (int i = 1; i <= segments; i++)
        {
            float angle = i * Mathf.PI * 2f / segments;
            Vector3 nextPoint = center + new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * radius;
            Gizmos.DrawLine(prevPoint, nextPoint);
            prevPoint = nextPoint;
        }
    }
}