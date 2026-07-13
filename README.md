# Gaze-Guided-Spiral-Soft-Robotic-Grasping-System
Gaze-guided spiral soft robotic grasping system for Parkinson's patients, STM32 embedded control, impedance control via Damiao(TBD) motors, and eye-tracking-driven grasp intent recognition.
# Gaze-Guided Spiral Soft Robotic Grasping System

A gaze-controlled soft robotic grasper designed to assist Parkinson's patients with fine motor impairments in everyday grasping tasks. The system closes the loop from **perception** (gaze tracking) to **decision** (intent recognition) to **actuation** (compliant soft gripper), combining embedded control, impedance control, and human-robot interaction.

## Overview

Patients with Parkinson's disease often experience tremors and reduced fine motor control that make precise grasping difficult. This project explores a hands-free, gaze-driven alternative: the user looks at an object, the system recognizes grasp intent from gaze signals, and a compliant soft gripper executes the grasp safely and adaptively.

## Key Features

- **Soft spiral gripper** — SpiRobs-inspired continuum structure, 3D printed in TPU (Bambu Lab X1C) for compliant, low-risk contact with the user's environment
- **Embedded control** — STM32-based real-time control loop for gripper actuation
- **Impedance control** — MIT-style impedance control implemented on Damiao motors for hybrid force–position control, improving safety and compliance during human-robot interaction
- **Gaze-driven interaction** — eye-tracking glasses feed gaze signals into an intent-recognition pipeline that triggers grasp actions
- **Rigid-arm integration** — positioning and reach provided by a rigid manipulator arm developed with the McMaster Robomaster team

## Hardware

| Component | Details |
|---|---|
| Gripper | SpiRobs-inspired soft spiral gripper, TPU, 3D printed on Bambu Lab X1C |
| Microcontroller | STM32 |
| Actuators | Damiao motors |
| Sensing | Eye-tracking glasses |
| Manipulator | Rigid arm (McMaster Robomaster platform) |

## Software / Control Stack

- Embedded C/C++ (STM32 firmware, real-time actuation loop)
- Impedance control (MIT-style force–position control)
- Gaze signal processing / intent-recognition pipeline
- *(Add specific frameworks, repos, or libraries used for eye-tracking and impedance control here)*

## Getting Started

> Fill in with actual setup steps once finalized.

```bash
# Clone the repository
git clone <repo-url>
cd <repo-name>

# Flash STM32 firmware
# ...

# Run the gaze-tracking / intent-recognition module
# ...
```

## Team & Acknowledgments

- Eye-tracking subsystem developed in collaboration with the eye-tracking subteam

## Motivation

This project targets an underserved need: many assistive grasping devices assume intact fine motor control for triggering the device itself. By using gaze as the control input and a compliant soft gripper as the end effector, the system aims to reduce both the motor burden on the user and the risk of unsafe contact forces.

## License

*(Add a license if you plan to open-source this.)*
