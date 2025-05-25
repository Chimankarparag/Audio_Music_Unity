using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Audio;

public class AudioLoudnessDetection : MonoBehaviour
{
    public int sampleWindow = 64;
    private AudioClip microphoneClip;
    private bool microphoneInitialized = false;

    void Start()
    {
        if (Microphone.devices.Length == 0)
        {
            Debug.LogWarning("No microphone detected! Disabling ScaleFromMicrophone script.");
            return;
        }
        MicrophoneToAudioClip();
    }

    void Update()
    {
        // Wait for mic to fill at least 1 second of data
        if (!microphoneInitialized && Microphone.GetPosition(null) > AudioSettings.outputSampleRate / 2)
        {
            microphoneInitialized = true;
            Debug.Log("Microphone initialized.");
        }
    }

    public void MicrophoneToAudioClip()
    {
        string microphoneName = Microphone.devices[0];
        Debug.Log("Using microphone: " + microphoneName);

        int lengthSec = 20; // Length of the clip in seconds
        microphoneClip = Microphone.Start(microphoneName, true, lengthSec, AudioSettings.outputSampleRate);
        Debug.Log("Output Sample Rate: " + AudioSettings.outputSampleRate);
    }


    public float GetLoudnessFromMicrophone()
    {
        if (!microphoneInitialized || microphoneClip == null)
        {
            return 0;
        }

        return GetLoudnessFromAudioClip(microphoneClip, Microphone.GetPosition(null));
    }

    public float GetLoudnessFromAudioClip(AudioClip clip, int clipPosition)
    {
        int startPosition = clipPosition - sampleWindow;

        float[] waveData = new float[sampleWindow];
        clip.GetData(waveData, startPosition);

        float totalLoudness = 0;
        for (int i = 0; i < sampleWindow; i++)
        {
            totalLoudness += Mathf.Abs(waveData[i]);
        }
        return totalLoudness / sampleWindow;
    }

}
