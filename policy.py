"""Scripted navigation composed with Pollen Robotics' pretrained walking policy."""
from dataclasses import dataclass
from pathlib import Path
import math
import numpy as np
import onnxruntime as ort

JOINTS = ('left_hip_yaw left_hip_roll left_hip_pitch left_knee left_ankle '
          'neck_pitch head_pitch head_yaw head_roll '
          'right_hip_yaw right_hip_roll right_hip_pitch right_knee right_ankle').split()
HOME = np.array([0, -.08726646259971647, -.457924, -.004940, .452984,
                 .3490658503988659, .3490658503988659, 0, 0,
                 0, .08726646259971647, .457924, .004940, -.452984])
CONTROL_DT = .02
_SESSIONS = {}

def wrap(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi

@dataclass
class Intent:
    twist: tuple = (0., 0., 0.)
    mode: str = 'walk'
    head: tuple = (0., 0., 0., 0.)
    direct_head: bool = False

@dataclass
class Observation:
    position: np.ndarray
    yaw: float
    gyro: np.ndarray
    gravity: np.ndarray
    joint_positions: np.ndarray
    joint_velocities: np.ndarray
    command: np.ndarray
    mode: str = 'walk'
    direct_head: bool = False

class WalkingPolicy:
    """act() is the only producer of robot joint targets after reset."""
    def __init__(self, checkpoint=None):
        checkpoint = checkpoint or Path(__file__).parent / 'assets/policies/BEST_alpha_walking.onnx'
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        self.options = options
        self.checkpoint = Path(checkpoint)
        self.session = self.load_session(self.checkpoint)
        self.reset()

    def load_session(self, checkpoint):
        key = str(checkpoint.resolve())
        if key not in _SESSIONS:
            _SESSIONS[key] = ort.InferenceSession(key, self.options, providers=['CPUExecutionProvider'])
        return _SESSIONS[key]

    def reset(self):
        self.last_action = np.zeros(14, dtype=np.float32)
        self.calls = 0
        self.minimum = math.inf
        self.maximum = -math.inf
        self.mode_calls = {}
        self.head_smooth = np.zeros(4)

    def act(self, observation):
        command = np.zeros(13, dtype=np.float32)
        command[:len(observation.command)] = observation.command
        if observation.mode in ('sit','stand'):
            command[:3] = [int(observation.mode == 'sit'),0,0]
            session = self.load_session(self.checkpoint.parent/'BEST_alpha_sitstand.onnx')
        elif observation.mode == 'walk':
            session = self.session
        else:raise ValueError('Unknown posture mode: '+observation.mode)
        obs = np.concatenate([observation.gyro, observation.gravity,
                              observation.joint_positions - HOME,
                              observation.joint_velocities, self.last_action, command]).astype(np.float32)
        action = session.run(['actions'], {'obs': obs[None, :]})[0].reshape(14)
        if not np.all(np.isfinite(action)):
            raise ValueError('Non-finite policy action')
        # Match the XML's explicit control range; retain applied actions in history.
        targets = np.clip(HOME + action, -10, 10)
        if observation.direct_head:
            # Bounded scripted gaze/reach lives inside the policy and drives real joints.
            self.head_smooth += np.clip(command[3:7]-self.head_smooth, -.025, .025)
            targets[5:9] = np.clip(HOME[5:9]+self.head_smooth,
                                    [-1.45,-1.45,-2.7,-.35], [1.,1.45,2.7,.35])
        else:
            self.head_smooth = targets[5:9]-HOME[5:9]
        self.last_action = (targets - HOME).astype(np.float32)
        self.calls += 1
        self.mode_calls[observation.mode] = self.mode_calls.get(observation.mode,0)+1
        self.minimum = min(self.minimum, float(targets.min()))
        self.maximum = max(self.maximum, float(targets.max()))
        return targets

def circle_command(position, yaw, radius, speed):
    """World-state navigation; no camera perception or learned game strategy."""
    angle = math.atan2(position[1], position[0])
    error_radius = float(np.linalg.norm(position[:2])) - radius
    desired = angle + math.pi / 2 + math.atan2(error_radius, .25)
    error = wrap(desired - yaw)
    forward = speed * max(.2, math.cos(error))
    turn = np.clip(speed / radius + 2.5 * error, -1., 1.)
    return np.array([forward, 0., turn])
