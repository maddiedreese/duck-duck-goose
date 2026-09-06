# Duck Duck Goose

Six little Microducks play a continuous game of Duck Duck Goose in MuJoCo.
Five sit in a circle and watch the action. The picker walks around them,
chooses a goose, leans in for a physical beak tap, and runs. The goose stands
up and chases. An escaping picker returns to the empty seat and sits down;
the goose becomes the next picker. After a catch, they separate and the goose
returns to its seat before play resumes.

Peaches, Clover, Lilac, Puddle, Butter, and Rosie each wear different colored
overalls with straps, buttons and pockets, plus a freely spinning propeller hat.
Their names, outfits and scores stay with them when their roles change.

**Source repository:** [https://github.com/maddiedreese/duck-duck-goose](https://github.com/maddiedreese/duck-duck-goose)

[Watch the full game](https://github.com/maddiedreese/duck-duck-goose/blob/main/demo/result.mp4) ·
[Watch the tag-back comparison](https://github.com/maddiedreese/duck-duck-goose/blob/main/demo/tag-back-comparison.mp4) ·
[Recorded evidence](https://github.com/maddiedreese/duck-duck-goose/blob/main/demo/evidence.json)


## Run it

Use Python 3.12 on a desktop with OpenGL. `uv` is recommended; the script also
supports `python3 -m venv`. The first run downloads the pinned Python
dependencies. After that, simulation and inference run entirely locally.

```sh
./run.sh
```

This creates `.venv`, installs `requirements.txt`, runs six tests, records a
three-round game and a tag-back comparison, then evaluates five more seeds.
It produces:

- `results/result.mp4`: the complete three-round reference game, with field
  and close-up cameras, identity/role labels and a measured scoreboard.
- `results/tag-back-comparison.mp4`: a clearly labeled comparison in which
  the runner's navigation is disabled after the opening tap and exit.
- `results/evidence.json`: outcomes, events, physical contact evidence, policy
  calls, action bounds, watching motion ranges, versions and source hashes.
- PNG frames showing the flock, opening tap, chase and final measured state.

For evaluation without a display:

```sh
./run.sh --no-video
```

Options: `--seed 0`, `--rounds 3`, `--benchmark 5`, `--output-dir results`,
and `--skip-comparison-video`. The benchmark uses the next five seeds, with
two rounds each. To use an existing environment, set `DUCK_PYTHON` to its
Python executable. FFmpeg is supplied by `imageio-ffmpeg`.

Tested on Apple Silicon macOS, Python 3.12.14, MuJoCo 3.12.0 and
ONNX Runtime 1.29.0. Other operating systems and physics versions have not
been verified; exact contact timing can vary across platforms.

## What is scripted, learned, and physical?

The game strategy, navigation, gaze and reach gestures are **scripted**.
Walking and sit/stand use Pollen Robotics' published pretrained ONNX networks.
This project trained no new network. The checkpoint normalizers are retained.

Every robot has a free base. At each 20 ms control step,
`WalkingPolicy.act(observation)` produces all 14 of that robot's joint-position
targets. It selects the walking or sit/stand network, then applies bounded
head-joint targets when a scripted watching or reaching gesture is requested.
MuJoCo advances four 5 ms physics steps. The policy runs every control step
for every duck, including those sitting and watching.

The 61-float low-level observation contains gyro, projected gravity, joint
positions relative to the home pose, joint velocities, previous applied action,
and 13 command slots. The game reads true simulator positions and orientations;
it does not use camera perception. Previous-action history includes applied
head overrides. Joint targets are clamped to the XML's [-10, 10] control range;
head targets also have explicit joint limits and rate limits.

The original robot geometry, inertia, free joints and actuator configuration
are reused. The scene uses XML PD actuators and `implicitfast` integration,
not the higher-fidelity BAM actuator model used by the training stack.
There are no tethers, fixed robot bases, external push forces, hidden balance
assistance, mid-game pose resets, or animations driving robot motion.
Initial poses and passive propeller velocities are assigned only at reset.

This is simulation only, with no hardware validation or readiness claim.

## Watching, outfits and deliberate tags

Seated ducks alternate their attention between the picker and the goose,
with different timing and small head tilts. Gaze requests are smoothed and
limited to about ±1.35 radians of yaw; the real head joints move under motor
control. The watching range was limited after larger turns proved unstable.
They remain supported by their own bodies and simulator contact with the floor.

Microduck has no arms. Both the opening tap and the catch therefore use a
deliberate neck reach and beak touch. An opening tap lowers the beak toward
the seated duck; a chase tag reaches toward the standing runner. A score needs
a real inter-robot MuJoCo contact on the actor's jaw/lower-head geometry,
within 45 mm of its mouth-tip site. The chase tag also requires the deliberate
reach command to be active. General body bumps, floor contacts, visual proximity,
and costume intersections do not count.

Overalls and caps are non-colliding visual geometry. Each propeller has a
passive hinge and nominal 20 mg mass, with initial spin set at episode reset;
it is subsequently driven only by physics. These are visual costume models,
not a cloth, aerodynamic, or real garment-mass simulation. Costumes cannot
create success contacts. The original robot colliders are retained underneath.

## Game rules

1. Five ducks sit around the center; one picker walks counterclockwise.
   A seeded random generator selects an occupied seat, excluding the previous
   selection when other seats are available. The same seed reproduces the choices.
2. The picker lines up behind the selected duck, approaches, and leans forward
   for a physical beak tap. A small corrective step is allowed if the first
   reach falls short. No contact means no physical-tag event or chase start.
3. The goose stands, and both ducks move to the outside running lane. The
   goose's stand/reaction interval is 2.4 s. Typical forward command values
   are 0.40 m/s for the picker and 0.34 m/s for the goose; these are requested
   velocities, not measured speed guarantees. Turning and backing out use
   separate bounded commands. This gives the picker an escape opportunity.
4. The goose follows the ring at distance, then turns and reaches toward the
   picker when close. Tag-back detection re-arms only after the opening contact
   has been clear for half a second. Only a deliberate physical beak tag scores.
5. The picker completes the circuit, approaches the empty seat, and must
   physically sit with an upright body before earning the escape point. It
   becomes the seated duck; the goose becomes the next picker.
6. On a catch, the goose earns a point immediately. The ducks back away, the
   goose returns to its seat and sits, and the same picker starts another round.
7. A fall, leaving the bounded play area, a failed opening tap or a round timeout
   ends the run as a reported failure. Such outcomes are never edited into wins.

The game is an intentionally simplified Microduck adaptation. It does not
include hand taps, a learned strategy, sophisticated interception, airborne
running, or unlimited validated rounds. The fixed circle and reference gait
settings are part of the published task, not a general robotics benchmark.

## Verification

| Check | Recorded result |
| --- | --- |
| Reference, seed 0 | 3 complete rounds in 177.64 simulated seconds |
| Selected geese in the reference | Rosie, Puddle, Butter |
| Additional seeds 1–5 | 5 / 5 runs complete; 10 / 10 rounds complete |
| Runner navigation disabled | Physical beak catch at 54.60 s |
| Reach disabled | No opening tap; stops at 38.92 s |
| Catch / separate / return / resume test | Two consecutive caught rounds complete |
| Automated tests | 6 passed |

The default reference completes three rounds with different geese and role
changes. Two causal comparisons are included: disabling the runner's navigation
leads to a beak catch, and disabling the reach prevents the opening tap.
Five additional seeds are evaluated with two rounds each; every result is
retained in `evidence.json`. These seeds vary the selection sequence, not robot
hardware, terrain, sensor quality or actuator parameters.

The six tests cover multi-round role changes and measured tags, the neutral
runner, the disabled reach, catch/separate/return/resume behavior, stable
watching with real head-joint motion and free bases, and reproducible/varied
selection. They also check the absence of external forces and the passive
propeller motion.

The source ZIP was also extracted into a separate directory and rerun using
the pinned local environment. All six tests passed, and the reference and
both causal comparisons reproduced their recorded outcomes and timings.

The reference video is recorded from the same episode that produces its
evidence. Both videos use 25 fps at approximately real-time speed, with a
clearly labeled two-second hold of the final state. The close-up camera shows
the same live physics world. The scoreboard, event captions and role labels
come from measured game events. No outcomes or robot movements are animated
or edited into the video.

## Source and packaging

- `full_game.py`: selection, phases, deliberate tags, scoring and role changes.
- `flock.py`: six-duck world, contact evidence and watching behavior.
- `policy.py`: pretrained inference, motor targets and scripted head gestures.
- `simulation.py`: original robot models and shared MuJoCo scene.
- `costumes.py`: the six outfit palettes, overalls and passive propeller hats.
- `full_render.py` and `render.py`: cameras, scoreboard and local typography.
- `main.py`: repeatable evaluation, comparisons and video/evidence output.
- `test_game.py`: meaningful behavior and physics tests.
- `assets/`: only required model geometry, two inference checkpoints and notices.

```sh
python package.py
```

This creates `../duck-duck-goose-source.zip` and an inventory with file sizes
and SHA-256 hashes. It uses an explicit allowlist and excludes generated
videos, results/logs, virtual environments, caches, credentials and secrets.
See `SUBMISSION.md` for the remaining publication steps and `NOTICE.md` plus
`assets/PROVENANCE.json` for upstream sources and exact asset hashes.
