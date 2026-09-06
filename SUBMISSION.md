# HIM Arena submission guide

Source repository: https://github.com/maddiedreese/duck-duck-goose

## Files and exact form values

Prepare the archive with `python package.py`. The source ZIP is uploaded separately
from the generated `results/result.mp4`; do not put the video inside the ZIP.
The delivery folder `arena-submission` beside this project contains the final
copies named `submission.zip` and `result.mp4`, plus this guide and an inventory.

| Section | Value |
| --- | --- |
| Challenge | Microduck · $2,500 Best Sports Sim |
| Robot | Microduck |
| Simulator | MuJoCo |
| What are you uploading? | Policy + simulator |
| Project ZIP | submission.zip |
| Result video | result.mp4 |
| Name | Duck Duck Goose — The Propeller Hat League |
| Caption (optional, 500 characters maximum) | Copy the text below or CAPTION.txt |

Name and Caption appear after selecting both files. The web form currently has
no separate repository URL or run-command field. The README contains both.
For a CLI or any later run-command field, use `./run.sh`.

## Caption (485 characters)

Six Microducks play Duck Duck Goose in colorful overalls and propeller hats. Scripted strategy, gaze and beak-tag gestures use Pollen Robotics’ pretrained walking/sit-stand networks; no new training. Three scored rounds with seated spectators and role swaps. Disabling runner navigation produces a physical catch; disabling reach prevents the opening tap. Free-base MuJoCo physics, no balance assistance. Simulation only; cosmetic costumes. Source and limitations linked in the README.

## Packaging and checks

The source archive contains the runnable Python source, six behavior tests,
small required robot meshes, only the two required final inference checkpoints,
dependency pins, README, licenses and asset provenance. It excludes `.git`,
credentials, `.env`, datasets, logs, caches, environments and generated video.

- Main MP4: 27,269,223 bytes; 1280 × 800, 25 fps, 179.68 seconds.
- Source ZIP: approximately 3.46 MB; exact size and SHA-256 are in the inventory.
- Combined upload: approximately 30.73 MB, below the 100 MB limit.
- MP4 alone is below the 50 MB limit and has passed a complete decode check.
- Six tests passed. Reference: three rounds, 177.64 simulated seconds.
- Additional seeds 1–5: 10/10 rounds completed.
- Navigation-disabled comparison: physical catch at 54.60 s.
- Reach-disabled comparison: no opening tap, stop at 38.92 s.
- Clean ZIP extraction reproduced tests and measured outcomes using the pinned
  local environment. See README for platform limits and honest policy attribution.

The separate tag-back comparison and evidence are available in the GitHub
`demo/` directory as supporting material. Upload the full game as the main video.
The two-second final-state hold is labeled in both videos.

## After filling the form

Click **Upload work in progress** to publish the Arena entry. After reviewing the
public result, mark it ready using Arena's readiness control. The site describes
new uploads as work in progress even when the local project is complete.

The challenge also asks entrants to share their Arena build on X and email the
post link to team@himrobotics.com. No Arena upload, X post or email has been made
by this project preparation step.

The published deadline reads September 8, 2026 at 5:00 PM PST. Check the challenge
page for any changes before final submission. The sports track accepts scripted
controllers; the soccer-specific suggested prompt is not a requirement to change
this game into soccer or train a new policy.

- Form: https://arena.himrobotics.com/build?challenge=microduck-sports-sim-2026#upload
- Challenge: https://arena.himrobotics.com/challenges/microduck-sports
- Rules: https://arena.himrobotics.com/challenge-rules
