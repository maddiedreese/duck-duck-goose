"""Non-colliding 3D overalls and lightweight, passive propeller hats."""
import math
import xml.etree.ElementTree as ET

PALETTE = [
    ('Peaches', '#ee9974', (.93,.53,.34)),
    ('Clover', '#83b99b', (.37,.66,.48)),
    ('Lilac', '#b7a2d5', (.63,.48,.78)),
    ('Puddle', '#82b8d6', (.38,.64,.79)),
    ('Butter', '#e5c774', (.89,.72,.32)),
    ('Rosie', '#d78ca5', (.80,.43,.57)),
]

def rgba(c):return ' '.join(str(round(x,5)) for x in (*c,1.))

def dress_duck(body, role, index):
    name,_,color=PALETTE[index%len(PALETTE)]
    dark=tuple(x*.73 for x in color)
    cream=(.96,.87,.64)
    for geom in body.iter('geom'):
        mesh=geom.get('mesh','')
        if geom.get('class')=='visual':
            if any(x in mesh for x in ('shell','neck')):
                geom.attrib.pop('material',None);geom.set('rgba',rgba(cream))
            if mesh in ('upper_leg_left','upper_leg_right','leg'):
                geom.attrib.pop('material',None);geom.set('rgba',rgba(color))
    def g(parent,kind,pos,size,c,**kw):
        return ET.SubElement(parent,'geom',type=kind,pos=pos,size=size,rgba=rgba(c),
                             contype='0',conaffinity='0',group='2',mass='0',**kw)
    # Soft-looking belt, front bib, back panel, straps, patch pocket and brass buttons.
    g(body,'box','-.006 0 -.006','.043 .034 .015',color)
    g(body,'box','.037 0 .019','.003 .027 .027',color)
    g(body,'box','-.050 0 .015','.002 .030 .022',color)
    for side in (-1,1):
        y=side*.020
        g(body,'box',f'-.006 {y} .046','.044 .005 .0025',color)
        g(body,'box',f'.041 {y} .024','.0017 .003 .018',dark)
        g(body,'sphere',f'.043 {y} .037','.0034',(1.,.80,.32))
    g(body,'box','.041 0 .011','.0017 .014 .011',dark)
    g(body,'box','.043 0 .020','.0008 .014 .0007',(.98,.92,.74))
    for side in (-1,1):
        g(body,'box',f'.043 {side*.014} .011','.0008 .0007 .010',(.98,.92,.74))
    # Head local +x is up; this hat frame has conventional +z up and +x forward.
    head=next(b for b in body.iter('body') if b.get('name')==role+'/jaw_soft')
    hat=ET.SubElement(head,'body',name=role+'/hat',pos='.044 0 -.020',quat='.70710678 0 .70710678 0')
    g(hat,'cylinder','0 0 0','.049 .002',dark)
    g(hat,'ellipsoid','0 0 .006','.044 .044 .016',color)
    g(hat,'ellipsoid','.028 0 .001','.035 .029 .002',color)
    g(hat,'cylinder','0 0 .026','.002 .010',(1.,.80,.32))
    g(hat,'sphere','0 0 .037','.0045',(1.,.80,.32))
    rotor=ET.SubElement(hat,'body',name=role+'/propeller',pos='0 0 .039')
    ET.SubElement(rotor,'inertial',pos='0 0 0',mass='.00002',diaginertia='1e-8 1e-8 2e-8')
    ET.SubElement(rotor,'joint',name=role+'/propeller_hinge',type='hinge',axis='0 0 1',
                  limited='false',damping='1e-11',frictionloss='0',armature='0')
    blade_colors=[(.98,.55,.40),(.38,.71,.74),(.98,.81,.36)]
    for k,c in enumerate(blade_colors):
        a=k*2*math.pi/3
        # Each blade is a visible rounded ellipsoid, not a collision/tag surface.
        g(rotor,'ellipsoid',f'{.025*math.cos(a)} {.025*math.sin(a)} 0','.030 .008 .0015',c,
          quat=f'{math.cos(a/2)} 0 0 {math.sin(a/2)}')
