using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerController : MonoBehaviour
{
    public float moveSpeed = 5f;
    public float lookSpeed = 3f;

    private Vector2 movementInput;
    private Vector2 lookInput;
    private CharacterController controller;
    private float rotationX = 0f;

    [SerializeField] private Transform cameraTransform;

    private void Awake()
    {
        controller = GetComponent<CharacterController>();
        Cursor.lockState = CursorLockMode.None; // Unlock cursor for UI
        Cursor.visible = true;                  // Show cursor for UI
    }

    private void Update()
    {
        // Move the player
        Vector3 move = transform.right * movementInput.x + transform.forward * movementInput.y;
        controller.Move(move * moveSpeed * Time.deltaTime);

        // Rotate the camera/player
        transform.Rotate(Vector3.up * lookInput.x * lookSpeed);

        // Vertical camera rotation (pitch)
        rotationX -= lookInput.y * lookSpeed;
        rotationX = Mathf.Clamp(rotationX, -90f, 90f);
        cameraTransform.localRotation = Quaternion.Euler(rotationX, 0f, 0f);
    }

    // Input System callback
    public void OnMove(InputAction.CallbackContext context)
    {
        movementInput = context.ReadValue<Vector2>();
    }

    public void OnLook(InputAction.CallbackContext context)
    {
        lookInput = context.ReadValue<Vector2>();
    }
}
