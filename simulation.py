"""Independent real, free-base Microducks sharing one MuJoCo physics world."""
from pathlib import Path
import copy
import math
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from policy import JOINTS, HOME, Observation, WalkingPolicy, CONTROL_DT, Intent

ROOT = Path(__file__).parent
COLORS = {'runner': '.97 .60 .36 1', 'goose': '.38 .66 .66 1'}

def scene_xml(radius=.65, roles=('runner','goose'), outfits=False):
    source = ET.parse(ROOT / 'assets/robot/robot_allcollisions.xml').getroot()
    root = copy.deepcopy(source)
    root.set('model', 'duck_duck_goose')
    root.find('compiler').set('meshdir', str(ROOT / 'assets/robot/meshes'))
    ET.SubElement(root.find('asset'),'texture',type='skybox',builtin='gradient',
                  rgb1='.93 .92 .85',rgb2='.72 .78 .69',width='512',height='3072')
    for tag in ('worldbody', 'sensor', 'actuator', 'equality', 'contact', 'keyframe'):
        for item in list(root.findall(tag)):
            root.remove(item)
    ET.SubElement(root, 'option', timestep='.005', integrator='implicitfast')
    visual = ET.SubElement(root, 'visual')
    ET.SubElement(visual, 'global', offwidth='1280', offheight='960')
    ET.SubElement(visual, 'quality', shadowsize='2048')
    ET.SubElement(visual, 'headlight', diffuse='.35 .35 .35', ambient='.3 .3 .3', specular='.05 .05 .05')
    world = ET.SubElement(root, 'worldbody')
    ET.SubElement(world, 'light', pos='0 -1 3', dir='0 .2 -1', diffuse='.8 .8 .8', castshadow='true')
    ET.SubElement(world, 'light', pos='2 2 2', dir='-1 -1 -1', diffuse='.25 .25 .25', castshadow='false')
    ET.SubElement(world, 'geom', name='floor', type='plane', size='4 4 .05', rgba='.78 .80 .72 1', friction='1 .005 .0001')
    # Flat painted markings have no collision: they cannot propel the robots.
    for i in range(96):
        a = i * 2 * math.pi / 96
        for r in (radius - .22, radius + .22):
            ET.SubElement(world, 'geom', type='sphere', pos=f'{r*math.cos(a)} {r*math.sin(a)} .001',
                          size='.008', rgba='.39 .43 .36 1', contype='0', conaffinity='0')
    if len(roles)==2:
        ET.SubElement(world, 'geom', name='safe_spot', type='cylinder', pos=f'{radius-.13} 0 .001',
                      size='.14 .001', rgba='.44 .65 .39 1', contype='0', conaffinity='0')
    else:
        for i in range(len(roles)-1):
            a=i*2*math.pi/(len(roles)-1)
            ET.SubElement(world,'geom',name='seat_'+str(i),type='cylinder',
                          pos=f'{.55*math.cos(a)} {.55*math.sin(a)} .001',size='.115 .001',
                          rgba='.62 .71 .56 .7',contype='0',conaffinity='0')
    ET.SubElement(world, 'geom', name='center_disc', type='cylinder', pos='0 0 .001',
                  size='.32 .001', rgba='.73 .75 .65 1', contype='0', conaffinity='0')
    sensors = ET.SubElement(root, 'sensor')
    actuators = ET.SubElement(root, 'actuator')
    # Asset and default-class names are shared; all dynamic names/references are unique.
    refs = {'name', 'joint', 'body', 'site', 'objname', 'body1', 'body2', 'joint1', 'joint2'}
    for index,role in enumerate(roles):
        body = copy.deepcopy(source.find('worldbody/body'))
        elements = [body, copy.deepcopy(source.find('sensor')), copy.deepcopy(source.find('actuator'))]
        for part in elements:
            for el in part.iter():
                for key in refs & el.attrib.keys():
                    el.set(key, role + '/' + el.get(key))
        for geom in body.iter('geom'):
            if geom.get('class') == 'visual' and any(x in geom.get('mesh', '') for x in ('shell', 'neck', 'upper_leg')):
                geom.attrib.pop('material', None)
                geom.set('rgba', COLORS.get(role,'.92 .83 .62 1'))
        if outfits:
            from costumes import dress_duck
            dress_duck(body,role,index)
        world.append(body)
        sensors.extend(list(elements[1]))
        actuators.extend(list(elements[2]))
    return ET.tostring(root, encoding='unicode')

