# Mobile Push Notifications Integration Guide

This guide explains how to integrate push notifications for iOS and Android mobile apps with the Sheriff Sales platform.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Android (FCM) Setup](#android-fcm-setup)
3. [iOS (APNs) Setup](#ios-apns-setup)
4. [API Reference](#api-reference)
5. [Mobile App Code Examples](#mobile-app-code-examples)
6. [Testing](#testing)

---

## Quick Start

### 1. Server-Side Configuration

Add the following to your `.env` file:

```bash
# For Android (FCM)
FCM_SERVER_KEY=AAAAbbbbCCCCdddd...

# For iOS (APNs) - Token Auth (Recommended)
APNS_AUTH_KEY_PATH=/path/to/AuthKey_ABC123.p8
APNS_KEY_ID=ABC123
APNS_TEAM_ID=DEF456
APNS_BUNDLE_ID=com.yourcompany.yourapp
APNS_USE_SANDBOX=true  # true for dev, false for prod
```

### 2. Install Python Dependencies

```bash
pip install apns2 pyjwt[crypto] httpx
```

### 3. Run the Background Worker

```bash
# Run once (for testing)
python -m webhook_server.push_notification_worker --once

# Run continuously
python -m webhook_server.push_notification_worker --interval 30
```

---

## Android (FCM) Setup

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing
3. Add an Android app with your package name (e.g., `com.yourcompany.yourapp`)
4. Download `google-services.json` and add to your Android app

### Step 2: Get Server Key

1. Go to Project Settings > Cloud Messaging
2. Copy the **Server Key** (not the Sender ID)
3. Add to `.env`: `FCM_SERVER_KEY=AAAAbbbbCCCC...`

### Step 3: Android App Integration

```kotlin
// MainActivity.kt
import com.google.firebase.messaging.FirebaseMessaging

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Get FCM token
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) {
                val token = task.result
                Log.d("FCM", "Token: $token")
                registerTokenWithServer(token)
            }
        }
    }

    private fun registerTokenWithServer(token: String) {
        // Your user ID from auth
        val userId = getCurrentUserId()

        val json = JSONObject().apply {
            put("user_id", userId)
            put("device_token", token)
            put("platform", "android")
            put("device_info", JSONObject().apply {
                put("model", Build.MODEL)
                put("os_version", Build.VERSION.RELEASE)
            })
        }

        val request = JsonObjectRequest(
            Request.Method.POST,
            "https://your-server.com/api/deal-intelligence/notifications/register",
            json,
            { response -> Log.d("API", "Token registered") },
            { error -> Log.e("API", "Error: ${error.message}") }
        )

        Volley.newRequestQueue(this).add(request)
    }
}
```

---

## iOS (APNs) Setup

### Step 1: Create Push Notification Key

1. Go to [Apple Developer](https://developer.apple.com/account/resources/authkeys/list)
2. Click **+** to create a new key
3. Select **Apple Push Notifications service (APNs)**
4. Download the `.p8` key file (you can only download it once!)
5. Note the **Key ID** (10-character string)
6. Note your **Team ID** (10-character string)

### Step 2: Configure App Capabilities

1. In Xcode, go to your Target > Signing & Capabilities
2. Add **Push Notifications** capability
3. Note your **Bundle ID** (e.g., `com.yourcompany.yourapp`)

### Step 3: Server Configuration

Place the `.p8` key file in a secure location and set environment variables:

```bash
APNS_AUTH_KEY_PATH=/secrets/AuthKey_ABC123.p8
APNS_KEY_ID=ABC123
APNS_TEAM_ID=DEF456
APNS_BUNDLE_ID=com.yourcompany.yourapp
APNS_USE_SANDBOX=true  # true for development
```

### Step 4: iOS App Integration (Swift)

```swift
// AppDelegate.swift
import UserNotifications

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        // Request notification permission
        UNUserNotificationCenter.current().requestAuthorization(
            options: [.alert, .sound, .badge]
        ) { granted, error in
            if granted {
                DispatchQueue.main.async {
                    application.registerForRemoteNotifications()
                }
            }
        }

        return true
    }

    // Called when token is received
    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        let tokenParts = deviceToken.map { data in String(format: "%02.2hhx", data) }
        let token = tokenParts.joined()
        print("APNs Token: \(token)")
        registerTokenWithServer(token)
    }

    func registerTokenWithServer(_ token: String) {
        guard let userId = getCurrentUserId() else { return }
        guard let url = URL(string: "https://your-server.com/api/deal-intelligence/notifications/register") else { return }

        let request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "user_id": userId,
            "device_token": token,
            "platform": "ios",
            "device_info": [
                "model": UIDevice.current.model,
                "os_version": UIDevice.current.systemVersion
            ]
        ]

        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error registering token: \(error)")
            } else {
                print("Token registered successfully")
            }
        }.resume()
    }

    func getCurrentUserId() -> String? {
        // Return your authenticated user ID
        return UserDefaults.standard.string(forKey: "userId")
    }
}
```

---

## API Reference

### Register Device Token

**Endpoint:** `POST /api/deal-intelligence/notifications/register`

**Request Body:**
```json
{
  "user_id": "uuid-of-user",
  "device_token": "device-token-from-fcm-or-apns",
  "platform": "android | ios | web",
  "device_info": {
    "model": "iPhone 14",
    "os_version": "16.0",
    "app_version": "1.0.0"
  }
}
```

**Response:**
```json
{
  "id": 123,
  "user_id": "uuid-of-user",
  "platform": "ios",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Send Notification (Server-Side)

**Endpoint:** `POST /api/deal-intelligence/notifications/send`

**Request Body:**
```json
{
  "user_id": "uuid-of-user",
  "notification_type": "hot_deal",
  "title": "New Hot Deal!",
  "body": "123 Main St just listed - 40% below market!",
  "property_id": 12345,
  "deep_link": "myapp://property/12345",
  "priority": "high"
}
```

### Get Notification History

**Endpoint:** `GET /api/deal-intelligence/notifications/{user_id}`

**Response:**
```json
{
  "notifications": [
    {
      "id": 1,
      "title": "New Hot Deal!",
      "body": "123 Main St just listed...",
      "created_at": "2024-01-01T00:00:00Z",
      "opened_at": "2024-01-01T00:05:00Z"
    }
  ]
}
```

---

## Mobile App Code Examples

### React Native

```typescript
import { messaging } from '@react-native-firebase/messaging';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// Request permission and get token
async function registerPushNotifications(userId: string) {
  const authStatus = await messaging().requestPermission();
  const enabled = authStatus === messaging.AuthorizationStatus.AUTHORIZED;

  if (!enabled) {
    console.log('Push notifications not enabled');
    return;
  }

  const token = await messaging().getToken();
  console.log('FCM Token:', token);

  // Register with server
  await fetch('https://your-server.com/api/deal-intelligence/notifications/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      device_token: token,
      platform: Platform.OS,
      device_info: {
        model: Device.model,
        os_version: Device.osVersion,
      },
    }),
  });
}

// Listen for incoming messages
messaging().onMessage(async remoteMessage => {
  console.log('Foreground message:', remoteMessage);
  // Handle in-app notification
});

// Listen for background/tap messages
messaging().onNotificationOpenedApp(remoteMessage => {
  console.log('Notification opened:', remoteMessage);
  // Navigate to property
  if (remoteMessage.data?.property_id) {
    navigation.navigate('Property', { id: remoteMessage.data.property_id });
  }
});
```

### Flutter

```dart
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

class PushNotificationService {
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;

  Future<void> initialize(String userId) async {
    // Request permission
    NotificationSettings settings = await _fcm.requestPermission();
    if (settings.authorizationStatus != AuthorizationStatus.authorized) {
      return;
    }

    // Get token
    String? token = await _fcm.getToken();
    await _registerToken(userId, token!);

    // Handle incoming messages
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      _showNotification(message);
    });

    // Handle tap on notification
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      _navigateToProperty(message.data['property_id']);
    });
  }

  Future<void> _registerToken(String userId, String token) async {
    final response = await http.post(
      Uri.parse('https://your-server.com/api/deal-intelligence/notifications/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'user_id': userId,
        'device_token': token,
        'platform': Platform.isIOS ? 'ios' : 'android',
      }),
    );
  }

  void _showNotification(RemoteMessage message) {
    flutterLocalNotificationsPlugin.show(
      0,
      message.notification?.title,
      message.notification?.body,
      NotificationDetails(...),
    );
  }
}
```

---

## Testing

### Test with cURL

```bash
# Register a test token
curl -X POST http://localhost:8080/api/deal-intelligence/notifications/register \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-uuid",
    "device_token": "test-token",
    "platform": "android"
  }'

