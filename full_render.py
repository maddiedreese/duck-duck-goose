"""Live field and close-up cameras, with identity/role/score overlays."""
from pathlib import Path
import math
import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image,ImageDraw
from render import font,PAPER,INK,MUTED
from costumes import PALETTE

PHASES={'seating':'Take your places','selecting':'Duck... duck...',
        'turn_to_goose':'Who will it be?','approach_goose':'A little closer...',
        'beak_tap':'Ready to boop','nudge_closer':'One tiny step',
        'exiting':'GOOSE!','chase':'Run, little ducks!',
        'returning':'Find the empty seat','intermission':'Your turn!',
        'caught_return':'Tagged! Back to your seat','caught_clear':'Boop! A little space...','complete':'A lovely little game'}

class FullRecorder:
    def __init__(self,game,path):
        self.game=game;self.path=Path(path);self.frames=0;self.snapshots=set()
        self.renderer=mujoco.Renderer(game.world.model,height=720,width=960)
        self.close_renderer=mujoco.Renderer(game.world.model,height=200,width=280)
        self.camera=mujoco.MjvCamera();self.camera.lookat[:]=[0,0,.055]
        self.camera.distance=2.6;self.camera.azimuth=35;self.camera.elevation=-44
        self.close_camera=mujoco.MjvCamera();self.close_camera.distance=.72;self.close_camera.elevation=-22
        self.close_target=None;self.close_azimuth=None
        self.opt=mujoco.MjvOption();self.opt.geomgroup[3]=0
        self.writer=imageio.get_writer(str(path),fps=25,codec='libx264',quality=6,macro_block_size=16,pixelformat='yuv420p')

    def capture(self):
        g=self.game;w=g.world
        self.renderer.update_scene(w.data,camera=self.camera,scene_option=self.opt)
        canvas=Image.new('RGB',(1280,800),PAPER);canvas.paste(Image.fromarray(self.renderer.render()),(0,80))
        d=ImageDraw.Draw(canvas);d.rectangle((960,80,1280,800),fill=PAPER)
        d.line((960,104,960,780),fill='#d8ded2')
        d.text((28,11),'Duck Duck Goose',font=font(34,True),fill=INK)
        subtitle='Comparison: runner navigation disabled once both ducks exit.' if g.neutral else 'Six little robots. One very important boop.'
        d.text((30,54),subtitle,font=font(14),fill=MUTED)
        d.rounded_rectangle((1090,24,1255,55),radius=15,fill=INK)
        d.text((1105,30),f'ROUND {g.round_index or 1} OF {g.round_limit}',font=font(13,True),fill=PAPER)
        d.text((985,103),PHASES.get(g.phase,g.phase),font=font(20,True),fill=INK)
        d.text((985,139),f'{g.time:06.2f}',font=font(38),fill=INK)
        d.text((1169,161),'sim seconds',font=font(11),fill=MUTED)
        d.line((985,195,1255,195),fill='#d8ded2')
        for i,role in enumerate(w.roles):
            name,hexcolor,_=PALETTE[i];y=214+i*42
            d.ellipse((987,y+3,999,y+15),fill=hexcolor)
            d.text((1008,y-2),name,font=font(16,True),fill=INK)
            if role==g.picker:label='IT'
            elif role==g.goose and g.opening_tag is not None and g.phase not in ('intermission','selecting'):label='GOOSE'
            else:label='WATCHING'
            d.text((1112,y+1),label,font=font(10,True),fill=MUTED)
            d.text((1236,y-5),str(g.scores[role]),font=font(22,True),fill=INK)
        tapping=g.phase in ('turn_to_goose','approach_goose','beak_tap','nudge_closer','exiting')
        d.text((987,480),'BEAK CAM' if tapping else 'A CLOSER LOOK',font=font(11,True),fill=MUTED)
        actor=g.goose if g.neutral and g.phase=='chase' else g.picker
        pos=w.observe(actor).position
        target=pos+np.array([0,0,.045])
        if g.goose and g.phase in ('approach_goose','beak_tap','nudge_closer','exiting'):
            target=(pos+w.observe(g.goose).position)/2+np.array([0,0,.055])
        yaw=w.observe(actor).yaw
        azimuth=math.degrees(yaw)+(90 if tapping else 160)
        self.close_camera.distance=.58 if tapping else .72
        if self.close_target is None:self.close_target=target.copy();self.close_azimuth=azimuth
        self.close_target+=.12*(target-self.close_target)
        angle_error=(azimuth-self.close_azimuth+180)%360-180
        self.close_azimuth+=float(np.clip(.1*angle_error,-2.,2.))
        self.close_camera.lookat[:]=self.close_target;self.close_camera.azimuth=self.close_azimuth
        self.close_renderer.update_scene(w.data,camera=self.close_camera,scene_option=self.opt)
        canvas.paste(Image.fromarray(self.close_renderer.render()),(980,501))
        d=ImageDraw.Draw(canvas)
        d.text((986,716),'Real joints. Real contact. Tiny overalls.',font=font(12,True),fill=INK)
        d.text((986,739),'Scripted game + pretrained robot skills',font=font(11),fill=MUTED)
        d.text((986,759),'Simulation only / seed '+str(g.seed),font=font(11),fill=MUTED)
        recent=[e for e in g.events if e['event'].startswith('physical_beak') and g.time-e['time_s']<1.6]
        if recent:
            e=recent[-1];actorname=PALETTE[w.roles.index(e['actor'])][0];targetname=PALETTE[w.roles.index(e['target'])][0]
            msg=f'BOOP!  {actorname} tagged {targetname}.'
            d.rounded_rectangle((28,102,540,145),radius=13,fill=INK)
            d.text((45,113),msg,font=font(18,True),fill=PAPER)
        if g.result:
            msg='GAME COMPLETE / Final measured state' if g.completed else f'RUN ENDED / {g.result}'
            d.rounded_rectangle((28,742,590,782),radius=12,fill=INK)
            d.text((44,753),msg,font=font(16,True),fill=PAPER)
        frame=np.asarray(canvas);self.writer.append_data(frame);self.frames+=1
        wanted=None
        if g.time>=8 and 'flock' not in self.snapshots:wanted='flock'
        if recent and 'boop' not in self.snapshots:wanted='boop'
        if g.phase=='chase' and 'chase' not in self.snapshots:wanted='chase'
        if g.result:wanted='final'
        if wanted:
            canvas.save(self.path.with_name(self.path.stem+'-'+wanted+'.png'));self.snapshots.add(wanted)
        return frame

    def close(self,final=None):
        if final is not None:
            for _ in range(50):self.writer.append_data(final);self.frames+=1
        self.writer.close();self.renderer.close();self.close_renderer.close()
