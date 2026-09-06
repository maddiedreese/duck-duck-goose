import math
import unittest
import mujoco
import numpy as np
from full_game import FullGame
from flock import Flock
from main import run_episode,validate_report
from policy import Intent

class GameTests(unittest.TestCase):
    def test_three_rounds_real_tags_and_role_swaps(self):
        r=run_episode(0,3);validate_report(r)
        self.assertEqual(r['result'],'complete')
        self.assertEqual(len(r['rounds']),3)
        for before,after in zip(r['rounds'],r['rounds'][1:]):
            self.assertNotEqual(before['seat'],after['seat'])
            if before['result']=='escaped':self.assertEqual(after['picker'],before['goose'])
        self.assertEqual(len([e for e in r['events'] if e['event']=='physical_beak_tap']),3)
        self.assertGreater(min(r['minimum_upright_cosine'].values()),.9)

    def test_neutral_runner_gets_physical_beak_tag(self):
        r=run_episode(0,1,neutral=True);validate_report(r)
        self.assertEqual(r['result'],'complete')
        self.assertEqual(r['rounds'][0]['result'],'caught')
        self.assertTrue(any(e['event']=='physical_beak_tag_back' for e in r['events']))

    def test_disabling_reach_prevents_opening_tap(self):
        r=run_episode(0,1,disabled_tags=True)
        self.assertEqual(r['result'],'opening_tag_disabled')
        self.assertFalse(any(e['event']=='physical_beak_tap' for e in r['events']))

    def test_caught_goose_returns_and_next_round_starts(self):
        r=run_episode(0,2,neutral=True)
        self.assertEqual(r['result'],'complete')
        self.assertEqual([x['result'] for x in r['rounds']],['caught','caught'])
        self.assertEqual(r['rounds'][0]['picker'],r['rounds'][1]['picker'])
        self.assertEqual(sum(r['scores'].values()),2)
        self.assertTrue(any(e['event']=='caught_clear' for e in r['events']))

    def test_watchers_remain_seated_and_turn_real_joints(self):
        w=Flock();w.start();minimum=1.;angles={r:[] for r in w.roles[1:]}
        for i in range(1500):
            target=[.78*math.cos(i*.007),.78*math.sin(i*.007),.2]
            w.step({r:Intent() if r=='duck0' else w.watch(r,target,w.data.time) for r in w.roles})
            if i>100:
                for role in w.roles[1:]:
                    o=w.observe(role);minimum=min(minimum,-float(o.gravity[2]))
                    angles[role].append(float(o.joint_positions[7]))
                    self.assertLess(o.position[2],.078)
        self.assertGreater(minimum,.9)
        for values in angles.values():self.assertGreater(max(values)-min(values),1.5)
        self.assertEqual(w.model.neq,0)
        self.assertEqual(np.count_nonzero(w.model.jnt_type==mujoco.mjtJoint.mjJNT_FREE),6)
        self.assertEqual(w.model.nu,84)
        np.testing.assert_array_equal(w.data.xfrc_applied,0)
        np.testing.assert_array_equal(w.data.qfrc_applied,0)
        for role in w.roles:
            joint=w.model.joint(role+'/propeller_hinge')
            self.assertGreater(abs(w.data.qpos[int(joint.qposadr[0])]),1.)

    def test_seeded_selection_is_reproducible_and_varied(self):
        def choices(seed):
            g=FullGame(seed=seed)
            result=[]
            for _ in range(8):g.choose();result.append(g.selected_seat)
            return result
        a=choices(3)
        self.assertEqual(a,choices(3))
        self.assertNotEqual(a,choices(4))
        self.assertGreater(len(set(a)),2)
        self.assertTrue(all(x!=y for x,y in zip(a,a[1:])))

if __name__=='__main__':unittest.main()
