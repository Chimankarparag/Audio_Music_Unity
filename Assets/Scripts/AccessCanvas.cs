using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI; // Needed for Button

public class AccessCanvas : MonoBehaviour
{
    private GameObject musicUI;

    void Start()
    {
        // musicUI = GameObject.Find("MusicUI");
        // if (musicUI != null)
        // {
        //     musicUI.SetActive(false); // Start with UI disabled
        // }
        // else
        // {
        //     Debug.LogWarning("MusicUI GameObject not found in the scene.");
        // }
    }

    // private void OnTriggerEnter(Collider other)
    // {
    //     if (other.CompareTag("Player") && musicUI != null)
    //     {
    //         musicUI.SetActive(true);
    //     }
    // }

    // private void OnTriggerExit(Collider other)
    // {
    //     if (other.CompareTag("Player") && musicUI != null)
    //     {
    //         musicUI.SetActive(false);
    //     }
    // }
}
