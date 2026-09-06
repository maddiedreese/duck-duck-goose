# Attribution and changes

Robot geometry, the MJCF model, and pretrained walking and sit/stand networks
are by Pollen Robotics and the Microduck contributors. Downloaded from the
official `pollen-robotics/microduck-simulator` Hugging Face Space at revision
`e81974b932c7ca1819843b7bb3dcd42e2993e98e` on September 5, 2026:

https://huggingface.co/spaces/pollen-robotics/microduck-simulator

That Space identifies its model and policy sources as:

- https://github.com/pollen-robotics/microduck
- https://github.com/pollen-robotics/microduck_rl

Apache-2.0 license texts from both repositories are included as
`assets/LICENSE-microduck` and `assets/LICENSE-microduck-rl`.
The downloaded MJCF, required STL files, and two inference checkpoints are
retained unmodified. Their hashes and download URLs are in `PROVENANCE.json`.

`simulation.py` transforms the original model in memory: it prefixes instance
names, adds course/render settings, and recolors visual parts. `costumes.py`
adds original, non-colliding 3D garment geometry and tiny passive propeller
rotors. Original robot free joints, inertias, collision geometry and actuator
configuration remain present. The rotor's small nominal inertia is disclosed.

`policy.py` follows the observation layout, home pose, command slots and action
mapping documented in the Space's `app/src/game/constants.js` and `game.js`,
which follow Microduck's inference runtime. It adds scripted head targets,
watching and reaching behaviors. The game, state machine, outfits, evaluation
and presentation are original project code distributed under Apache-2.0.

The upstream networks are used for inference. Their original training was
performed by their upstream authors; this project claims no new training.
No simulator networking, unrelated UI, sounds, or third-party art assets are
included. Rendering uses a locally available system font, which is not bundled.
