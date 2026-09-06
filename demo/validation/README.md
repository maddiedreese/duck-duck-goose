# Verified Linux stability repair

The previous public build could keep driving the stand-transition network after
a duck was already upright, move a goose into the picker's exit path, and switch
from walking into sitting before its posture settled. The fix waits for observed
clearance before standing, switches controllers when standing posture is ready,
and aligns and settles before sitting. These are actuator commands in the existing
scripted controller; robot physics, colliders, checkpoints and outfits are unchanged.

The neutral comparison now disables picker navigation only after both ducks have
exited to the running lane, so it shares the same physical setup as the full game.

| Check | Original HIM test | Repaired macOS | Repaired HIM Linux |
| --- | --- | --- | --- |
| Automated tests | 4/6 passed | 7/7 passed | 7/7 passed |
| Seeds 1–20, two rounds each | 15/20 runs complete | 20/20 complete | 20/20 complete |
| Completed trial rounds | 35/40 | 40/40 | 40/40 |
| Seed 0, three-round reference | Fall in round 2 | Complete, 187.74 s | Complete, 186.86 s |
| Neutral navigation comparison | Catch at 67.54 s | Catch at 53.62 s | Catch at 49.52 s |
| Reach-disabled comparison | No opening tap | No opening tap | No opening tap |

All times are simulated seconds. The seventh test repeats the five original
Linux failure seeds. Every benchmark trial is retained, and an incomplete trial
now causes the command to return a failure status after saving its evidence.

macOS used Apple Silicon and Python 3.12.14. HIM used Linux x86_64, Python 3.12.3
and NVIDIA L4 rendering. Both used the pinned MuJoCo 3.12.0, ONNX Runtime 1.29.0
and NumPy 2.5.2 dependencies. Source and checkpoint hashes in both evidence files
match the revised project. No new network was trained.

The final ZIP was extracted on the HIM machine and executed with
`./run.sh --benchmark 20` using the pinned environment. The launch script selected
EGL automatically; the standard image required Ubuntu EGL/OpenGL libraries.
The entire run returned success. Physics and inference ran on CPU; graphics
were verified as NVIDIA L4. All final artifacts were downloaded and verified
against remote SHA-256 checksums before shutdown.

The main video is 188.92 seconds (27,280,839 bytes); the comparison is 51.56 seconds
(6,918,318 bytes). Both are 1280 × 800 at 25 fps, with a labeled two-second final
hold. Both passed full decode checks and visual inspection. They show the actual
final evaluated episodes, including all three reference rounds.

These results establish the tested platform/seed cases, not universal robustness
or hardware readiness. The earlier failure record is preserved locally, and the
original public source is available in commit
`06034721599de4ea92ff69f56428999be2b60b75`.

The HIM repair machine was confirmed stopped after artifact verification. Its
hard ceiling was 93 credits and its one-hour limit was not extended.