# Send a test notification
curl -X POST http://localhost:8080/api/deal-intelligence/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-uuid",
    "notification_type": "hot_deal",
    "title": "Test Notification",
    "body": "This is a test from the server"
  }'

# Process notification queue
curl -X POST http://localhost:8080/api/deal-intelligence/notifications/process-queue
```

### Test with Real Devices

1. **Android:**
   - Deploy app to device/emulator
   - Check logcat for FCM token: `adb logcat | grep FCM`
   - Use the token to send test notification

2. **iOS:**
   - Deploy app to physical device (push notifications don't work in simulator)
   - Check Xcode console for APNs token
   - Use the token to send test notification

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| FCM returns "InvalidRegistration" | Token expired - re-register from device |
| APNs returns "BadDeviceToken" | Using production token in sandbox (or vice versa) |
| Notifications not received | Check device notification permissions are granted |
| Background worker not processing | Ensure worker process is running |

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Notification Queue

```sql
-- View pending notifications
SELECT * FROM push_notification_queue WHERE status = 'pending';

-- View recent history
SELECT * FROM push_notification_history ORDER BY created_at DESC LIMIT 10;

-- View active tokens
SELECT * FROM mobile_push_tokens WHERE is_active = true;
```

---

## Production Deployment

### 1. Use Production APNs

```bash
APNS_USE_SANDBOX=false
```

### 2. Run Worker as Systemd Service

```ini
# /etc/systemd/system/push-worker.service
[Unit]
Description=Push Notification Worker
After=network.target

[Service]
User=appuser
WorkingDirectory=/path/to/app
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m webhook_server.push_notification_worker
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. Set Up Monitoring

- Monitor queue depth
- Alert on high failure rates
- Track delivery success rate
