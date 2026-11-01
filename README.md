# Vrika Mobile Security

Vrika Mobile Security is an automated, all-in-one mobile application (Android/iOS/Windows) pen-testing, malware analysis, and security assessment platform capable of performing static and dynamic analysis. Based on [MobSF](https://github.com/MobSF/Mobile-Security-Framework-MobSF).

The Static Analyzer supports popular mobile app binaries and libraries (`APK`, `XAPK`, `AAB`, `JAR`, `AAR`, `DEX`, `SO`, `IPA`, `DYLIB`, `A`, `APPX`) as well as Android and iOS source code. The Dynamic Analyzer supports both Android and iOS applications across emulators, simulators, Corellium, and physical devices (including stock non-rooted Android devices via Frida Gadget), offering an interactive platform for instrumented testing, runtime data inspection, and live web traffic analysis. Vrika Mobile Security integrates with your DevSecOps or CI/CD pipeline via REST APIs and CLI tools.

[![python](https://img.shields.io/badge/python-3.12+-blue.svg?logo=python&labelColor=yellow)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0--only-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)

## Quick Start

Build and run locally with docker:

```bash
docker build -t vrika-mobile-security .
docker run -it --rm -p 8000:8000 vrika-mobile-security
```

Or with docker compose (postgres, nginx, djangoq included):

```bash
cd docker
docker compose up
```

Default username and password: `mobsf/mobsf`

## Features

* Static Analysis - Android
* Static Analysis - iOS
* Dynamic Analysis - Android APK
* Dynamic Analysis - iOS IPA
* Web API Viewer
* REST API for CI/CD integration

## Documentation

* MobSF upstream docs: [mobsf.github.io/docs](https://mobsf.github.io/docs)
* MobSF SAST scanner for CI/CD: [mobsfscan](https://github.com/MobSF/mobsfscan)

## License

GPL-3.0-only
