using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ScaleFromAudioClip : MonoBehaviour
{
    public AudioSource audioSource;
    public Vector3 minscale;
    public Vector3 maxscale;

    public AudioLoudnessDetection detector;
    // Start is called before the first frame update
    public float loudnessSensitivity = 1;
    public float threshold = 0.1f;
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        float loudness = detector.GetLoudnessFromAudioClip(audioSource.clip, audioSource.timeSamples)*loudnessSensitivity;

        if (loudness < threshold)
        {
            loudness = 0;
        }
        else
        {
            loudness = Mathf.Clamp(loudness, 0, 1);
        }
        transform.localScale = Vector3.Lerp(minscale, maxscale, loudness);
    }
}
