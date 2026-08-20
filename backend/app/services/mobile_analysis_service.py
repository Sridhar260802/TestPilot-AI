"""
Mobile App Testing engine.

Runs real static analysis against an uploaded .apk (Android) or .ipa (iOS)
file - no emulator/device needed for the static pass. Depth of the scan is
controlled by the user's plan, same pattern as the website testing services:

    basic     -> Android only. Package/manifest overview + a handful of
                 high-signal security flags (debuggable, backup, cleartext
                 traffic, dangerous permissions), plus a lightweight
                 permission audit and deep-link scheme count.
    standard  -> Android AND iOS. Adds exported-component analysis,
                 App Transport Security / network-security-config checks,
                 permission risk breakdown, iOS usage-description audit,
                 plus report-shape additions: Executive Summary, Risk
                 Distribution, App Architecture, Storage Security (basic
                 heuristics), Authentication (basic heuristics),
                 Accessibility (basic heuristics), Performance overview,
                 a lightweight Deep Link inventory, and a basic-tier AI
                 root-cause + fix recommendation per issue (title/severity
                 level, no deep KB lookup - see premium for the full
                 version).
    premium   -> Everything in standard, plus a deep security pass:
                 hardcoded secret / API-key scanning, weak-crypto usage
                 heuristics, native library / embedded-framework inventory,
                 signing-certificate inspection (Android, incl. expiry) /
                 provisioning-profile inspection (iOS, incl. expiry),
                 WebView JS-bridge exposure, SSL/TLS pinning & trust-manager
                 bypass detection, root/jailbreak & anti-tamper protection
                 coverage, third-party SDK fingerprinting with known-CVE
                 matching, deep-link (custom URL scheme) hijack exposure,
                 full Storage Security audit, full Authentication audit, a
                 Dynamic Test Results / Crash-ANR / Screenshots section
                 (populated only when a dynamic run was actually supplied -
                 this module is static-analysis-only), full AI-style
                 root-cause + fix recommendations per issue (deterministic
                 KB lookup), a remediation priority queue, a consolidated
                 Data Leakage Risk summary, and a weighted Final Score.

NOTE: this module only computes what's listed above. It does NOT perform
dynamic testing, Appium automation, AI test generation, visual regression,
fuzz testing, or runtime network testing at any depth - those require an
actual device/emulator session and are out of scope for a static analyzer.
Any product/marketing copy claiming this engine performs them is wrong;
correct it rather than the code.

Android parsing uses androguard (real manifest/dex/cert parsing, not a
hand-rolled binary-XML reader). iOS parsing uses the stdlib's plistlib,
which natively reads both XML and binary Info.plist files.
"""

from __future__ import annotations

import os
import re
import sys
import plistlib
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# androguard is very chatty on DEBUG/INFO by default (loguru) - quiet it
# down to warnings so a normal API request doesn't spam server logs.
try:
    from loguru import logger as _loguru_logger
    _loguru_logger.remove()
    _loguru_logger.add(sys.stderr, level="WARNING")
except Exception:
    pass

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

# Protection-level "dangerous" permissions (AOSP list, abbreviated to the
# ones users actually recognize/care about) - used to flag privacy-sensitive
# access at a glance instead of dumping 40 raw permission strings.
DANGEROUS_PERMISSIONS = {
    "android.permission.READ_CONTACTS": "Read contacts",
    "android.permission.WRITE_CONTACTS": "Modify contacts",
    "android.permission.CAMERA": "Use camera",
    "android.permission.RECORD_AUDIO": "Record audio / microphone",
    "android.permission.ACCESS_FINE_LOCATION": "Precise location",
    "android.permission.ACCESS_COARSE_LOCATION": "Approximate location",
    "android.permission.ACCESS_BACKGROUND_LOCATION": "Background location",
    "android.permission.READ_SMS": "Read SMS messages",
    "android.permission.SEND_SMS": "Send SMS messages",
    "android.permission.RECEIVE_SMS": "Receive SMS messages",
    "android.permission.READ_CALL_LOG": "Read call log",
    "android.permission.WRITE_CALL_LOG": "Modify call log",
    "android.permission.CALL_PHONE": "Place phone calls",
    "android.permission.READ_PHONE_STATE": "Read phone state / identifiers",
    "android.permission.READ_EXTERNAL_STORAGE": "Read device storage",
    "android.permission.WRITE_EXTERNAL_STORAGE": "Write device storage",
    "android.permission.BODY_SENSORS": "Body sensors",
    "android.permission.GET_ACCOUNTS": "Access device accounts",
    "android.permission.READ_CALENDAR": "Read calendar",
    "android.permission.WRITE_CALENDAR": "Modify calendar",
    "android.permission.POST_NOTIFICATIONS": "Post notifications",
    "android.permission.BLUETOOTH_CONNECT": "Bluetooth device access",
    "android.permission.ACTIVITY_RECOGNITION": "Physical activity tracking",
}

# Coarse risk tier per dangerous permission - drives the Permission Audit
# section's "high/medium/low privacy impact" grouping.
PERMISSION_RISK_TIER = {
    "android.permission.READ_SMS": "High",
    "android.permission.SEND_SMS": "High",
    "android.permission.READ_CALL_LOG": "High",
    "android.permission.WRITE_CALL_LOG": "High",
    "android.permission.ACCESS_BACKGROUND_LOCATION": "High",
    "android.permission.RECORD_AUDIO": "High",
    "android.permission.CAMERA": "High",
    "android.permission.READ_CONTACTS": "Medium",
    "android.permission.WRITE_CONTACTS": "Medium",
    "android.permission.ACCESS_FINE_LOCATION": "Medium",
    "android.permission.READ_PHONE_STATE": "Medium",
    "android.permission.GET_ACCOUNTS": "Medium",
    "android.permission.BODY_SENSORS": "Medium",
    "android.permission.CALL_PHONE": "Medium",
}

