"""Shared six-duck scene and attentive, rate-limited watching behavior."""
import math
import mujoco
import numpy as np
from simulation import World
from policy import Intent,wrap

class Flock(World):
    def __init__(self, count=6, seat_radius=.48, route_radius=.78, outfits=True):
        self.count=count
        self.roles=tuple('duck'+str(i) for i in range(count))
        self.seat_radius=seat_radius
        self.seat_angles=np.arange(count-1)*2*math.pi/(count-1)
        super().__init__(radius=route_radius,roles=self.roles,outfits=outfits)
        self.seat_owners={i:self.roles[i+1] for i in range(count-1)}
        self.gaze={r:np.zeros(4) for r in self.roles}
        self.contact_log=[]

    def start(self):
        placements={self.roles[0]:(self.radius*math.cos(-.65),self.radius*math.sin(-.65),-.65+math.pi/2)}
        for i,role in self.seat_owners.items():
            a=self.seat_angles[i]
            placements[role]=(self.seat_radius*math.cos(a),self.seat_radius*math.sin(a),a+math.pi)
        self.reset_at(placements)
        for i,role in enumerate(self.roles):
            joint=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,role+'/propeller_hinge')
            if joint>=0:self.data.qvel[int(self.model.jnt_dofadr[joint])]=12.+i*1.8
        mujoco.mj_forward(self.model,self.data)

    def step(self,commands):
        for role,policy in self.policies.items():
            self.data.ctrl[self.ids[role]['ctrl']]=policy.act(self.observe(role,commands[role]))
        self.contact_log=[]
        for _ in range(4):
            mujoco.mj_step(self.model,self.data)
            self.contact_log.extend(self.contacts())
        return self.contact_log

    def watch(self,role,target,time,posture='sit'):
        """Each spectator tracks the action, briefly tilts, and leads moving targets."""
        index=self.roles.index(role)
        o=self.observe(role)
        bearing=math.atan2(target[1]-o.position[1],target[0]-o.position[0])
        yaw=np.clip(wrap(bearing-o.yaw),-1.35,1.35)
        # Head pitch is a small downward gaze; restrained individual tilts avoid bobbleheads.
        desired=np.array([0.,.03+.015*math.sin(time*.85+index),yaw,.025*math.sin(time*.7+index*1.7)])
        self.gaze[role]+=np.clip(desired-self.gaze[role],-.014,.014)
        return Intent(mode=posture,head=tuple(self.gaze[role]),direct_head=True)

    def beak_contact(self,actor,target):
        return self.beak_contact_details(actor,target) is not None

    def beak_contact_details(self,actor,target):
        head=self.model.body(actor+'/jaw_soft').id
        for a,b,ga,gb,pos in self.contact_log:
            if {a,b}!={actor,target}:continue
            own=ga if a==actor else gb
            mesh=int(self.model.geom_dataid[own])
            mesh_name=self.model.mesh(mesh).name if mesh>=0 and self.model.geom_type[own]==mujoco.mjtGeom.mjGEOM_MESH else ''
            tip=self.data.site(actor+'/mouth_tip').xpos
            if int(self.model.geom_bodyid[own])==head and mesh_name in ('jaw','bottom_head_shell') and np.linalg.norm(pos-tip)<.045:
                other=gb if a==actor else ga
                other_mesh=int(self.model.geom_dataid[other])
                return {'actor_mesh':mesh_name,'target_mesh':self.model.mesh(other_mesh).name if other_mesh>=0 else None,
                        'contact_position_m':[round(float(x),5) for x in pos],
                        'distance_from_beak_tip_m':round(float(np.linalg.norm(pos-tip)),5)}
        return None
