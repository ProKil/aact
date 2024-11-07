# Teleoperating Robots with AAct, Quest, and Stretch

The latency of the AAct system is low enough to allow for teleoperating robots in real-time. This is a powerful capability that can be used for a variety of applications, such as teleoperating a robot to perform a task in a remote location, collecting ego-centric (or together with exocentric) data for training robotics models, or deploying and evaluating models in the real world.

In this demo (live demoed at CoRL 2024), we are going to use Meta Oculus Quest 3 / Pro and Stretch 3 mobile manipulator.

## Prerequisites

### Hardware

- Meta Quest 3 / Pro.
- Stretch 3 mobile manipulator or Stretch 2R with upgraded webcam.

### Software

- Python 3.10.

## Steps

The overall steps are:

- Launch Stretch control loop.
- Launch AAct nodes on Stretch.
- Launch AAct nodes on a local machine.
- Build and launch app on Meta Quest.

### Launch Stretch control loop

Before running nodes on stretch, please do these:

1. Homing: `python -m teleop.stretch_home`
2. Running deamon control loop in a tmux or nohup or screen: `python -m teleop.stretch_control_loop`

### Launch AAct nodes on Stretch

You can easily launch the AAct nodes on Stretch by running the following command:

```bash
aact run-dataflow dataflows/examples/stretch_zmq_streaming.toml
```

### Launch AAct nodes on a local machine

Before this step, please get the IP of your Oculus Quest. And change line 40 in `dataflows/examples/quest_local_redis.toml` to your IP.

Then, you can launch the AAct nodes on a local machine by running the following command:
```bash
aact run-dataflow dataflows/examples/quest_local_redis.toml
```

### Build and launch app on Meta Quest

We provide the APK file for the app. You can install it on your Meta Quest by running the following command:

```bash
adb install -r app.apk
```

But you can also build the app manually, by building the Unity Project.


## Demo

<iframe width="560" height="315" src="https://www.youtube.com/embed/OChbSQad4ps?si=QQe9MW6Aie_FvRKA" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
