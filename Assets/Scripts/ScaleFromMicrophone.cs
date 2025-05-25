using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ScaleFromMicrophone : MonoBehaviour
{
    // public AudioSource audioSource;
    public Vector3 minscale;
    public Vector3 maxscale;

    public AudioLoudnessDetection detector;
    // Start is called before the first frame update
    public float loudnessSensitivity = 100;
    public float threshold = 0.1f;
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        float loudness = detector.GetLoudnessFromMicrophone()*loudnessSensitivity;
        // Debug.Log("Loudness: " + loudness);

        if (loudness < threshold)
        {
            loudness = 0;
        }
        GetComponent<Renderer>().material.color = Color.Lerp(Color.black, Color.white, loudness);

        transform.localScale = Vector3.Lerp(minscale, maxscale, loudness);
    }
}