class World:
    def __init__(self, radius=.65, roles=('runner','goose'), outfits=False):
        self.radius = radius
        self.model = mujoco.MjModel.from_xml_string(scene_xml(radius, roles, outfits))
        self.data = mujoco.MjData(self.model)
        self.policies = {role: WalkingPolicy() for role in roles}
        self.ids = {}
        for role in self.policies:
            joints = [self.model.joint(role + '/' + x) for x in JOINTS]
            self.ids[role] = dict(
                qpos=np.array([int(j.qposadr[0]) for j in joints]),
                qvel=np.array([int(j.dofadr[0]) for j in joints]),
                ctrl=np.array([self.model.actuator(role + '/' + x).id for x in JOINTS]),
                root=int(self.model.joint(role + '/trunk_base_freejoint').qposadr[0]),
                body=self.model.body(role + '/trunk_base').id,
                gyro=int(self.model.sensor(role + '/imu_ang_vel').adr[0]))
        self.geom_roles = {}
        for i in range(self.model.ngeom):
            name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, int(self.model.geom_bodyid[i])) or ''
            self.geom_roles[i] = name.split('/')[0]

    def reset(self, runner_angle=-.6, goose_angle=0., goose_yaw_offset=0.):
        mujoco.mj_resetData(self.model, self.data)
        for role, angle in [('runner', runner_angle), ('goose', goose_angle)]:
            ids = self.ids[role]
            q = ids['root']
            yaw = angle + math.pi / 2 + (goose_yaw_offset if role == 'goose' else 0.)
            radius = self.radius if role == 'runner' else self.radius-.13
            self.data.qpos[q:q+7] = [radius * math.cos(angle), radius * math.sin(angle), .12,
                                    math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
            self.data.qpos[ids['qpos']] = HOME
            self.policies[role].reset()
        mujoco.mj_forward(self.model, self.data)

    def observe(self, role, command=None):
        ids = self.ids[role]
        b = ids['body']
        rot = self.data.xmat[b].reshape(3, 3)
        mode='walk';direct_head=False
        if isinstance(command,Intent):
            mode=command.mode;direct_head=command.direct_head
            cmd=np.zeros(13);cmd[:3]=command.twist;cmd[3:7]=command.head
        else:cmd=np.zeros(3) if command is None else np.asarray(command)
        return Observation(self.data.xpos[b].copy(), math.atan2(rot[1,0], rot[0,0]),
                           self.data.sensordata[ids['gyro']:ids['gyro']+3].copy(),
                           rot.T @ np.array([0., 0., -1.]),
                           self.data.qpos[ids['qpos']].copy(), self.data.qvel[ids['qvel']].copy(),
                           cmd,mode,direct_head)

    def reset_at(self, placements):
        """Episode reset only: (x, y, yaw) for every duck; no subsequent pose writes."""
        mujoco.mj_resetData(self.model,self.data)
        for role,(x,y,yaw) in placements.items():
            ids=self.ids[role];q=ids['root']
            self.data.qpos[q:q+7]=[x,y,.12,math.cos(yaw/2),0,0,math.sin(yaw/2)]
            self.data.qpos[ids['qpos']]=HOME
            self.policies[role].reset()
        mujoco.mj_forward(self.model,self.data)

    def contacts(self):
        result=[]
        for c in self.data.contact:
            a,b=int(c.geom1),int(c.geom2)
            ra,rb=self.geom_roles[a],self.geom_roles[b]
            if c.dist<=0 and ra!=rb and ra in self.policies and rb in self.policies:
                result.append((ra,rb,a,b,c.pos.copy()))
        return result

    def step(self, commands):
        for role, policy in self.policies.items():
            self.data.ctrl[self.ids[role]['ctrl']] = policy.act(self.observe(role, commands[role]))
        contact = False
        for _ in range(4):
            mujoco.mj_step(self.model, self.data)
            contact |= self.has_tag_contact()
        return contact

    def has_tag_contact(self):
        return bool(self.contacts())

    def fallen(self, role):
        obs = self.observe(role)
        return obs.position[2] < .065 or obs.gravity[2] > -.55