# Regex signatures for secrets that commonly get baked into a build by
# mistake. Deliberately generic/high-signal patterns only - this is a
# defensive linter, not an exploit tool.
SECRET_PATTERNS = [
    ("AWS Access Key",       re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret Key",       re.compile(r"(?i)aws(.{0,20})?(secret|access).{0,3}key(.{0,3})?[\"'\s:=]{1,4}[0-9a-zA-Z/+]{40}")),
    ("Google API Key",       re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Firebase URL",         re.compile(r"[a-z0-9-]+\.firebaseio\.com")),
    ("Slack Token",          re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,48}")),
    ("Stripe Live Key",      re.compile(r"sk_live_[0-9a-zA-Z]{16,}")),
    ("Generic Bearer/API Key", re.compile(r"(?i)(api[_-]?key|secret|token)[\"'\s]*[:=][\"'\s]*[0-9a-zA-Z\-_]{16,}")),
    ("Private Key Block",    re.compile(r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----")),
    ("Basic Auth in URL",    re.compile(r"https?://[^/\s:]+:[^/\s@]+@")),
]

WEAK_CRYPTO_PATTERNS = [
    ("MD5",  re.compile(r"\bMD5\b")),
    ("SHA1", re.compile(r"\bSHA-?1\b")),
    ("DES",  re.compile(r"\bDES(?!ede)\b|DESede\b")),
    ("RC4",  re.compile(r"\bRC4\b")),
    ("ECB mode", re.compile(r"/ECB/|Cipher\.getInstance\([\"']AES/ECB")),
    ("Hardcoded IV/Key hint", re.compile(r"(?i)(iv|key)\s*=\s*[\"'][0-9a-fA-F]{16,}[\"']")),
]

# --------------------------------------------------------------------- #
# Premium-only code-level pattern groups (Android)                      #
# --------------------------------------------------------------------- #

WEBVIEW_RISK_PATTERNS = [
    ("addJavascriptInterface() bridge", re.compile(r"addJavascriptInterface")),
    ("JavaScript enabled on WebView", re.compile(r"setJavaScriptEnabled")),
    ("WebView file-access enabled", re.compile(r"setAllowFileAccess(?:FromFileURLs)?")),
    ("WebView universal file access", re.compile(r"setAllowUniversalAccessFromFileURLs")),
    ("Mixed-content allowed in WebView", re.compile(r"setMixedContentMode")),
]

SSL_BYPASS_PATTERNS = [
    ("Custom TrustManager (possible cert bypass)", re.compile(r"X509TrustManager")),
    ("checkServerTrusted overridden", re.compile(r"checkServerTrusted")),
    ("Hostname verification disabled", re.compile(r"ALLOW_ALL_HOSTNAME_VERIFIER|setHostnameVerifier")),
    ("SSLContext with permissive TrustManager", re.compile(r"SSLContext\.getInstance")),
]

SSL_PINNING_EVIDENCE_PATTERNS = [
    ("OkHttp CertificatePinner", re.compile(r"CertificatePinner")),
    ("TrustKit pinning library", re.compile(r"com/datatheorem/android/trustkit|TrustKit")),
    ("Network Security Config pin-set", re.compile(r"<pin-set")),
]

ANTI_TAMPER_PATTERNS = [
    ("RootBeer root-detection library", re.compile(r"RootBeer")),
    ("Manual root-detection check", re.compile(r"isDeviceRooted|checkRootMethod")),
    ("Google Play Integrity / SafetyNet", re.compile(r"SafetyNet|PlayIntegrity|com/google/android/play/core/integrity")),
    ("Frida detection", re.compile(r"frida-server|frida-gadget|isFridaDetected")),
    ("Xposed/Substrate detection", re.compile(r"de/robv/android/xposed|com\.saurik\.substrate")),
    ("Debugger-attach detection", re.compile(r"Debug\.isDebuggerConnected")),
]

# --------------------------------------------------------------------- #
# Exposed URLs / endpoints                                              #
# --------------------------------------------------------------------- #
# http(s) URL extraction from packaged strings (dex string pool, assets,
# config/json files).
#
# IMPORTANT: this is intentionally *tight*, not "anything that isn't a
# quote/space/bracket". Binary files (resources.arsc, compiled binary XML,
# multi-locale string tables) get decoded permissively with
# errors="ignore", so a real URL sitting next to unrelated binary/unicode
# bytes in the string pool would otherwise have those bytes swept into the
# same "match" - producing two failure modes at once:
#   1. Unreadable report rows (garbage suffixes like "■00Onnittelut!%s").
#   2. Duplicate explosion: the SAME real URL (e.g. a deep-link constant
#      referenced once per locale in a strings table) gets a different
#      garbage suffix each time, so naive exact-string dedup treats every
#      occurrence as a "different" URL and the report balloons with dozens
#      of near-identical rows for one endpoint.
# Restricting the post-host character class to legal URI characters
# (RFC 3986 unreserved + reserved sets) makes the match stop cleanly at
# the real end of the URL, which both cleans up display AND fixes the
# dedup (all occurrences of the same real URL now produce the identical
# trimmed string, so they collapse into one entry automatically).
_URI_CHARS = r"A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%"
URL_EXTRACT_PATTERN = re.compile(rf"https?://[A-Za-z0-9](?:[{_URI_CHARS}]){{3,300}}")

# Any of these substrings in the host portion mark a URL as "internal /
# non-production" - staging or debug endpoints are a common source of
# unauthenticated backend exposure once shipped in a release build.
INTERNAL_URL_HINTS = (
    "localhost", "127.0.0.1", "0.0.0.0", "10.", "192.168.", "staging",
    "stage.", "dev.", "-dev.", "debug", "internal", "test.", "-test.",
    "qa.", "uat.", "beta.",
)

IP_HOST_PATTERN = re.compile(r"^\d{1,3}(\.\d{1,3}){3}")

# --------------------------------------------------------------------- #
# Boilerplate / namespace hosts that show up in http(s) URL string      #
# extraction on essentially every build regardless of app-specific      #
# content, and are not app-controlled network endpoints:                #
#   - schemas.android.com / w3.org: XML/AAPT namespace URIs baked into  #
#     every compiled resources.arsc / binary XML by the build tools.    #
#   - slf4j.org: doc-links hardcoded inside the SLF4J logging library's #
#     own error messages, shipped in the .dex of any app pulling it in. #
#   - schemas.microsoft.com / xml.apache.org / ns.adobe.com / schema.org#
#     are the same class of thing from other common namespace/metadata  #
#     sources (MSAL/AppCenter, XML parsers, XMP image metadata, JSON-LD).#
# Filtered out before classification so the Exposed URLs section stays  #
# focused on URLs an app author actually put there.                     #
# --------------------------------------------------------------------- #
NON_ENDPOINT_URL_HOSTS = (
    "schemas.android.com",
    "www.w3.org", "w3.org",
    "www.slf4j.org", "slf4j.org",
    "schemas.microsoft.com",
    "xml.apache.org",
    "ns.adobe.com",
    "schema.org",
    "www.apache.org", "apache.org",  # Apache-2.0 LICENSE text URL, ships in every dependency's NOTICE
    "opensource.org",                 # OSI license URLs, same boilerplate class
)


def _is_boilerplate_host(host: str) -> bool:
    host = host.lower()
    return any(host == h or host.endswith("." + h) for h in NON_ENDPOINT_URL_HOSTS)


def _classify_url(url: str) -> Dict[str, Any]:
    scheme_insecure = url.lower().startswith("http://")
    host = url.split("//", 1)[-1].split("/", 1)[0].split(":")[0].lower()
    is_ip = bool(IP_HOST_PATTERN.match(host))
    is_internal = is_ip or any(hint in host for hint in INTERNAL_URL_HINTS)
    return {
        "url": url,
        "insecure_http": scheme_insecure,
        "host": host,
        "looks_internal_or_debug": is_internal,
    }


DEEPLINK_INDICATOR_PATTERNS = [
    ("Firebase Dynamic Links", re.compile(r"com/google/firebase/dynamiclinks")),
    ("App Links / Branch.io", re.compile(r"io/branch/referral")),
]

# --------------------------------------------------------------------- #
# Storage Security patterns (Android) - premium full audit, standard    #
# gets a lightweight subset via STORAGE_BASIC_PATTERNS below.           #
# --------------------------------------------------------------------- #

STORAGE_RISK_PATTERNS = [
    ("Plaintext SharedPreferences write", re.compile(r"getSharedPreferences|PreferenceManager\.getDefaultSharedPreferences")),
    ("SQLite database usage", re.compile(r"SQLiteOpenHelper|SQLiteDatabase")),
    ("EncryptedSharedPreferences usage", re.compile(r"EncryptedSharedPreferences")),
    ("SQLCipher usage", re.compile(r"net/sqlcipher|SQLCipher")),
    ("External storage write", re.compile(r"getExternalStorageDirectory|getExternalFilesDir")),
    ("World-readable/writable file mode", re.compile(r"MODE_WORLD_READABLE|MODE_WORLD_WRITEABLE")),
    ("Android Keystore usage", re.compile(r"AndroidKeyStore|KeyGenParameterSpec")),
]

STORAGE_BASIC_PATTERNS = [p for p in STORAGE_RISK_PATTERNS if p[0] in (
    "External storage write", "World-readable/writable file mode",
)]

# --------------------------------------------------------------------- #
# Authentication patterns (Android) - premium full audit, standard      #
# gets presence-only biometric/auth-framework detection.                #
# --------------------------------------------------------------------- #

AUTH_RISK_PATTERNS = [
    ("BiometricPrompt / Fingerprint API usage", re.compile(r"BiometricPrompt|FingerprintManager")),
    ("Hardcoded credential-like assignment", re.compile(r"(?i)(password|passwd|pwd)\s*=\s*[\"'][^\"']{3,}[\"']")),
    ("WebView-based login form", re.compile(r"loadUrl\([\"']https?://[^\"']*login")),
    ("OAuth/token storage reference", re.compile(r"(?i)(access_token|refresh_token|session_token)")),
    ("Weak session/token generation (Random)", re.compile(r"java\.util\.Random\(\)")),
]

AUTH_BASIC_PATTERNS = [p for p in AUTH_RISK_PATTERNS if p[0] == "BiometricPrompt / Fingerprint API usage"]

# --------------------------------------------------------------------- #
# Accessibility heuristics (Android)                                    #
# --------------------------------------------------------------------- #

ACCESSIBILITY_PATTERNS = [
    ("contentDescription usage", re.compile(r"contentDescription|setContentDescription")),
    ("Accessibility service reference", re.compile(r"AccessibilityService|AccessibilityNodeInfo")),
    ("importantForAccessibility usage", re.compile(r"importantForAccessibility")),
]

# --------------------------------------------------------------------- #
# Third-party SDK fingerprints + a small static known-CVE reference     #
# table. This is NOT a live feed - it's a short, hand-maintained list   #
# of publicly disclosed issues for common SDK version ranges, used to   #
# flag "worth checking your version" rather than give a definitive      #
# vulnerable/not-vulnerable verdict (we can't always read the exact     #
# SDK version out of a stripped/minified build).                        #
# --------------------------------------------------------------------- #

ANDROID_THIRD_PARTY_SDKS = {
    "com/google/firebase": "Firebase",
    "com/google/android/gms/ads": "Google AdMob",
    "com/facebook/ads": "Meta Audience Network",
    "com/facebook/appevents": "Meta (Facebook) SDK",
    "com/appsflyer": "AppsFlyer",
    "com/adjust/sdk": "Adjust",
    "com/braze": "Braze",
    "com/onesignal": "OneSignal",
    "com/crashlytics": "Firebase Crashlytics",
    "com/bugsnag": "Bugsnag",
    "com/segment/analytics": "Segment",
    "com/mixpanel": "Mixpanel",
    "com/amplitude": "Amplitude",
    "com/unity3d/ads": "Unity Ads",
    "com/applovin": "AppLovin",
    "com/squareup/okhttp": "OkHttp",
    "com/squareup/picasso": "Picasso",
    "com/bumptech/glide": "Glide",
}

# label -> list of {advisory, affected, note}. Deliberately small/illustrative;
# real deployments should wire this to an actual CVE/OSS-vulnerability feed.
KNOWN_SDK_ADVISORIES = {
    "OkHttp": [
        {"advisory": "CVE-2021-0341-class", "affected": "< 3.12.11 / < 3.14.x",
         "note": "Older OkHttp releases had hostname-verification edge cases fixed in later 3.x/4.x lines. Confirm the bundled version is current."},
    ],
    "Picasso": [
        {"advisory": "Unmaintained-library-risk", "affected": "all",
         "note": "Picasso is in maintenance mode upstream; no active security patching. Consider migrating to a maintained image loader."},
    ],
    "Glide": [
        {"advisory": "Disk-cache-permissions-class", "affected": "< 4.9.0",
         "note": "Pre-4.9 Glide releases had disk-cache file permission issues on some OEM skins. Confirm the bundled version is current."},
    ],
}

# --------------------------------------------------------------------- #
# Premium-only code-level pattern groups (iOS)                          #
# --------------------------------------------------------------------- #

JAILBREAK_DETECTION_PATTERNS = [
    ("Cydia path check", re.compile(r"/Applications/Cydia\.app|cydia://")),
    ("MobileSubstrate / tweak injection check", re.compile(r"MobileSubstrate|/Library/MobileSubstrate")),
    ("Suspicious writable-path check", re.compile(r"/private/var/lib/apt|/bin/bash|/usr/sbin/sshd")),
    ("Jailbreak-detection library", re.compile(r"IOSSecuritySuite|DTTJailbreakDetection")),
]

IOS_PINNING_EVIDENCE_PATTERNS = [
    ("TrustKit pinning library", re.compile(r"TrustKit")),
    ("Manual SecTrustEvaluate pinning", re.compile(r"SecTrustEvaluate")),
    ("Alamofire ServerTrustManager pinning", re.compile(r"ServerTrustManager|PinnedCertificatesTrustEvaluator")),
]

IOS_STORAGE_PATTERNS = [
    ("NSUserDefaults usage", re.compile(r"NSUserDefaults|UserDefaults\.standard")),
    ("Keychain usage", re.compile(r"SecItemAdd|SecItemCopyMatching|kSecClass")),
    ("Core Data / SQLite usage", re.compile(r"NSPersistentContainer|sqlite3_open")),
    ("NSFileProtectionNone (no file encryption)", re.compile(r"NSFileProtectionNone")),
]
IOS_STORAGE_BASIC_PATTERNS = [p for p in IOS_STORAGE_PATTERNS if p[0] == "NSFileProtectionNone (no file encryption)"]

IOS_AUTH_PATTERNS = [
    ("LocalAuthentication (Face ID / Touch ID) usage", re.compile(r"LAContext|evaluatePolicy")),
    ("Hardcoded credential-like assignment", re.compile(r"(?i)(password|passwd|pwd)\s*=\s*\"[^\"]{3,}\"")),
    ("OAuth/token reference", re.compile(r"(?i)(access_token|refresh_token|session_token)")),
]
IOS_AUTH_BASIC_PATTERNS = [p for p in IOS_AUTH_PATTERNS if p[0] == "LocalAuthentication (Face ID / Touch ID) usage"]

IOS_THIRD_PARTY_SDKS = {
    "FirebaseCore": "Firebase",
    "FBSDKCoreKit": "Meta (Facebook) SDK",
    "GoogleMobileAds": "Google AdMob",
    "AppsFlyerLib": "AppsFlyer",
    "Adjust": "Adjust",
    "Branch": "Branch.io",
    "OneSignal": "OneSignal",
    "Bugsnag": "Bugsnag",
    "Mixpanel": "Mixpanel",
    "Amplitude": "Amplitude",
    "AppLovinSDK": "AppLovin",
    "Crashlytics": "Firebase Crashlytics",
    "Alamofire": "Alamofire",
}

MAX_SCAN_FILE_SIZE = 15 * 1024 * 1024  # skip scanning inside anything bigger than this per-file
MAX_TOTAL_SCAN_BYTES = 150 * 1024 * 1024  # cap total bytes read for pattern scans

_SEVERITY_PENALTY = {"Critical": 25, "High": 15, "Medium": 8, "Low": 3, "Info": 0}

# Rough "how long will this take to fix" bucket, used by the Remediation
# Priority queue to break ties within the same severity.
_SEVERITY_EFFORT_HINT = {
    "Critical": "Immediate - block release",
    "High": "Fix before next release",
    "Medium": "Fix in upcoming sprint",
    "Low": "Backlog / best-effort",
    "Info": "Informational - no action required",
}

# How many days out from expiry a signing certificate / provisioning
# profile is flagged as "expiring soon" (Medium) vs already-expired
# (Critical, checked separately).
CERT_EXPIRY_WARNING_DAYS = 90
PROVISIONING_EXPIRY_WARNING_DAYS = 30

# Deterministic "AI root cause + fix" knowledge base, keyed by issue title.
# Ships a same-turn recommendation instead of depending on a live model
# call, so report generation stays fast and reproducible; swap the lookup
# for a real LLM call if richer, non-deterministic write-ups are wanted.
ROOT_CAUSE_FIX_KB = {
    "App is debuggable": {
        "root_cause": "The release build was compiled with android:debuggable left at its default/true value, usually because a debug build.gradle flavor leaked into the release variant.",
        "fix": "Set android:debuggable=\"false\" explicitly for release builds and verify with `aapt dump badging` before shipping.",
    },
    "Full app backup is enabled": {
        "root_cause": "android:allowBackup was never set, so it defaults to true and adb/cloud backup can extract app-private storage.",
        "fix": "Set android:allowBackup=\"false\", or scope backups with a android:fullBackupContent XML that excludes sensitive files.",
    },
    "Unprotected exported components": {
        "root_cause": "Components with an <intent-filter> are exported by default on pre-Android-12 targets, and no custom permission was declared to gate access.",
        "fix": "Set android:exported=\"false\" on components that don't need to be reachable from other apps, or add a signature-level custom permission to the ones that do.",
    },
    "Cleartext traffic explicitly allowed": {
        "root_cause": "usesCleartextTraffic=\"true\" was set, likely to support a legacy HTTP endpoint or local dev server that was never removed for release.",
        "fix": "Set usesCleartextTraffic=\"false\" and move any remaining HTTP endpoints to HTTPS; use a Network Security Config to scope narrow exceptions instead of a blanket allow.",
    },
    "Possible hardcoded secrets found": {
        "root_cause": "A credential or API key was embedded directly in source/config/asset files rather than fetched at runtime or injected via a secrets manager / build-time env var.",
        "fix": "Rotate any real credentials immediately, move secrets to a backend-mediated flow or Android Keystore-backed storage, and add a pre-commit secret scanner to catch recurrences.",
    },
    "Weak/legacy cryptographic primitives referenced": {
        "root_cause": "Legacy digest/cipher APIs (MD5, SHA-1, DES, RC4, or ECB mode) are still referenced, often copied from older sample code.",
        "fix": "Migrate hashing to SHA-256 or better, and symmetric encryption to AES-GCM with a properly random IV per operation.",
    },
    "No APK Signature Scheme v2/v3": {
        "root_cause": "The build pipeline only produced a legacy v1 (JAR) signature, typically because a custom signing step bypassed the standard Gradle signing config.",
        "fix": "Enable v2/v3 signing in the signing config (this is the Gradle default since AGP 3.0) and re-sign the release artifact.",
    },
    "WebView exposes a JavaScript bridge": {
        "root_cause": "addJavascriptInterface() is registered on a WebView that also has JavaScript execution enabled, without restricting the WebView to trusted, bundled content.",
        "fix": "Restrict the WebView to a fixed set of trusted origins (WebViewClient.shouldOverrideUrlLoading allow-list), remove the JS interface if not essential, and target API 17+ with @JavascriptInterface-annotated methods only.",
    },
    "Possible SSL/TLS trust validation bypass": {
        "root_cause": "A custom X509TrustManager / hostname verifier was implemented, and a common mistake is leaving the trust checks as no-ops during development and shipping that build.",
        "fix": "Verify the custom TrustManager still calls through to the default trust manager's checks (or implements real pinning), and remove any ALLOW_ALL_HOSTNAME_VERIFIER usage.",
    },
    "No certificate pinning detected": {
        "root_cause": "The app relies solely on the OS trust store with no additional pinning layer (CertificatePinner, TrustKit, or a Network Security Config pin-set).",
        "fix": "Add certificate or public-key pinning for high-value endpoints (auth, payments) using OkHttp's CertificatePinner or a Network Security Config pin-set, with a documented pin-rotation plan.",
    },
    "No root/anti-tamper detection signatures found": {
        "root_cause": "No root-detection, Play Integrity/SafetyNet, or anti-debug library is linked, which is fine for most apps but a gap for high-value targets (payments, DRM).",
        "fix": "If the app handles payments or sensitive data, integrate Play Integrity API and layer in basic root-indicator checks; treat detections as risk signals, not hard blocks.",
    },
    "Unvalidated custom URL scheme(s) exposed": {
        "root_cause": "An exported activity handles a custom (non-https) URL scheme without a signature permission, so any installed app can register the same scheme.",
        "fix": "Migrate security-sensitive deep links to verified Android App Links (https + assetlinks.json), and treat all incoming intent extras/data as untrusted input.",
    },
    "Code does not appear to be obfuscated/minified": {
        "root_cause": "ProGuard/R8 minification and obfuscation are likely disabled for the release build type in build.gradle.",
        "fix": "Enable minifyEnabled true / shrinkResources true for the release build type and validate the app still functions correctly with a ProGuard/R8 keep-rules review.",
    },
    "App Transport Security disabled globally": {
        "root_cause": "NSAllowsArbitraryLoads=true was set app-wide, usually to unblock one legacy HTTP endpoint during development.",
        "fix": "Remove the global exception and add narrowly-scoped NSExceptionDomains entries only for the specific hosts that truly need them, migrating them to HTTPS where possible.",
    },
    "get-task-allow entitlement is enabled": {
        "root_cause": "The embedded provisioning profile was built for development/ad-hoc distribution rather than App Store distribution.",
        "fix": "Re-export/re-sign the build with an App Store distribution provisioning profile, which sets get-task-allow to false.",
    },
    "No jailbreak-detection signatures found": {
        "root_cause": "No jailbreak-detection checks are linked, which is fine for most apps but a gap for apps handling payments or DRM'd content.",
        "fix": "If warranted by the app's risk profile, integrate a maintained jailbreak-detection library (or DeviceCheck/App Attest) and treat detections as a risk signal.",
    },
    "Insecure local data storage detected": {
        "root_cause": "Sensitive-looking data is being written via plain SharedPreferences/NSUserDefaults or an unencrypted SQLite database rather than an encrypted store.",
        "fix": "Move sensitive fields to EncryptedSharedPreferences (Android) / Keychain with appropriate accessibility class (iOS), and encrypt local databases with SQLCipher or Core Data's NSFileProtectionComplete.",
    },
    "Hardcoded credential-like value found": {
        "root_cause": "A string literal matching a password/credential pattern was found directly in code.",
        "fix": "Remove hardcoded credentials, rotate any real ones, and source them from a secure runtime configuration instead.",
    },
    "Very low minimum SDK": {
        "root_cause": "minSdkVersion was set low (below API 23) to maximize device reach, without a compensating security review for the older platform versions that get let in.",
        "fix": "Raise minSdkVersion if analytics show negligible install share on very old Android versions, or explicitly document and test the app against the security gaps present on the versions you still support.",
    },
    "Sensitive permissions requested": {
        "root_cause": "The app declares dangerous-protection-level permissions in its manifest, which is often necessary for legitimate features but expands the app's privacy footprint.",
        "fix": "Confirm each dangerous permission maps to an actual in-app feature, request them at time-of-use rather than all at launch, and remove any that are unused leftovers from removed features.",
    },
    "Internal/staging/debug URL(s) exposed in build": {
        "root_cause": "A staging, debug, or internal-network endpoint got baked into the release build, typically because build-time configuration wasn't swapped from a dev/staging flavor to production before packaging.",
        "fix": "Move environment-specific URLs into build-variant config (not shared source), verify the release build flavor points only at production endpoints, and ensure internal endpoints require authentication even if they do leak.",
    },
    "Plain HTTP URL(s) found in build": {
        "root_cause": "One or more endpoints are still referenced over plain http:// rather than https://, often copied from an old sample or a resource that predates the app's TLS migration.",
        "fix": "Migrate all referenced endpoints to https://, and enforce this going forward with usesCleartextTraffic=\"false\" (Android) or ATS defaults (iOS) so a future regression fails loudly instead of shipping silently.",
    },
    "Third-party SDK(s) with known advisories": {
        "root_cause": "One or more bundled third-party SDKs have publicly documented advisories for older version ranges, and the exact bundled version couldn't be confirmed from the binary alone.",
        "fix": "Confirm the exact SDK versions in your dependency lockfile/build.gradle and upgrade any that fall inside the affected ranges listed in the report.",
    },
    "Signing certificate has expired": {
        "root_cause": "The certificate used to sign this build has passed its notAfter date, typically because the signing keystore/cert was rotated or generated with a short validity window and the pipeline was never updated.",
        "fix": "Re-sign the release with a currently-valid certificate. If this is your long-term app-signing key, generate a replacement well before expiry (Play App Signing / App Store Connect both support key rotation) and re-publish.",
    },
    "Signing certificate expiring soon": {
        "root_cause": "The signing certificate's notAfter date falls within the near-term window, which will block future release builds once it lapses.",
        "fix": "Plan a certificate rotation now rather than after it expires - coordinate with your signing/release pipeline owner so app updates aren't blocked.",
    },
    "Provisioning profile has expired": {
        "root_cause": "The embedded provisioning profile's expiration date has passed, typically because the build was archived/distributed well after it was generated.",
        "fix": "Re-export and re-sign the build with a currently-valid provisioning profile from App Store Connect / your Apple Developer account.",
    },
    "Provisioning profile expiring soon": {
        "root_cause": "The embedded provisioning profile is close to its expiration date.",
        "fix": "Regenerate the provisioning profile before it lapses so future builds/distributions aren't blocked.",
    },
}


def _new_issue(list_: List[dict], severity: str, title: str, detail: str):
    list_.append({"severity": severity, "title": title, "detail": detail})


def _root_cause_and_fix(title: str) -> Optional[Dict[str, str]]:
    return ROOT_CAUSE_FIX_KB.get(title)


def _scan_zip_for_patterns(
    zf: zipfile.ZipFile,
    patterns,
    name_filter=None,
    max_total_bytes: int = MAX_TOTAL_SCAN_BYTES,
) -> Dict[str, List[str]]:
    """Read every packaged file (bounded) and test it against a list of
    (label, compiled-regex) tuples. Returns {label: [example matches]}.

    `name_filter`, if given, is a callable(filename) -> bool that limits
    which zip entries are even opened (e.g. only classes*.dex files) so a
    dedicated pattern group doesn't have to re-read the whole package.
    """
    hits: Dict[str, List[str]] = {}
    total_read = 0
    for info in zf.infolist():
        if info.is_dir() or info.file_size > MAX_SCAN_FILE_SIZE:
            continue
        if name_filter is not None and not name_filter(info.filename):
            continue
        if total_read >= max_total_bytes:
            break
        try:
            raw = zf.read(info.filename)
        except Exception:
            continue
        total_read += len(raw)
        # Cheap "is this worth regexing" gate: decode permissively, keep
        # printable-ish text. Covers dex, plist, xml, js, json, config files,
        # and Mach-O/DEX string tables well enough for substring matching.
        text = raw.decode("utf-8", errors="ignore")
        if not text:
            continue
        for label, pattern in patterns:
            m = pattern.search(text)
            if m:
                hits.setdefault(label, [])
                if len(hits[label]) < 3:
                    snippet = m.group(0)
                    if len(snippet) > 60:
                        snippet = snippet[:57] + "..."
                    hits[label].append(f"{info.filename}: {snippet}")
    return hits


def _extract_urls(
    zf: zipfile.ZipFile,
    max_total_bytes: int = MAX_TOTAL_SCAN_BYTES,
    max_urls: int = 200,
) -> List[Dict[str, Any]]:
    """Scan packaged files for http(s) URL strings and return a deduped,
    classified list (insecure http?, looks like an IP/staging/debug host?).

    Skips known namespace/doc-link boilerplate hosts (schemas.android.com,
    w3.org, slf4j.org, etc - see NON_ENDPOINT_URL_HOSTS) that show up in
    every build's compiled resources/binary XML or bundled third-party
    libraries regardless of app-specific content, and would otherwise
    drown out genuine app-controlled endpoints in the report.

    Bounded the same way as _scan_zip_for_patterns so this stays fast on
    large packages. Each surviving URL gets a stable `url_id` for report
    tables, ordered internal/debug-first so the highest-signal rows sort
    to the top.
    """
    seen: Dict[str, Dict[str, Any]] = {}
    total_read = 0
    for info in zf.infolist():
        if info.is_dir() or info.file_size > MAX_SCAN_FILE_SIZE:
            continue
        if total_read >= max_total_bytes or len(seen) >= max_urls:
            break
        try:
            raw = zf.read(info.filename)
        except Exception:
            continue
        total_read += len(raw)
        text = raw.decode("utf-8", errors="ignore")
        if not text:
            continue
        for m in URL_EXTRACT_PATTERN.finditer(text):
            url = m.group(0).rstrip(".,;:)")
            if url in seen or len(seen) >= max_urls:
                continue
            host = url.split("//", 1)[-1].split("/", 1)[0].split(":")[0].lower()
            if _is_boilerplate_host(host):
                continue
            classified = _classify_url(url)
            classified["source_file"] = info.filename
            seen[url] = classified

    ordered = sorted(
        seen.values(),
        key=lambda u: (not u["looks_internal_or_debug"], not u["insecure_http"]),
    )
    for idx, u in enumerate(ordered, start=1):
        u["url_id"] = f"URL-{idx:03d}"
    return ordered


def _is_dex(filename: str) -> bool:
    base = filename.rsplit("/", 1)[-1]
    return base.startswith("classes") and base.endswith(".dex")


def _exported_components(manifest_tree, tag: str) -> List[dict]:
    """Walk <activity>/<service>/<receiver>/<provider> nodes and report
    which are exported - explicitly or implicitly via an intent-filter -
    since an exported component is reachable by any other app on the
    device."""
    results = []
    if manifest_tree is None:
        return results
    for node in manifest_tree.iter(tag):
        name = node.get(f"{ANDROID_NS}name") or "(unnamed)"
        exported_attr = node.get(f"{ANDROID_NS}exported")
        has_intent_filter = node.find("intent-filter") is not None
        permission = node.get(f"{ANDROID_NS}permission")

        if exported_attr is not None:
            exported = exported_attr == "true"
        else:
            # Pre-Android-12 default: exported implicitly true if it has
            # an intent-filter and no explicit exported attribute.
            exported = has_intent_filter

        if exported:
            results.append({
                "name": name,
                "protected_by_permission": bool(permission),
                "permission": permission,
                "has_intent_filter": has_intent_filter,
            })
    return results


def _deep_link_schemes(manifest_tree) -> List[dict]:
    """Collect custom (non-http/https) URL schemes declared on exported
    activities via <intent-filter><data android:scheme="..."/>. Any app can
    register the same scheme and race the real app for it, so an unvalidated
    custom scheme is a classic deep-link hijack / parameter-injection vector."""
    schemes: List[dict] = []
    if manifest_tree is None:
        return schemes

    for activity in manifest_tree.iter("activity"):
        name = activity.get(f"{ANDROID_NS}name") or "(unnamed)"
        exported_attr = activity.get(f"{ANDROID_NS}exported")
        permission = activity.get(f"{ANDROID_NS}permission")

        for intent_filter in activity.findall("intent-filter"):
            is_browsable = any(
                cat.get(f"{ANDROID_NS}name") == "android.intent.category.BROWSABLE"
                for cat in intent_filter.findall("category")
            )
            for data in intent_filter.findall("data"):
                scheme = data.get(f"{ANDROID_NS}scheme")
                if not scheme or scheme in ("http", "https"):
                    continue
                exported = (exported_attr == "true") if exported_attr is not None else True
                schemes.append({
                    "activity": name,
                    "scheme": scheme,
                    "host": data.get(f"{ANDROID_NS}host"),
                    "exported": exported,
                    "browsable": is_browsable,
                    "protected_by_permission": bool(permission),
                })
    return schemes


def _obfuscation_estimate(apk) -> Optional[Dict[str, Any]]:
    """Rough heuristic for whether the build was minified/obfuscated
    (ProGuard/R8/DexGuard): sample the app's own class names (skip known
    third-party/framework packages) and measure what fraction look like
    short auto-generated identifiers (a, b, aa, a1, ...)."""
    try:
        classes = list(apk.get_classes())
    except Exception:
        return None
    if not classes:
        return None

    SKIP_PREFIXES = ("Landroid/", "Landroidx/", "Lcom/google/", "Lkotlin/", "Lkotlinx/", "Ljava/", "Lokhttp3/", "Lretrofit2/")
    own_classes = [c for c in classes if not str(c).startswith(SKIP_PREFIXES)]
    if not own_classes:
        return None

    sample = own_classes[:5000]
    short_name_re = re.compile(r"/([A-Za-z]{1,2})(\$[A-Za-z0-9]{1,2})?;$")
    short_count = sum(1 for c in sample if short_name_re.search(str(c)))
    ratio = short_count / len(sample)

    return {
        "sampled_classes": len(sample),
        "short_identifier_ratio": round(ratio, 2),
        "likely_obfuscated": ratio > 0.35,
    }


def _size_bucket(num_bytes: int) -> str:
    mb = num_bytes / (1024 * 1024)
    if mb < 20:
        return "Small (<20MB)"
    if mb < 60:
        return "Medium (20-60MB)"
    if mb < 150:
        return "Large (60-150MB)"
    return "Very large (>150MB)"


def _days_until(expiry_dt) -> Optional[int]:
    """Days remaining until `expiry_dt` (a datetime), or negative if already
    passed. Returns None if expiry_dt isn't a usable datetime."""
    if not isinstance(expiry_dt, datetime):
        return None
    now = datetime.now(expiry_dt.tzinfo) if expiry_dt.tzinfo else datetime.now()
    return (expiry_dt - now).days


def _check_cert_validity(cert_info: List[dict]) -> List[dict]:
    """Checks each signing certificate's notAfter date and returns
    (severity, title, detail) issue tuples for expired / soon-to-expire
    certs. Mutates each cert_info entry in place to add
    'days_until_expiry' for display in the report."""
    findings: List[dict] = []
    for c in cert_info:
        days_left = _days_until(c.get("_not_valid_after_dt"))
        c["days_until_expiry"] = days_left
        if days_left is None:
            continue
        if days_left < 0:
            findings.append({
                "severity": "Critical",
                "title": "Signing certificate has expired",
                "detail": f"Certificate for '{c.get('subject', 'unknown subject')}' expired "
                          f"{abs(days_left)} day(s) ago (not valid after {c.get('not_valid_after')}). "
                          "Builds signed with an expired certificate can fail install/update on some "
                          "devices and often indicate a stale or forgotten signing pipeline.",
            })
        elif days_left < CERT_EXPIRY_WARNING_DAYS:
            findings.append({
                "severity": "Medium",
                "title": "Signing certificate expiring soon",
                "detail": f"Certificate for '{c.get('subject', 'unknown subject')}' expires in "
                          f"{days_left} day(s) (not valid after {c.get('not_valid_after')}). "
                          "Rotate before expiry to avoid update-signature mismatches.",
            })
    return findings


def _data_leakage_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    """Consolidates every already-collected leak-relevant signal (hardcoded
    secrets, exposed internal/debug/plain-HTTP URLs, unencrypted local
    storage, weak crypto) into a single risk_level + signal list so the
    report can answer 'is this app likely leaking data' in one place
    instead of forcing a reviewer to piece it together from five sections."""
    secrets = result.get("secret_scan") or {}
    urls = result.get("exposed_urls") or {}
    storage = result.get("storage_security") or {}
    crypto = result.get("weak_crypto_scan") or {}

    signals: List[str] = []

    if secrets:
        signals.append(f"Hardcoded secret pattern(s) detected: {', '.join(secrets.keys())}")

    internal_count = urls.get("internal_or_debug_count") or 0
    if internal_count:
        signals.append(f"{internal_count} internal/staging/debug URL(s) baked into the build")

    insecure_http_count = urls.get("insecure_http_count") or 0
    if insecure_http_count:
        signals.append(f"{insecure_http_count} plain-HTTP endpoint(s) referenced (traffic interceptable)")

    storage_indicators = storage.get("indicators") or {}
    has_encryption_evidence = bool(storage.get("encrypted_storage_evidence") or storage.get("keychain_usage_detected"))
    if storage_indicators and not has_encryption_evidence:
        signals.append("Local data storage found with no encryption evidence (SharedPreferences/SQLite/NSUserDefaults)")

    if crypto:
        signals.append(f"Weak/legacy cryptographic primitive(s) referenced: {', '.join(crypto.keys())}")

    if secrets or internal_count:
        risk_level = "High"
    elif signals:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {"risk_level": risk_level, "signals": signals}


def _build_executive_summary(platform: str, package_or_bundle: str, issues: List[dict], score: int) -> str:
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Info": 0}
    for i in issues:
        counts[i["severity"]] = counts.get(i["severity"], 0) + 1
    headline = (
        f"{counts['Critical']} critical, {counts['High']} high, {counts['Medium']} medium, "
        f"{counts['Low']} low, and {counts['Info']} informational finding(s)"
    )
    if counts["Critical"]:
        posture = "requires immediate remediation before release"
    elif counts["High"]:
        posture = "has notable gaps that should be fixed before the next release"
    elif counts["Medium"]:
        posture = "is in reasonable shape with some hardening opportunities"
    else:
        posture = "shows a solid baseline security posture"
    return (
        f"Static analysis of {package_or_bundle} ({platform}) surfaced {headline}. "
        f"Overall security score: {score}/100. The app {posture}."
    )


def _risk_distribution(issues: List[dict]) -> Dict[str, int]:
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Info": 0}
    for i in issues:
        counts[i["severity"]] = counts.get(i["severity"], 0) + 1
    return counts


def _remediation_priority(issues: List[dict]) -> List[dict]:
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
    ranked = sorted(issues, key=lambda i: order.get(i["severity"], 99))
    queue = []
    for i in ranked:
        queue.append({
            "severity": i["severity"],
            "title": i["title"],
            "recommended_action": _SEVERITY_EFFORT_HINT.get(i["severity"], "Review"),
        })
    return queue


def _ai_findings(issues: List[dict], depth: str = "premium") -> List[dict]:
    """AI-style root-cause + fix write-up per issue.

    depth="premium" uses the full deterministic knowledge base (specific
    root cause + fix per issue title, falling back to a generic template
    for anything not yet in the KB).

    depth="standard" produces a lighter "basic" version: severity-driven
    generic guidance only, no KB lookup - enough to tell a reviewer what
    to prioritize without the full diagnostic write-up premium gives.
    """
    findings = []
    if depth == "standard":
        for i in issues:
            findings.append({
                "title": i["title"],
                "severity": i["severity"],
                "recommendation": f"{_SEVERITY_EFFORT_HINT.get(i['severity'], 'Review')} - see finding "
                                   "detail for the specific condition. Upgrade to Premium for a full "
                                   "root-cause analysis and fix recommendation on this issue.",
            })
        return findings

    for i in issues:
        kb = _root_cause_and_fix(i["title"])
        if kb is None:
            kb = {
                "root_cause": "See finding detail for the specific condition that triggered this check.",
                "fix": "Review the finding detail and apply the relevant platform security best practice.",
            }
        findings.append({
            "title": i["title"],
            "severity": i["severity"],
            "root_cause": kb["root_cause"],
            "fix_recommendation": kb["fix"],
        })
    return findings


def _dynamic_test_placeholder(dynamic_run: Optional[dict]) -> Dict[str, Any]:
    """This engine performs static analysis only (no emulator/device). If a
    caller has separately run a dynamic pass and hands us its output via
    `dynamic_run`, we pass it through under this section; otherwise we
    report the section as not performed rather than fabricating results."""
    if dynamic_run:
        return {"performed": True, **dynamic_run}
    return {
        "performed": False,
        "reason": "Static analysis only - no emulator/device session was supplied for this scan.",
    }


def _crash_anr_placeholder(dynamic_run: Optional[dict]) -> Dict[str, Any]:
    if dynamic_run and "crash_anr" in dynamic_run:
        return {"performed": True, **dynamic_run["crash_anr"]}
    return {
        "performed": False,
        "reason": "Requires a dynamic/instrumented run; not collected during static analysis.",
    }


def _screenshots_placeholder(dynamic_run: Optional[dict]) -> Dict[str, Any]:
    if dynamic_run and "screenshots" in dynamic_run:
        return {"performed": True, "evidence": dynamic_run["screenshots"]}
    return {
        "performed": False,
        "evidence": [],
        "reason": "Requires a dynamic/instrumented run; not captured during static analysis.",
    }


def analyze_android(file_path: str, depth: str, dynamic_run: Optional[dict] = None) -> Dict[str, Any]:
    from androguard.core.apk import APK

    issues: List[dict] = []
    apk = APK(file_path)

    package = apk.get_package()
    version_name = apk.get_androidversion_name()
    version_code = apk.get_androidversion_code()
    min_sdk = apk.get_min_sdk_version()
    target_sdk = apk.get_target_sdk_version()
    file_size = os.path.getsize(file_path)

    permissions = apk.get_permissions() or []
    dangerous = sorted({p: DANGEROUS_PERMISSIONS[p] for p in permissions if p in DANGEROUS_PERMISSIONS}.items())

    debuggable = (apk.get_attribute_value("application", "debuggable") == "true")
    allow_backup_raw = apk.get_attribute_value("application", "allowBackup")
    allow_backup = allow_backup_raw != "false"  # AOSP default is true when unset
    uses_cleartext_raw = apk.get_attribute_value("application", "usesCleartextTraffic")
    network_sec_config = apk.get_attribute_value("application", "networkSecurityConfig")

    # Manifest tree is cheap to parse and several basic-tier checks below
    # (deep-link scheme count) need it, so it's fetched unconditionally
    # rather than only at standard+.
    manifest_tree = apk.get_android_manifest_xml()

    if debuggable:
        _new_issue(issues, "Critical", "App is debuggable",
                   "android:debuggable=\"true\" is set in a release build. This lets anyone attach a "
                   "debugger to the app on a device and inspect/modify it at runtime. Remove before release.")

    if allow_backup:
        _new_issue(issues, "Medium", "Full app backup is enabled",
                   "android:allowBackup is not set to \"false\", so `adb backup` can copy the app's "
                   "private data off the device without root, including local databases/tokens.")

    # --- Cleartext traffic check (basic tier) ---------------------------
    # Moved out of the standard+ block: the module docstring promises
    # "cleartext traffic" as one of the basic-tier high-signal flags, but
    # this explicit-allow check previously only ran at standard+, so a
    # basic-plan scan never actually flagged it. It only needs data already
    # fetched above (uses_cleartext_raw), so there's no reason to gate it.
    if uses_cleartext_raw == "true":
        _new_issue(issues, "High", "Cleartext traffic explicitly allowed",
                   "android:usesCleartextTraffic=\"true\" permits plain HTTP, exposing traffic to "
                   "on-path interception.")
    elif uses_cleartext_raw is None and not network_sec_config and int(target_sdk or 0) < 28:
        _new_issue(issues, "Medium", "Cleartext traffic not explicitly disabled",
                   f"targetSdkVersion={target_sdk} is below 28, so cleartext HTTP is allowed by "
                   "default unless a Network Security Config says otherwise.")

    if int(min_sdk or 0) and int(min_sdk) < 23:
        _new_issue(issues, "Low", "Very low minimum SDK",
                   f"minSdkVersion={min_sdk} supports Android versions with known unpatched platform "
                   "vulnerabilities. Consider raising the floor if you don't need that reach.")

    if dangerous:
        _new_issue(issues, "Info", "Sensitive permissions requested",
                   f"{len(dangerous)} dangerous-protection-level permission(s) requested: "
                   + ", ".join(p for p, _ in dangerous[:6]) + ("..." if len(dangerous) > 6 else ""))

    # --- Permission Audit: risk-tiered breakdown (all depths get the raw
    # list; standard+ get the risk-tier grouping used in the report UI) ---
    permission_audit = {
        "total_requested": len(permissions),
        "dangerous": [{"permission": p, "description": d,
                        "risk_tier": PERMISSION_RISK_TIER.get(p, "Low")} for p, d in dangerous],
    }

    # --- Deep Link scheme count (basic tier) -----------------------------
    # Lightweight version of the standard-tier "Deep Links" section: just
    # the custom-scheme count from the manifest we already parsed above,
    # with no zip-content scanning. Standard/premium below overwrite
    # result["deep_links"] with their richer versions.
    deep_links_basic = _deep_link_schemes(manifest_tree)
    basic_deep_link_schemes = sorted({d["scheme"] for d in deep_links_basic})

    result: Dict[str, Any] = {
        "platform": "android",
        "overview": {
            "package": package,
            "version_name": version_name,
            "version_code": version_code,
            "min_sdk": min_sdk,
            "target_sdk": target_sdk,
            "file_size_bytes": file_size,
            "is_signed": apk.is_signed(),
            "signed_v1": apk.is_signed_v1(),
            "signed_v2": apk.is_signed_v2(),
            "signed_v3": apk.is_signed_v3(),
        },
        "permissions": permission_audit,
        "security_flags": {
            "debuggable": debuggable,
            "allow_backup": allow_backup,
            "uses_cleartext_traffic": uses_cleartext_raw,
            "has_network_security_config": bool(network_sec_config),
        },
        "deep_links": {
            "schemes": basic_deep_link_schemes,
            "count": len(basic_deep_link_schemes),
        },
        "issues": issues,
    }

    exported: Dict[str, list] = {}
    if depth in ("standard", "premium"):
        exported = {
            "activities": _exported_components(manifest_tree, "activity"),
            "services": _exported_components(manifest_tree, "service"),
            "receivers": _exported_components(manifest_tree, "receiver"),
            "providers": _exported_components(manifest_tree, "provider"),
        }
        unprotected_exported = sum(
            1 for group in exported.values() for c in group if not c["protected_by_permission"]
        )
        if unprotected_exported:
            _new_issue(issues, "High", "Unprotected exported components",
                       f"{unprotected_exported} exported component(s) have no permission requirement, "
                       "meaning any other app on the device can launch/bind to them.")

        # Manifest Audit section - exported components + top-level manifest facts.
        result["manifest_audit"] = {
            "exported_components": exported,
            "unprotected_exported_count": unprotected_exported,
            "uses_cleartext_traffic": uses_cleartext_raw,
            "has_network_security_config": bool(network_sec_config),
        }
        result["network_security"] = {
            "cleartext_traffic": uses_cleartext_raw,
            "network_security_config_present": bool(network_sec_config),
        }
        result["libraries"] = apk.get_libraries()

        # App Architecture overview (standard+)
        result["app_architecture"] = {
            "activities": len(list(manifest_tree.iter("activity"))) if manifest_tree is not None else None,
            "services": len(list(manifest_tree.iter("service"))) if manifest_tree is not None else None,
            "receivers": len(list(manifest_tree.iter("receiver"))) if manifest_tree is not None else None,
            "providers": len(list(manifest_tree.iter("provider"))) if manifest_tree is not None else None,
            "native_libraries": apk.get_libraries(),
            "min_sdk": min_sdk,
            "target_sdk": target_sdk,
        }

        # Performance overview (standard+) - static, size/count based only.
        result["performance"] = {
            "file_size_bytes": file_size,
            "file_size_bucket": _size_bucket(file_size),
            "native_library_count": len(apk.get_libraries() or []),
            "note": "Static-analysis performance signal only (package size, native lib count). "
                    "Full runtime performance profiling requires a dynamic test session.",
        }

        # Storage Security - basic subset on standard, full set on premium
        # (full set collected further below where the premium zip pass runs).
        with zipfile.ZipFile(file_path) as zf_std:
            storage_hits_basic = _scan_zip_for_patterns(zf_std, STORAGE_BASIC_PATTERNS, name_filter=_is_dex)
        if "World-readable/writable file mode" in storage_hits_basic:
            _new_issue(issues, "High", "Insecure local data storage detected",
                       "World-readable/writable file mode constants were found, which expose files to "
                       "every other app on the device.")
        result["storage_security"] = {
            "depth": "basic",
            "indicators": {label: hits for label, hits in storage_hits_basic.items()},
        }

        # Authentication - presence-only check on standard.
        with zipfile.ZipFile(file_path) as zf_auth:
            auth_hits_basic = _scan_zip_for_patterns(zf_auth, AUTH_BASIC_PATTERNS, name_filter=_is_dex)
        result["authentication"] = {
            "depth": "basic",
            "biometric_api_detected": "BiometricPrompt / Fingerprint API usage" in auth_hits_basic,
        }

        # Accessibility - lightweight heuristic on standard.
        with zipfile.ZipFile(file_path) as zf_a11y:
            a11y_hits = _scan_zip_for_patterns(zf_a11y, ACCESSIBILITY_PATTERNS)
        result["accessibility"] = {
            "content_description_usage_detected": "contentDescription usage" in a11y_hits,
            "accessibility_service_reference_detected": "Accessibility service reference" in a11y_hits,
            "note": "Static reference detection only - not a substitute for a manual screen-reader pass.",
        }

        # Deep Links - lightweight inventory on standard (full hijack audit is premium).
        if depth == "standard":
            result.pop("deep_links", None)

        # Exposed URLs - full extraction + classification even at standard
        # depth, since this is cheap and high-signal (leaked staging/debug
        # endpoints are common). Premium adds the dedicated issue below.
        with zipfile.ZipFile(file_path) as zf_urls:
            exposed_urls = _extract_urls(zf_urls)
        insecure_count = sum(1 for u in exposed_urls if u["insecure_http"])
        internal_count = sum(1 for u in exposed_urls if u["looks_internal_or_debug"])
        result["exposed_urls"] = {
            "total_found": len(exposed_urls),
            "insecure_http_count": insecure_count,
            "internal_or_debug_count": internal_count,
            "urls": exposed_urls,
        }
        if internal_count:
            _new_issue(issues, "Medium", "Internal/staging/debug URL(s) exposed in build",
                       f"{internal_count} URL(s) found that look like internal, staging, debug, or "
                       "IP-literal endpoints. Shipping these in a release build can expose "
                       "non-production infrastructure to anyone who decompiles the app.")
        if insecure_count:
            _new_issue(issues, "Low", "Plain HTTP URL(s) found in build",
                       f"{insecure_count} URL(s) use plain http:// instead of https://. Traffic to "
                       "these endpoints is vulnerable to on-path interception.")

    # ------------------------------------------------------------------ #
    # PREMIUM — deep security pass                                       #
    # ------------------------------------------------------------------ #
    if depth == "premium":
        native_libs = sorted({
            n for n in apk.get_files()
            if n.startswith("lib/") and n.endswith(".so")
        })

        cert_info: List[dict] = []
        try:
            for cert in apk.get_certificates():
                cert_info.append({
                    "subject": cert.subject.human_friendly,
                    "issuer": cert.issuer.human_friendly,
                    "serial_number": str(cert.serial_number),
                    "not_valid_before": str(cert.not_valid_before),
                    "not_valid_after": str(cert.not_valid_after),
                    "signature_algorithm": cert.signature_algo,
                    # Kept as a raw datetime for the expiry check below;
                    # stripped out before this list is stored on `result`.
                    "_not_valid_after_dt": cert.not_valid_after,
                })
        except Exception:
            cert_info = []

        # --- Certificate validity check ---------------------------------
        for finding in _check_cert_validity(cert_info):
            _new_issue(issues, finding["severity"], finding["title"], finding["detail"])

        with zipfile.ZipFile(file_path) as zf:
            # Full-package scans (secrets/crypto can hide in assets, config
            # files, JS bundles, etc — not just compiled code).
            secret_hits = _scan_zip_for_patterns(zf, SECRET_PATTERNS)
            crypto_hits = _scan_zip_for_patterns(zf, WEAK_CRYPTO_PATTERNS)

            # Code-level scans are scoped to classes*.dex — these patterns
            # are API/class names, which only ever appear in compiled code,
            # so narrowing the read set keeps this fast on large APKs.
            webview_hits = _scan_zip_for_patterns(zf, WEBVIEW_RISK_PATTERNS, name_filter=_is_dex)
            ssl_bypass_hits = _scan_zip_for_patterns(zf, SSL_BYPASS_PATTERNS, name_filter=_is_dex)
            pinning_hits = _scan_zip_for_patterns(zf, SSL_PINNING_EVIDENCE_PATTERNS, name_filter=_is_dex)
            anti_tamper_hits = _scan_zip_for_patterns(zf, ANTI_TAMPER_PATTERNS, name_filter=_is_dex)
            deeplink_lib_hits = _scan_zip_for_patterns(zf, DEEPLINK_INDICATOR_PATTERNS, name_filter=_is_dex)
            storage_hits = _scan_zip_for_patterns(zf, STORAGE_RISK_PATTERNS, name_filter=_is_dex)
            auth_hits = _scan_zip_for_patterns(zf, AUTH_RISK_PATTERNS, name_filter=_is_dex)

            sdk_patterns = [(label, re.compile(re.escape(prefix))) for prefix, label in ANDROID_THIRD_PARTY_SDKS.items()]
            sdk_hits = _scan_zip_for_patterns(zf, sdk_patterns, name_filter=_is_dex)

        if secret_hits:
            _new_issue(issues, "Critical", "Possible hardcoded secrets found",
                       f"Pattern match(es) for: {', '.join(secret_hits.keys())}. Review and rotate any "
                       "real credentials found packaged inside the app.")
        if crypto_hits:
            _new_issue(issues, "Medium", "Weak/legacy cryptographic primitives referenced",
                       f"References to: {', '.join(crypto_hits.keys())}. Prefer AES-GCM and SHA-256+ "
                       "for anything security-sensitive.")
        if not apk.is_signed_v2() and not apk.is_signed_v3():
            _new_issue(issues, "Medium", "No APK Signature Scheme v2/v3",
                       "Only legacy v1 (JAR) signing was detected. v1-only signing is more susceptible "
                       "to APK tampering (e.g. the Janus vulnerability class) on older devices.")

        # --- WebView JS-bridge exposure --------------------------------
        if "addJavascriptInterface() bridge" in webview_hits and "JavaScript enabled on WebView" in webview_hits:
            _new_issue(issues, "High", "WebView exposes a JavaScript bridge",
                       "addJavascriptInterface() is used together with JavaScript execution enabled. "
                       "If the WebView can ever load untrusted/remote content, this bridge lets that "
                       "page call into native app code directly (a classic WebView RCE pattern below "
                       "API 17, and still a data-exposure risk above it).")
        elif webview_hits:
            _new_issue(issues, "Low", "WebView usage detected",
                       f"WebView API(s) in use: {', '.join(webview_hits.keys())}. Worth a manual check "
                       "that only trusted content is ever loaded.")

        # --- TLS trust bypass -------------------------------------------
        if ssl_bypass_hits:
            _new_issue(issues, "High", "Possible SSL/TLS trust validation bypass",
                       f"Found: {', '.join(ssl_bypass_hits.keys())}. A custom TrustManager or hostname "
                       "verifier can be legitimate for pinning, but is also the standard pattern for "
                       "accidentally (or deliberately) disabling certificate validation. Confirm the "
                       "implementation still rejects invalid/self-signed certificates.")

        # --- Certificate pinning coverage --------------------------------
        has_pinning_evidence = bool(pinning_hits) or bool(network_sec_config)
        if not has_pinning_evidence:
            _new_issue(issues, "Low", "No certificate pinning detected",
                       "No CertificatePinner, TrustKit, or Network Security Config pin-set was found. "
                       "Pinning isn't mandatory, but its absence means the app relies solely on the "
                       "device's trust store, which is defeatable with a rogue CA on the device.")

        # --- Root / anti-tamper protection coverage -----------------------
        if not anti_tamper_hits:
            _new_issue(issues, "Info", "No root/anti-tamper detection signatures found",
                       "No known root-detection, Play Integrity/SafetyNet, or anti-debugging library "
                       "signatures were found. Relevant mainly for apps handling payments, DRM'd "
                       "content, or sensitive data — not every app needs this.")

        # --- Deep-link / custom URL scheme audit ---------------------------
        deep_links = _deep_link_schemes(manifest_tree)
        unprotected_deep_links = [d for d in deep_links if d["exported"] and not d["protected_by_permission"]]
        if unprotected_deep_links:
            schemes = sorted({d["scheme"] for d in unprotected_deep_links})
            _new_issue(issues, "Medium", "Unvalidated custom URL scheme(s) exposed",
                       f"Custom scheme(s) {', '.join(schemes)} are handled by exported, unprotected "
                       "activities. Any other installed app can register the same scheme and intercept "
                       "or spoof these deep links. Validate all incoming intent data and prefer Android "
                       "App Links (verified https) for anything security-sensitive.")

        # --- Obfuscation heuristic -----------------------------------------
        obfuscation = _obfuscation_estimate(apk)
        if obfuscation is not None and not obfuscation["likely_obfuscated"]:
            _new_issue(issues, "Low", "Code does not appear to be obfuscated/minified",
                       "Class/method names largely look human-readable, suggesting ProGuard/R8 shrinking "
                       "and obfuscation may not be enabled for release builds. Obfuscation raises the "
                       "bar for reverse engineering (though it isn't a substitute for real security).")

        # --- Storage Security (full) -----------------------------------------
        if ("Plaintext SharedPreferences write" in storage_hits or "SQLite database usage" in storage_hits) \
                and "EncryptedSharedPreferences usage" not in storage_hits and "SQLCipher usage" not in storage_hits:
            _new_issue(issues, "Medium", "Insecure local data storage detected",
                       "SharedPreferences and/or SQLite usage was found with no EncryptedSharedPreferences "
                       "or SQLCipher evidence, suggesting locally-stored data may be unencrypted at rest.")
        if "World-readable/writable file mode" in storage_hits:
            _new_issue(issues, "High", "World-readable/writable file mode used",
                       "MODE_WORLD_READABLE/WRITEABLE constants were found - deprecated since API 17 "
                       "and a direct local data-exposure risk.")

        # --- Authentication (full) --------------------------------------------
        if "Hardcoded credential-like assignment" in auth_hits:
            _new_issue(issues, "Critical", "Hardcoded credential-like value found",
                       "A string assignment matching a password/credential pattern was found in code.")
        if "Weak session/token generation (Random)" in auth_hits:
            _new_issue(issues, "Medium", "Weak session/token generation",
                       "java.util.Random() is not cryptographically secure; session/token generation "
                       "should use SecureRandom instead.")

        # --- SDK / Dependency advisories -----------------------------------
        detected_sdk_labels = sorted(set(sdk_hits.keys()) | set(deeplink_lib_hits.keys()))
        sdk_advisories = {label: KNOWN_SDK_ADVISORIES[label] for label in detected_sdk_labels if label in KNOWN_SDK_ADVISORIES}
        if sdk_advisories:
            _new_issue(issues, "Medium", "Third-party SDK(s) with known advisories",
                       f"Bundled SDK(s) with published advisories for older versions: {', '.join(sdk_advisories.keys())}. "
                       "Confirm bundled versions are current.")

        result["native_libraries"] = native_libs
        # Public-facing certificate list — drop the internal raw-datetime
        # helper key before this goes into the report/JSON.
        result["certificates"] = [
            {k: v for k, v in c.items() if not k.startswith("_")} for c in cert_info
        ]
        result["secret_scan"] = {label: hits for label, hits in secret_hits.items()}
        result["weak_crypto_scan"] = {label: hits for label, hits in crypto_hits.items()}
        result["webview_scan"] = {label: hits for label, hits in webview_hits.items()}
        result["ssl_tls_scan"] = {
            "trust_bypass_indicators": {label: hits for label, hits in ssl_bypass_hits.items()},
            "pinning_evidence": {label: hits for label, hits in pinning_hits.items()},
            "pinning_detected": has_pinning_evidence,
        }
        result["anti_tamper_scan"] = {
            "protections_detected": {label: hits for label, hits in anti_tamper_hits.items()},
            "any_protection_detected": bool(anti_tamper_hits),
        }
        if depth == "standard":
            result.pop("deep_links", None)
            result["obfuscation"] = obfuscation
            result["third_party_sdks"] = {
                "detected": detected_sdk_labels,
                "advisories": sdk_advisories,
            }
            result["storage_security"] = {
                "depth": "full",
                "indicators": {label: hits for label, hits in storage_hits.items()},
                "encrypted_storage_evidence": bool(
                    storage_hits.get("EncryptedSharedPreferences usage") or storage_hits.get("SQLCipher usage")
                    or storage_hits.get("Android Keystore usage")
                ),
            }
            result["authentication"] = {
                "depth": "full",
                "biometric_api_detected": "BiometricPrompt / Fingerprint API usage" in auth_hits,
                "indicators": {label: hits for label, hits in auth_hits.items()
                                if label != "Hardcoded credential-like assignment"},
                "hardcoded_credential_pattern_found": "Hardcoded credential-like assignment" in auth_hits,
            }
            result["dynamic_test_results"] = _dynamic_test_placeholder(dynamic_run)
            result["crash_anr"] = _crash_anr_placeholder(dynamic_run)
            result["screenshots_evidence"] = _screenshots_placeholder(dynamic_run)

    # ------------------------------------------------------------------ #
    # Report-shape sections available at standard+ (built after `issues`  #
    # is finalized for this depth so counts/summary reflect everything).  #
    # ------------------------------------------------------------------ #
    if depth in ("standard", "premium"):
        prelim = _score_and_severity(issues)
        result["executive_summary"] = _build_executive_summary(
            "Android", package or "this app", issues, prelim["security_score"])
        result["risk_distribution"] = _risk_distribution(issues)

    # AI root-cause + fix write-up: a lighter "basic" version ships at
    # standard depth (severity-driven generic guidance, no KB lookup); the
    # full deterministic KB write-up stays premium-only.
    if depth == "standard":
        result["ai_findings"] = _ai_findings(issues, depth="standard")

    if depth == "premium":
        result["ai_findings"] = _ai_findings(issues, depth="premium")
        result["remediation_priority"] = _remediation_priority(issues)

    return result


def analyze_ios(file_path: str, depth: str, dynamic_run: Optional[dict] = None) -> Dict[str, Any]:
    issues: List[dict] = []

    with zipfile.ZipFile(file_path) as zf:
        names = zf.namelist()
        plist_candidates = [
            n for n in names
            if re.match(r"^Payload/[^/]+\.app/Info\.plist$", n)
        ]
        if not plist_candidates:
            raise ValueError("Not a valid .ipa: no Payload/*.app/Info.plist found")

        app_root = plist_candidates[0].rsplit("/", 1)[0]
        with zf.open(plist_candidates[0]) as fh:
            info = plistlib.load(fh)

        provisioning_present = any(n == f"{app_root}/embedded.mobileprovision" for n in names)
        provisioning_snippet = None
        if provisioning_present:
            try:
                raw = zf.read(f"{app_root}/embedded.mobileprovision")
                text = raw.decode("latin-1", errors="ignore")
                start = text.find("<?xml")
                end = text.find("</plist>")
                if start != -1 and end != -1:
                    provisioning_snippet = plistlib.loads(text[start:end + 8].encode("latin-1"))
            except Exception:
                provisioning_snippet = None

    bundle_id = info.get("CFBundleIdentifier")
    version = info.get("CFBundleShortVersionString")
    build = info.get("CFBundleVersion")
    min_os = info.get("MinimumOSVersion")
    executable = info.get("CFBundleExecutable")
    file_size = os.path.getsize(file_path)

    ats = info.get("NSAppTransportSecurity", {}) or {}
    allows_arbitrary_loads = bool(ats.get("NSAllowsArbitraryLoads"))
    exception_domains = list((ats.get("NSExceptionDomains") or {}).keys())

    usage_descriptions = {
        k: v for k, v in info.items()
        if k.startswith("NS") and k.endswith("UsageDescription")
    }
    empty_usage_descriptions = [k for k, v in usage_descriptions.items() if not str(v).strip()]

    url_types = info.get("CFBundleURLTypes") or []
    custom_schemes = sorted({
        scheme
        for entry in url_types
        for scheme in (entry.get("CFBundleURLSchemes") or [])
    })

    if allows_arbitrary_loads:
        _new_issue(issues, "High", "App Transport Security disabled globally",
                   "NSAppTransportSecurity.NSAllowsArbitraryLoads = true allows plain HTTP and weak TLS "
                   "to any domain, defeating ATS's protections app-wide.")
    if exception_domains:
        _new_issue(issues, "Medium", "ATS exceptions configured for specific domains",
                   f"{len(exception_domains)} domain(s) opt out of default ATS protections: "
                   + ", ".join(exception_domains[:5]) + ("..." if len(exception_domains) > 5 else ""))
    if empty_usage_descriptions:
        _new_issue(issues, "Low", "Empty permission usage description(s)",
                   f"{', '.join(empty_usage_descriptions)} are present but empty - App Store review can "
                   "reject this, and users see a blank/unclear permission prompt.")

    # --- Deep link scheme count (basic tier) -----------------------------
    # Same lightweight treatment as Android: basic gets the custom-scheme
    # count/list from the Info.plist we already parsed above (cheap, no
    # zip re-scan). Standard/premium below overwrite with richer versions
    # where applicable.
    result: Dict[str, Any] = {
        "platform": "ios",
        "overview": {
            "bundle_id": bundle_id,
            "version": version,
            "build": build,
            "minimum_os_version": min_os,
            "executable": executable,
            "file_size_bytes": file_size,
        },
        "app_transport_security": {
            "allows_arbitrary_loads": allows_arbitrary_loads,
            "exception_domains": exception_domains,
        },
        "permission_usage_descriptions": usage_descriptions,
        "deep_links": {
            "schemes": custom_schemes,
            "count": len(custom_schemes),
        },
        "issues": issues,
    }

    if depth in ("standard", "premium"):
        result["provisioning_profile_present"] = provisioning_present
        if provisioning_present and isinstance(provisioning_snippet, dict):
            entitlements = provisioning_snippet.get("Entitlements", {})
            get_task_allow = bool(entitlements.get("get-task-allow"))
            if get_task_allow:
                _new_issue(issues, "High", "get-task-allow entitlement is enabled",
                           "This entitlement allows any process to attach a debugger to the app - it "
                           "should never be true in an App Store distribution build.")

            # --- Provisioning profile expiry check --------------------------
            expiration_date = provisioning_snippet.get("ExpirationDate")
            days_left = _days_until(expiration_date)
            if days_left is not None:
                if days_left < 0:
                    _new_issue(issues, "Critical", "Provisioning profile has expired",
                               f"Provisioning profile expired {abs(days_left)} day(s) ago "
                               f"(expiration date {expiration_date}). Expired profiles block "
                               "installs/updates for anyone who doesn't already have the app.")
                elif days_left < PROVISIONING_EXPIRY_WARNING_DAYS:
                    _new_issue(issues, "Medium", "Provisioning profile expiring soon",
                               f"Provisioning profile expires in {days_left} day(s) (expiration date "
                               f"{expiration_date}). Regenerate before it lapses.")

            result["provisioning_profile"] = {
                "name": provisioning_snippet.get("Name"),
                "team_name": provisioning_snippet.get("TeamName"),
                "expiration_date": str(expiration_date),
                "days_until_expiry": days_left,
                "get_task_allow": get_task_allow,
                "provisions_all_devices": bool(provisioning_snippet.get("ProvisionsAllDevices")),
            }

        # Manifest-equivalent audit for iOS: Info.plist facts in one place.
        result["manifest_audit"] = {
            "bundle_id": bundle_id,
            "minimum_os_version": min_os,
            "ats_allows_arbitrary_loads": allows_arbitrary_loads,
            "ats_exception_domain_count": len(exception_domains),
            "provisioning_profile_present": provisioning_present,
        }

        # App Architecture overview (standard+)
        with zipfile.ZipFile(file_path) as zf_arch:
            framework_count = len({
                n.split("/")[2] for n in zf_arch.namelist()
                if f"{app_root}/Frameworks/" in n and n.endswith(".framework/")
            })
        result["app_architecture"] = {
            "embedded_framework_count": framework_count,
            "minimum_os_version": min_os,
            "executable": executable,
        }

        # Performance overview (standard+)
        result["performance"] = {
            "file_size_bytes": file_size,
            "file_size_bucket": _size_bucket(file_size),
            "embedded_framework_count": framework_count,
            "note": "Static-analysis performance signal only (package size, framework count). "
                    "Full runtime performance profiling requires a dynamic test session.",
        }

        # Storage Security - basic subset on standard.
        with zipfile.ZipFile(file_path) as zf_std_store:
            storage_hits_basic = _scan_zip_for_patterns(zf_std_store, IOS_STORAGE_BASIC_PATTERNS)
        if "NSFileProtectionNone (no file encryption)" in storage_hits_basic:
            _new_issue(issues, "High", "Insecure local data storage detected",
                       "NSFileProtectionNone was found, which disables file-level encryption for the "
                       "affected files even when the device is locked.")
        result["storage_security"] = {
            "depth": "basic",
            "indicators": {label: hits for label, hits in storage_hits_basic.items()},
        }

        # Authentication - presence-only check on standard.
        with zipfile.ZipFile(file_path) as zf_auth_std:
            auth_hits_basic = _scan_zip_for_patterns(zf_auth_std, IOS_AUTH_BASIC_PATTERNS)
        result["authentication"] = {
            "depth": "basic",
            "biometric_api_detected": "LocalAuthentication (Face ID / Touch ID) usage" in auth_hits_basic,
        }

        # Accessibility - iOS has no static analog as strong as Android's
        # contentDescription check from a compiled IPA alone, so this stays
        # a light structural note rather than a fabricated heuristic.
        result["accessibility"] = {
            "note": "Static IPA analysis has limited visibility into accessibility labeling; a manual "
                    "VoiceOver pass or Xcode Accessibility Inspector run is recommended.",
        }

        # Deep Links - lightweight inventory on standard.
        result["deep_links"] = {
            "schemes": custom_schemes,
            "count": len(custom_schemes),
        }

        # Exposed URLs - same extraction/classification as Android.
        with zipfile.ZipFile(file_path) as zf_urls:
            exposed_urls = _extract_urls(zf_urls)
        insecure_count = sum(1 for u in exposed_urls if u["insecure_http"])
        internal_count = sum(1 for u in exposed_urls if u["looks_internal_or_debug"])
        result["exposed_urls"] = {
            "total_found": len(exposed_urls),
            "insecure_http_count": insecure_count,
            "internal_or_debug_count": internal_count,
            "urls": exposed_urls,
        }
        if internal_count:
            _new_issue(issues, "Medium", "Internal/staging/debug URL(s) exposed in build",
                       f"{internal_count} URL(s) found that look like internal, staging, debug, or "
                       "IP-literal endpoints. Shipping these in a release build can expose "
                       "non-production infrastructure to anyone who decompiles the app.")
        if insecure_count:
            _new_issue(issues, "Low", "Plain HTTP URL(s) found in build",
                       f"{insecure_count} URL(s) use plain http:// instead of https://. Traffic to "
                       "these endpoints is vulnerable to on-path interception.")

    # ------------------------------------------------------------------ #
    # PREMIUM — deep security pass                                       #
    # ------------------------------------------------------------------ #
    if depth == "premium":
        with zipfile.ZipFile(file_path) as zf:
            secret_hits = _scan_zip_for_patterns(zf, SECRET_PATTERNS)
            crypto_hits = _scan_zip_for_patterns(zf, WEAK_CRYPTO_PATTERNS)
            jailbreak_hits = _scan_zip_for_patterns(zf, JAILBREAK_DETECTION_PATTERNS)
            pinning_hits = _scan_zip_for_patterns(zf, IOS_PINNING_EVIDENCE_PATTERNS)
            storage_hits = _scan_zip_for_patterns(zf, IOS_STORAGE_PATTERNS)
            auth_hits = _scan_zip_for_patterns(zf, IOS_AUTH_PATTERNS)

            frameworks = sorted({
                n.split("/")[2] for n in zf.namelist()
                if f"{app_root}/Frameworks/" in n and n.endswith(".framework/")
            })

        if secret_hits:
            _new_issue(issues, "Critical", "Possible hardcoded secrets found",
                       f"Pattern match(es) for: {', '.join(secret_hits.keys())}. Review and rotate any "
                       "real credentials found packaged inside the app.")
        if crypto_hits:
            _new_issue(issues, "Medium", "Weak/legacy cryptographic primitives referenced",
                       f"References to: {', '.join(crypto_hits.keys())}. Prefer AES-GCM/CryptoKit "
                       "equivalents for anything security-sensitive.")

        # --- Jailbreak detection coverage --------------------------------
        if not jailbreak_hits:
            _new_issue(issues, "Info", "No jailbreak-detection signatures found",
                       "No known jailbreak-detection checks (Cydia paths, MobileSubstrate, common "
                       "jailbreak-detection libraries) were found. Relevant mainly for apps handling "
                       "payments, DRM'd content, or sensitive data — not every app needs this.")

        # --- Certificate pinning coverage ---------------------------------
        has_pinning_evidence = bool(pinning_hits)
        if not has_pinning_evidence:
            _new_issue(issues, "Low", "No certificate pinning detected",
                       "No TrustKit, SecTrustEvaluate-based, or third-party pinning library evidence "
                       "was found. Pinning isn't mandatory, but its absence means the app relies solely "
                       "on the device's trust store.")

        # --- Storage Security (full) -----------------------------------------
        if "NSFileProtectionNone (no file encryption)" in storage_hits:
            _new_issue(issues, "High", "Insecure local data storage detected",
                       "NSFileProtectionNone was found, disabling file-level encryption for affected files.")
        elif storage_hits.get("NSUserDefaults usage") and not storage_hits.get("Keychain usage"):
            _new_issue(issues, "Low", "Possible reliance on NSUserDefaults for sensitive data",
                       "NSUserDefaults usage was found with no Keychain usage detected elsewhere - "
                       "confirm no credentials/tokens are stored in NSUserDefaults, which is unencrypted.")

        # --- Authentication (full) --------------------------------------------
        if "Hardcoded credential-like assignment" in auth_hits:
            _new_issue(issues, "Critical", "Hardcoded credential-like value found",
                       "A string assignment matching a password/credential pattern was found in code.")

        # --- Third-party SDK fingerprinting --------------------------------
        detected_sdks = sorted({
            label for framework_prefix, label in IOS_THIRD_PARTY_SDKS.items()
            if any(framework_prefix.lower() in f.lower() for f in frameworks)
        })
        sdk_advisories = {label: KNOWN_SDK_ADVISORIES[label] for label in detected_sdks if label in KNOWN_SDK_ADVISORIES}
        if sdk_advisories:
            _new_issue(issues, "Medium", "Third-party SDK(s) with known advisories",
                       f"Bundled SDK(s) with published advisories for older versions: {', '.join(sdk_advisories.keys())}. "
                       "Confirm bundled versions are current.")

        # --- Deep-link (custom URL scheme) audit ----------------------------
        if custom_schemes:
            _new_issue(issues, "Info", "Custom URL scheme(s) registered",
                       f"App handles custom URL scheme(s): {', '.join(custom_schemes)}. Any other app "
                       "can register the same scheme and race for it (or spoof calls into yours) — "
                       "validate all incoming URL parameters and prefer Universal Links (verified "
                       "https, associated-domains) for anything security-sensitive.")

        result["embedded_frameworks"] = frameworks
        result["secret_scan"] = {label: hits for label, hits in secret_hits.items()}
        result["weak_crypto_scan"] = {label: hits for label, hits in crypto_hits.items()}
        result["jailbreak_detection_scan"] = {
            "protections_detected": {label: hits for label, hits in jailbreak_hits.items()},
            "any_protection_detected": bool(jailbreak_hits),
        }
        result["ssl_tls_scan"] = {
            "pinning_evidence": {label: hits for label, hits in pinning_hits.items()},
            "pinning_detected": has_pinning_evidence,
        }
        result["url_schemes"] = custom_schemes
        result["third_party_sdks"] = {
            "detected": detected_sdks,
            "advisories": sdk_advisories,
        }
        result["storage_security"] = {
            "depth": "full",
            "indicators": {label: hits for label, hits in storage_hits.items()},
            "keychain_usage_detected": "Keychain usage" in storage_hits,
        }
        result["authentication"] = {
            "depth": "full",
            "biometric_api_detected": "LocalAuthentication (Face ID / Touch ID) usage" in auth_hits,
            "hardcoded_credential_pattern_found": "Hardcoded credential-like assignment" in auth_hits,
        }
        result["accessibility"] = {
            "note": "Static IPA analysis has limited visibility into accessibility labeling; a manual "
                    "VoiceOver pass or Xcode Accessibility Inspector run is recommended.",
        }
        result["dynamic_test_results"] = _dynamic_test_placeholder(dynamic_run)
        result["crash_anr"] = _crash_anr_placeholder(dynamic_run)
        result["screenshots_evidence"] = _screenshots_placeholder(dynamic_run)

    if depth in ("standard", "premium"):
        prelim = _score_and_severity(issues)
        result["executive_summary"] = _build_executive_summary(
            "iOS", bundle_id or "this app", issues, prelim["security_score"])
        result["risk_distribution"] = _risk_distribution(issues)

    if depth == "standard":
        result["ai_findings"] = _ai_findings(issues, depth="standard")

    if depth == "premium":
        result["ai_findings"] = _ai_findings(issues, depth="premium")
        result["remediation_priority"] = _remediation_priority(issues)

    return result


def _score_and_severity(issues: List[dict]) -> Dict[str, Any]:
    score = 100
    for issue in issues:
        score -= _SEVERITY_PENALTY.get(issue["severity"], 0)
    score = max(0, min(100, score))

    if any(i["severity"] == "Critical" for i in issues):
        severity = "Critical"
    elif any(i["severity"] == "High" for i in issues):
        severity = "High"
    elif any(i["severity"] == "Medium" for i in issues):
        severity = "Medium"
    elif issues:
        severity = "Low"
    else:
        severity = "Low"

    return {"security_score": score, "severity": severity}


def _final_score(security_score: int, result: Dict[str, Any], depth: str) -> Dict[str, Any]:
    """Weighted Final Score for premium reports: blends the base security
    score with a couple of report-quality signals (pinning coverage,
    obfuscation, encrypted storage) that the plain issue-penalty score
    doesn't fully capture on its own."""
    bonuses = 0
    notes = []

    ssl = result.get("ssl_tls_scan") or {}
    if ssl.get("pinning_detected"):
        bonuses += 3
        notes.append("+3 certificate pinning in place")

    if result.get("platform") == "android":
        obf = result.get("obfuscation")
        if obf and obf.get("likely_obfuscated"):
            bonuses += 2
            notes.append("+2 code appears obfuscated")
        storage = result.get("storage_security") or {}
        if storage.get("encrypted_storage_evidence"):
            bonuses += 2
            notes.append("+2 encrypted local storage evidence found")
    else:
        storage = result.get("storage_security") or {}
        if storage.get("keychain_usage_detected"):
            bonuses += 2
            notes.append("+2 Keychain usage detected for sensitive storage")

    final = max(0, min(100, security_score + bonuses))
    return {"base_security_score": security_score, "bonus_points": bonuses,
            "bonus_notes": notes, "final_score": final}


def analyze_mobile_app(file_path: str, platform: str, depth: str, dynamic_run: Optional[dict] = None) -> Dict[str, Any]:
    """Entry point used by the router. `platform` is 'android' or 'ios',
    `depth` is 'basic' | 'standard' | 'premium' (already resolved from the
    user's plan before this is called). `dynamic_run`, if provided, is the
    output of a separately-run dynamic/instrumented test session (this
    module itself performs static analysis only) and is only consulted at
    premium depth to populate Dynamic Test Results / Crash-ANR / Screenshots."""

    if platform == "android":
        result = analyze_android(file_path, depth, dynamic_run=dynamic_run)
    elif platform == "ios":
        result = analyze_ios(file_path, depth, dynamic_run=dynamic_run)
    else:
        raise ValueError(f"Unsupported platform: {platform}")

    result["scan_depth"] = depth
    result.update(_score_and_severity(result["issues"]))

    if depth == "premium":
        result["final_score"] = _final_score(result["security_score"], result, depth)
        # Consolidated "is this app likely leaking data" verdict, built
        # from signals already collected above (secrets, exposed URLs,
        # storage encryption evidence, weak crypto).
        result["data_leakage_summary"] = _data_leakage_summary(result)

    return result


def detect_platform(filename: str) -> Optional[str]:
    lower = filename.lower()
    if lower.endswith(".apk"):
        return "android"
    if lower.endswith(".ipa"):
        return "ios"
    return None