"""Continuous six-duck game: sit, choose, beak-tap, chase, sit, swap roles."""
import math
import numpy as np
from flock import Flock
from policy import Intent, circle_command, wrap

def turn_command(error):
    if abs(error)<.10:return (0.,0.,0.)
    # The pretrained gait has a dead zone for small in-place turn commands.
    return (0.,0.,float(np.sign(error)*min(1.7,max(1.25,3*abs(error)))))

class FullGame:
    def __init__(self, seed=0, rounds=3, neutral=False, outfits=True, disabled_tags=False):
        self.seed=seed;self.rng=np.random.default_rng(seed);self.round_limit=rounds;self.neutral=neutral
        self.disabled_tags=disabled_tags
        self.world=Flock(outfits=outfits);self.world.start()
        self.picker='duck0';self.goose=None;self.selected_seat=None;self.last_seat=None
        self.phase='seating';self.phase_time=0.;self.round_time=0.;self.round_index=0
        self.steps=0;self.result=None;self.rounds=[];self.events=[];self.scores={r:0 for r in self.world.roles}
        self.last_angles={r:math.atan2(self.world.observe(r).position[1],self.world.observe(r).position[0]) for r in self.world.roles}
        self.angles=self.last_angles.copy();self.exit_stage={};self.opening_tag=None;self.chase_angle=None
        self.boop_attempts=0;self.retag_armed=False;self.clear_since=None;self.return_stage=None
        self.distance={r:0. for r in self.world.roles};self.previous={r:self.world.observe(r).position[:2] for r in self.world.roles}
        self.min_gravity={r:1. for r in self.world.roles};self.completed=False
        self.watch_range={r:[math.inf,-math.inf] for r in self.world.roles}
        self.pending_catch_time=None

    @property
    def time(self):return float(self.world.data.time)

    def event(self,name,**fields):
        e={'event':name,'time_s':round(self.time,3),'round':self.round_index,**fields};self.events.append(e)

    def transition(self,phase):
        self.phase=phase;self.phase_time=self.time;self.event(phase)

    def choose(self):
        choices=[s for s in self.world.seat_owners if s!=self.last_seat]
        self.selected_seat=int(self.rng.choice(choices));self.last_seat=self.selected_seat
        self.goose=self.world.seat_owners[self.selected_seat];self.round_index+=1
        self.round_time=self.time;self.opening_tag=None;self.boop_attempts=0;self.retag_armed=False;self.clear_since=None
        self.pending_catch_time=None
        a=float(self.world.seat_angles[self.selected_seat]);current=self.angles[self.picker]
        while a-.03<current+.1:a+=2*math.pi
        self.target_angle=a;self.exit_stage={self.picker:'back',self.goose:'prepare_stand'};self.stand_time=None
        self.event('goose_selected',picker=self.picker,goose=self.goose,seat=self.selected_seat)
        self.transition('selecting')

    def orbit(self,role,speed=.35):
        o=self.world.observe(role)
        return Intent(twist=tuple(circle_command(o.position,o.yaw,self.world.radius,speed)))

    def oriented(self,role,yaw):
        return abs(wrap(yaw-self.world.observe(role).yaw))<.13

    def face(self,role,yaw):return Intent(twist=turn_command(wrap(yaw-self.world.observe(role).yaw)),direct_head=True)

    def approach(self,role,target,stop_distance):
        o=self.world.observe(role);delta=np.asarray(target)[:2]-o.position[:2];distance=float(np.linalg.norm(delta))
        err=wrap(math.atan2(delta[1],delta[0])-o.yaw)
        if distance<=stop_distance:return Intent(direct_head=True),True
        if abs(err)>.35:return Intent(twist=turn_command(err),direct_head=True),False
        return Intent(twist=(.30,0,float(np.clip(3*err,-1,1))),direct_head=True),False

    def exit(self,role):
        stage=self.exit_stage[role];o=self.world.observe(role);r=np.linalg.norm(o.position[:2]);a=math.atan2(o.position[1],o.position[0])
        if stage=='prepare_stand':
            distance=np.linalg.norm(o.position[:2]-self.world.observe(self.picker).position[:2])
            # The stand policy moves backwards: wait until the picker clears its path.
            if self.time-self.opening_tag>1.2 and self.exit_stage[self.picker]=='run' and distance>.32:
                self.exit_stage[role]='stand';self.stand_time=self.time
                self.event('stand_started',duck=role,clearance_m=round(float(distance),5))
            return Intent(mode='sit',direct_head=True)
        if stage=='stand':
            # Switch back to the walking controller once physically standing;
            # continuing the transition network makes it drift into the runner.
            if self.time-self.stand_time>.45 and o.position[2]>.108 and -o.gravity[2]>.97 and np.linalg.norm(o.gyro)<1.5:
                self.exit_stage[role]='back'
                self.event('standing_ready',duck=role,upright_cosine=round(float(-o.gravity[2]),5),angular_speed=round(float(np.linalg.norm(o.gyro)),5))
            return Intent(mode='stand',direct_head=True)
        if stage=='back':
            if r>self.world.radius-.015:self.exit_stage[role]='turn'
            return Intent(twist=(-.40,0,0),direct_head=True)
        if stage=='turn':
            if self.oriented(role,a+math.pi/2):self.exit_stage[role]='run'
            return self.face(role,a+math.pi/2)
        return self.orbit(role)

    def chase(self):
        w=self.world;o=w.observe(self.goose);target=w.observe(self.picker).position
        delta=target[:2]-o.position[:2];dist=float(np.linalg.norm(delta))
        cmd=circle_command(o.position,o.yaw,w.radius,.34)
        bearing=wrap(math.atan2(delta[1],delta[0])-o.yaw)
        if dist<.42:
            if abs(bearing)>.45:
                return Intent(twist=turn_command(bearing),direct_head=True)
            cmd=np.array([.34 if dist>.17 else .0,0.,np.clip(3*bearing,-1.5,1.5)])
        if dist<.26:
            if dist<.17:cmd[0]=.30
            return Intent(twist=tuple(cmd),head=(-.25,-.15,float(np.clip(bearing,-.45,.45)),0),direct_head=True)
        return Intent(twist=tuple(cmd))

    def begin_return(self,role,seat):
        self.return_role=role;self.return_seat=seat;self.return_stage='turn'
        self.return_time=self.time
        a=float(self.world.seat_angles[seat]);current=self.angles[role]
        if abs(wrap(current-a))>.22:
            while a-.03<current:a+=2*math.pi
            self.return_angle=a;self.return_stage='orbit'

    def return_to_seat(self):
        role=self.return_role;w=self.world;a=float(w.seat_angles[self.return_seat]);o=w.observe(role)
        seat=np.array([w.seat_radius*math.cos(a),w.seat_radius*math.sin(a)])
        heading=math.atan2(seat[1]-o.position[1],seat[0]-o.position[0])
        if self.return_stage=='orbit':
            if self.angles[role]>=self.return_angle-.03:self.return_stage='turn'
            return self.orbit(role,.33),False
        if self.return_stage=='turn':
            if self.oriented(role,heading):self.return_stage='approach'
            return self.face(role,heading),False
        if self.return_stage=='approach':
            cmd,arrived=self.approach(role,seat,.045)
            if arrived:self.return_stage='align'
            return cmd,False
        if self.return_stage=='align':
            # Sit facing the circle, rather than a noisy bearing to a nearby point.
            if self.oriented(role,a+math.pi):
                self.return_stage='settle';self.return_time=self.time
            return self.face(role,a+math.pi),False
        if self.return_stage=='settle':
            if self.time-self.return_time>.8 and -o.gravity[2]>.97 and np.linalg.norm(o.gyro)<.5:
                self.return_stage='sit';self.return_time=self.time
                self.event('seat_settled',duck=role,upright_cosine=round(float(-o.gravity[2]),5),angular_speed=round(float(np.linalg.norm(o.gyro)),5))
            return Intent(direct_head=True),False
        done=self.time-self.return_time>1.8 and o.position[2]<.078 and o.gravity[2]<-.85
        return Intent(mode='sit',direct_head=True),done

    def finish_round(self,outcome):
        winner=self.picker if outcome=='escaped' else self.goose
        if outcome!='caught' or self.pending_catch_time is None:self.scores[winner]+=1
        self.rounds.append({'round':self.round_index,'picker':self.picker,'goose':self.goose,
                            'seat':self.selected_seat,'result':outcome,'winner':winner,
                            'opening_tag_s':round(self.opening_tag,3),'finished_s':round(self.time,3),
                            'scored_s':round(self.pending_catch_time if outcome=='caught' and self.pending_catch_time is not None else self.time,3),
                            'duration_s':round(self.time-self.round_time,3)})
        self.event(outcome,winner=winner)
        if outcome=='escaped':
            self.world.seat_owners[self.selected_seat]=self.picker
            self.picker=self.goose
        if len(self.rounds)>=self.round_limit:
            self.result='complete';self.completed=True;self.transition('complete')
        else:self.transition('intermission')

    def step(self):
        if self.result:raise RuntimeError('Finished')
        w=self.world
        target=w.observe(self.picker).position
        commands={}
        for index,r in enumerate(w.roles):
            watch_target=target
            if self.goose and self.phase in ('chase','exiting','returning') and int(self.time/4+index*.8)%3==0:
                watch_target=w.observe(self.goose).position
            commands[r]=w.watch(r,watch_target,self.time)
        commands[self.picker]=Intent()
        if self.goose:commands[self.goose]=Intent(mode='sit',direct_head=True)
        elapsed=self.time-self.phase_time
        if self.phase=='seating':
            if elapsed>3.:self.choose()
        elif self.phase=='selecting':
            commands[self.picker]=self.orbit(self.picker)
            if self.angles[self.picker]>=self.target_angle-.03:self.transition('turn_to_goose')
        elif self.phase=='turn_to_goose':
            o=w.observe(self.picker);target=w.observe(self.goose).position
            heading=math.atan2(target[1]-o.position[1],target[0]-o.position[0])
            commands[self.picker]=self.face(self.picker,heading)
            if self.oriented(self.picker,heading):self.transition('approach_goose')
        elif self.phase=='approach_goose':
            commands[self.picker],arrived=self.approach(self.picker,w.observe(self.goose).position,.13)
            if arrived:self.transition('beak_tap')
        elif self.phase=='beak_tap':
            commands[self.picker]=Intent(twist=(.30 if elapsed>.8 else 0.,0,0),head=(-.6,.6,0,0),direct_head=True)
            if self.disabled_tags:commands[self.picker]=Intent(direct_head=True)
            if elapsed>4.:
                self.boop_attempts+=1
                if self.disabled_tags:self.result='opening_tag_disabled'
                elif self.boop_attempts>=4:self.result='opening_tag_failed'
                else:self.transition('nudge_closer')
        elif self.phase=='nudge_closer':
            commands[self.picker]=Intent(twist=(.30,0,0),direct_head=True)
            if elapsed>.25:self.transition('beak_tap')
        elif self.phase in ('exiting','chase','returning'):
            for role in (self.picker,self.goose):
                commands[role]=self.exit(role) if self.exit_stage[role]!='run' else (self.chase() if role==self.goose else self.orbit(role,.40))
            if self.exit_stage[self.picker]=='run' and self.chase_angle is None:
                self.chase_angle=self.angles[self.picker];self.event('chase_started')
            if self.phase=='exiting' and all(s=='run' for s in self.exit_stage.values()):self.transition('chase')
            if self.neutral and all(stage=='run' for stage in self.exit_stage.values()):commands[self.picker]=Intent()
            if self.phase=='chase' and not self.neutral and self.angles[self.picker]>=self.target_angle+2*math.pi-.18:
                self.begin_return(self.picker,self.selected_seat);self.transition('returning')
            if self.phase=='returning':
                commands[self.picker],done=self.return_to_seat()
                if done:self.finish_round('escaped')
        elif self.phase=='intermission':
            commands[self.picker]=self.orbit(self.picker,.30)
            if elapsed>1.5:
                self.chase_angle=None;self.choose()
        elif self.phase=='caught_return':
            commands[self.picker]=self.orbit(self.picker,.32)
            commands[self.goose],done=self.return_to_seat()
            if done:self.finish_round('caught')
        elif self.phase=='caught_clear':
            commands[self.picker]=Intent(direct_head=True)
            commands[self.goose]=Intent(twist=(-.40,0,0),direct_head=True)
            distance=float(np.linalg.norm(w.observe(self.picker).position[:2]-w.observe(self.goose).position[:2]))
            if elapsed>1.2 and distance>.28:
                self.begin_return(self.goose,self.selected_seat);self.transition('caught_return')
        contacts=w.step(commands);self.steps+=1
        for r in w.roles:
            o=w.observe(r);a=math.atan2(o.position[1],o.position[0]);self.angles[r]+=wrap(a-self.last_angles[r]);self.last_angles[r]=a
            self.distance[r]+=float(np.linalg.norm(o.position[:2]-self.previous[r]));self.previous[r]=o.position[:2].copy()
            self.min_gravity[r]=min(self.min_gravity[r],float(-o.gravity[2]))
            if commands[r].mode=='sit':
                yaw=float(o.joint_positions[7]);self.watch_range[r][0]=min(self.watch_range[r][0],yaw);self.watch_range[r][1]=max(self.watch_range[r][1],yaw)
            if o.gravity[2]>-.55 or o.position[2]<.028:
                self.result='fall';self.event('fall',duck=r)
            if np.linalg.norm(o.position[:2])>1.25:
                self.result='out_of_bounds';self.event('out_of_bounds',duck=r)
        if self.phase=='beak_tap' and w.beak_contact(self.picker,self.goose):
            self.opening_tag=self.time;self.event('physical_beak_tap',actor=self.picker,target=self.goose,
                                                 contact=w.beak_contact_details(self.picker,self.goose))
            self.transition('exiting')
        if self.phase in ('exiting','chase','returning'):
            pair=any({a,b}=={self.picker,self.goose} for a,b,*_ in contacts)
            if not pair:
                if self.clear_since is None:self.clear_since=self.time
                if self.time-self.clear_since>.5:self.retag_armed=True
            else:self.clear_since=None
            if self.retag_armed and self.exit_stage[self.goose]=='run' and commands[self.goose].head[0]<-.1 and w.beak_contact(self.goose,self.picker):
                self.event('physical_beak_tag_back',actor=self.goose,target=self.picker,
                           contact=w.beak_contact_details(self.goose,self.picker))
                if self.neutral and self.round_limit==1:self.finish_round('caught')
                else:
                    # Recover along the outside before going back to the goose's seat.
                    self.pending_catch_time=self.time;self.scores[self.goose]+=1
                    self.transition('caught_clear')
        if self.time-self.round_time>150 and self.phase not in ('seating','complete'):
            self.result='round_timeout';self.event('round_timeout')
        return self.result

    def report(self):
        return {'seed':self.seed,'result':self.result,'rounds':self.rounds,'events':self.events,
                'neutral_navigation':self.neutral,'disabled_tag_gesture':self.disabled_tags,
                'scores':self.scores,'elapsed_s':round(self.time,3),'control_steps':self.steps,
                'policy_calls':{r:p.calls for r,p in self.world.policies.items()},
                'mode_calls':{r:p.mode_calls for r,p in self.world.policies.items()},
                'joint_target_range_rad':{r:[round(p.minimum,5),round(p.maximum,5)] for r,p in self.world.policies.items()},
                'assistance':'No fixed bases, tethers, external forces, or balance assistance. XML PD actuators; not BAM.',
                'costumes':'Non-colliding visual overalls/caps; 20 mg passive rotor per duck, spun only by initial reset velocity.',
                'distance_m':{r:round(x,4) for r,x in self.distance.items()},
                'minimum_upright_cosine':self.min_gravity,
                'watch_head_yaw_range_rad':{r:[round(x,3) if math.isfinite(x) else None for x in v] for r,v in self.watch_range.items()}}
