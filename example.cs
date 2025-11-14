using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using System.Text;

[Serializable]
public class ApiResponse
{
    public bool success;
    public string message;
    public string status;
    public string timestamp;
}

[Serializable]
public class VerificationRequest
{
    public string email;
    
    public VerificationRequest(string email)
    {
        this.email = email;
    }
}

[Serializable]
public class CodeVerificationRequest
{
    public string email;
    public string code;
    
    public CodeVerificationRequest(string email, string code)
    {
        this.email = email;
        this.code = code;
    }
}

public class PasswordResetManager : MonoBehaviour
{
    [Header("API Configuration")]
    [SerializeField] private string apiBaseUrl = "http://localhost:5000";
    
    private static PasswordResetManager _instance;
    public static PasswordResetManager Instance
    {
        get
        {
            if (_instance == null)
            {
                GameObject go = new GameObject("PasswordResetManager");
                _instance = go.AddComponent<PasswordResetManager>();
                DontDestroyOnLoad(go);
            }
            return _instance;
        }
    }
    
    void Awake()
    {
        if (_instance != null && _instance != this)
        {
            Destroy(gameObject);
            return;
        }
        _instance = this;
        DontDestroyOnLoad(gameObject);
    }
    
    /// <summary>
    /// Send password reset verification code to email
    /// </summary>
    /// <param name="email">User email</param>
    /// <param name="callback">Callback with success status and message</param>
    public void SendVerificationEmail(string email, Action<bool, string> callback)
    {
        StartCoroutine(SendVerificationEmailCoroutine(email, callback));
    }
    
    private IEnumerator SendVerificationEmailCoroutine(string email, Action<bool, string> callback)
    {
        string url = $"{apiBaseUrl}/send_verification";
        VerificationRequest requestData = new VerificationRequest(email);
        
        string jsonData = JsonUtility.ToJson(requestData);
        
        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                ApiResponse response = JsonUtility.FromJson<ApiResponse>(request.downloadHandler.text);
                callback?.Invoke(response.success, response.message);
            }
            else
            {
                Debug.LogError($"Error sending verification email: {request.error}");
                callback?.Invoke(false, $"Network error: {request.error}");
            }
        }
    }
    
    /// <summary>
    /// Verify the reset code sent to email
    /// </summary>
    /// <param name="email">User email</param>
    /// <param name="code">Verification code</param>
    /// <param name="callback">Callback with success status and message</param>
    public void VerifyResetCode(string email, string code, Action<bool, string> callback)
    {
        StartCoroutine(VerifyResetCodeCoroutine(email, code, callback));
    }
    
    private IEnumerator VerifyResetCodeCoroutine(string email, string code, Action<bool, string> callback)
    {
        string url = $"{apiBaseUrl}/verify_code";
        CodeVerificationRequest requestData = new CodeVerificationRequest(email, code);
        
        string jsonData = JsonUtility.ToJson(requestData);
        
        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                ApiResponse response = JsonUtility.FromJson<ApiResponse>(request.downloadHandler.text);
                callback?.Invoke(response.success, response.message);
            }
            else
            {
                Debug.LogError($"Error verifying code: {request.error}");
                callback?.Invoke(false, $"Network error: {request.error}");
            }
        }
    }
    
    /// <summary>
    /// Check if the service is healthy
    /// </summary>
    /// <param name="callback">Callback with health status</param>
    public void CheckHealth(Action<bool, string> callback)
    {
        StartCoroutine(CheckHealthCoroutine(callback));
    }
    
    private IEnumerator CheckHealthCoroutine(Action<bool, string> callback)
    {
        string url = $"{apiBaseUrl}/health";
        
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                ApiResponse response = JsonUtility.FromJson<ApiResponse>(request.downloadHandler.text);
                bool isHealthy = response.status == "success";
                callback?.Invoke(isHealthy, response.message ?? "Service is healthy");
            }
            else
            {
                callback?.Invoke(false, $"Health check failed: {request.error}");
            }
        }
    }
}

// Example usage in another script
public class PasswordResetUI : MonoBehaviour
{
    [SerializeField] private string userEmail;
    
    public void OnResetPasswordButtonClick()
    {
        PasswordResetManager.Instance.SendVerificationEmail(userEmail, (success, message) =>
        {
            if (success)
            {
                Debug.Log("Verification email sent successfully");
                // Show success UI
            }
            else
            {
                Debug.LogError($"Failed to send email: {message}");
                // Show error UI
            }
        });
    }
    
    public void OnVerifyCodeButtonClick(string code)
    {
        PasswordResetManager.Instance.VerifyResetCode(userEmail, code, (success, message) =>
        {
            if (success)
            {
                Debug.Log("Code verified successfully");
                // Proceed with password reset
            }
            else
            {
                Debug.LogError($"Code verification failed: {message}");
                // Show error message
            }
        });
    }
}