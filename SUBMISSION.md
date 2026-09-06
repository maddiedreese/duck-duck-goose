# Updated HIM Arena submission

Repository: https://github.com/maddiedreese/duck-duck-goose

## Replace these files

Use the new `arena-submission-v2` delivery folder:

- `submission.zip`: repaired source, required meshes and inference checkpoints,
  seven tests, dependency pins, licenses, provenance and updated README.
- `result.mp4`: the new three-round reference recorded on HIM Linux.
- `CAPTION.txt`: the new 465-character caption below.

The ZIP and video are separate uploads. Do not place either inside the other.
The inventory and delivery manifest list exact file sizes and SHA-256 hashes.
The video is below 50 MB; the combined ZIP and MP4 are below 100 MB.

## Form fields

| Section | Value |
| --- | --- |
| Challenge | Microduck · $2,500 Best Sports Sim |
| Robot | Microduck |
| Simulator | MuJoCo |
| What are you uploading? | Policy + simulator |
| Project ZIP | New submission.zip |
| Result video | New result.mp4 |
| Name | Duck Duck Goose — The Propeller Hat League |
| Caption | Text below |

Name and Caption appear after choosing both files in the new-upload form.
The current web form has no separate repository or run-command field; both are
in README. If a command field is offered, use `./run.sh --benchmark 20` to
reproduce the complete validation, or `./run.sh` for the default five extra seeds.

## Caption

Six Microducks play Duck Duck Goose in colorful overalls and propeller hats. Scripted strategy, gaze and beak tags use Pollen Robotics' pretrained walking/sit-stand networks; no new training. Three scored rounds with watching spectators and role swaps. Verified on macOS and HIM Linux: 7 tests and 20 two-round trials per platform. Free-base MuJoCo physics, no balance assistance. Simulation only; cosmetic costumes. Source and limitations are linked in the README.

## What changed

A goose now recenters its head while seated and waits for the picker to clear
its standing path. Standing ends when observed posture is ready. Returning
players face inward and settle before sitting. These changes keep the original
robot dynamics, colliders, inference checkpoints and costumes intact.

Both macOS and HIM Linux pass seven tests and all twenty two-round trial seeds.
The three-round reference also completes on both platforms. Neutral navigation
is disabled only after both ducks exit; it produces a real beak catch. Disabling
the reaching gesture prevents the opening tap. All outcomes and limitations are
reported in README and the GitHub `demo/validation/` evidence.

The Linux launcher selects EGL on headless hosts. A minimal Ubuntu image needs
`libegl1 libgl1 libopengl0 libegl-mesa0`, as documented in README.

## Finish in Arena

Replace the project ZIP and main video in your existing entry if Arena offers
an update control. Review the new public result and mark it ready. This GitHub
update and file preparation do not themselves change an existing Arena upload.
The tag-back comparison remains supporting material in the repository.

The challenge also asks entrants to share the Arena build on X and email the
post link to team@himrobotics.com. This update does not send those messages.
The published deadline is September 8, 2026 at 5:00 PM PST; check the page for
changes before submitting.

- Sports form: https://arena.himrobotics.com/build?challenge=microduck-sports-sim-2026#upload
- Challenge: https://arena.himrobotics.com/challenges/microduck-sports
- Rules: https://arena.himrobotics.com/challenge-rules
