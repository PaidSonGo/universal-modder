# Sandbox Reply Lab Android build

This project is an offline APK/XAPK static inspector with a local authenticated REA bridge for Termux and an optional, consent-based debug memory target for software you control.

Android sources are currently stored as a **SHA-256 verified source archive** (source.tar.xz). Workflow srl-android-verify-build.yml unpacks them in the CI runner and builds a debug APK.

SHA-256: 4d8ff944f4798f972af78de35c6d17edac2c4f6482e2444e475064fa82e7b461

The upstream REA 6.4.0 engine is **not** bundled in the APK. It runs locally in the separate Termux process at 127.0.0.1:18767 (see integrations/sandbox-reply-lab).

This is a test/debug build. Android signing credentials are runner-generated and cannot be assumed stable across separate CI runs. No claim of Android device runtime verification is made until installed and tested.
