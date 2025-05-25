using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RecordAudio : MonoBehaviour
{
    private AudioClip microphoneClip;
    [SerializeField] AudioSource audioSource;
    public void StartRecording()
    {
        string device = Microphone.devices[0];
        Debug.Log("Using microphone: " + device);
        int sampleRate = AudioSettings.outputSampleRate;
        int lengthSec = 100;
        microphoneClip = Microphone.Start(device, false, lengthSec, sampleRate);
        
    }

    public void PlayRecording()
    {
        audioSource.clip = microphoneClip;
        audioSource.Play();
    }

    // Update is called once per frame
    public void StopRecording()
    {
        Microphone.End(Microphone.devices[0]);
        Debug.Log("Recording stopped.");
    }
}
