"""Run, evaluate, and record the continuous six-duck game."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import mujoco
import onnxruntime
from full_game import FullGame

ROOT=Path(__file__).parent

def run_episode(seed=0,rounds=3,neutral=False,disabled_tags=False,video=None):
    game=FullGame(seed=seed,rounds=rounds,neutral=neutral,disabled_tags=disabled_tags)
    recorder=None;frame=None
    if video:
        from full_render import FullRecorder
        recorder=FullRecorder(game,video);recorder.capture()
    try:
        while not game.result:
            game.step()
            if recorder and (game.steps%2==0 or game.result):frame=recorder.capture()
    finally:
        if recorder:recorder.close(frame if game.result else None)
    report=game.report()
    if recorder:report['video']={'file':Path(video).name,'fps':25,'frames':recorder.frames,'final_state_hold_s':2}
    return report

def validate_report(report):
    for role,calls in report['policy_calls'].items():
        assert calls==report['control_steps'],f'{role}: policy skipped a control step'
        lo,hi=report['joint_target_range_rad'][role]
        assert -10<=lo<=hi<=10
    for event in report['events']:
        if event['event'].startswith('physical_beak'):
            assert event['contact']['actor_mesh'] in ('jaw','bottom_head_shell')
            assert event['contact']['distance_from_beak_tip_m']<.045

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--no-video',action='store_true')
    p.add_argument('--output-dir',default='results')
    p.add_argument('--seed',type=int,default=0)
    p.add_argument('--rounds',type=int,default=3)
    p.add_argument('--benchmark',type=int,default=5,help='Number of other seeds, with two rounds each')
    p.add_argument('--skip-comparison-video',action='store_true')
    args=p.parse_args()
    if args.rounds<1 or args.benchmark<0:p.error('rounds must be positive; benchmark cannot be negative')
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    reference=run_episode(args.seed,args.rounds,video=None if args.no_video else out/'result.mp4')
    print(f"Reference: {reference['result']}, {len(reference['rounds'])} rounds, {reference['elapsed_s']} simulated seconds",flush=True)
    neutral=run_episode(args.seed,1,neutral=True,video=None if args.no_video or args.skip_comparison_video else out/'tag-back-comparison.mp4')
    disabled=run_episode(args.seed,1,disabled_tags=True)
    trials=[]
    for seed in range(args.seed+1,args.seed+args.benchmark+1):
        result=run_episode(seed,2);trials.append(result)
        print(f"Seed {seed}: {result['result']}, {len(result['rounds'])} rounds",flush=True)
    for report in [reference,neutral,disabled,*trials]:validate_report(report)
    evidence={
        'reference':reference,'neutral_navigation_comparison':neutral,'disabled_tag_comparison':disabled,
        'variation_trials':trials,
        'variation_summary':{'completed_runs':sum(r['result']=='complete' for r in trials),'runs':len(trials),
                             'completed_rounds':sum(len(r['rounds']) for r in trials)},
        'versions':{'python':platform.python_version(),'mujoco':mujoco.__version__,'onnxruntime':onnxruntime.__version__},
        'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(ROOT.glob('*.py'))},
        'checkpoint_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((ROOT/'assets/policies').glob('*.onnx'))},
    }
    (out/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    assert reference['result']=='complete' and len(reference['rounds'])==args.rounds,'Reference game incomplete; evidence saved'
    assert neutral['result']=='complete' and neutral['rounds'][0]['result']=='caught','Neutral navigation comparison failed'
    assert disabled['result']=='opening_tag_disabled','Disabled reaching gesture unexpectedly succeeded'
    assert not any(e['event']=='physical_beak_tap' for e in disabled['events'])
    print(json.dumps({'reference_rounds':reference['rounds'],'neutral_catch_s':neutral['rounds'][0]['finished_s'],
                      'disabled_tag_result':disabled['result'],'variation_summary':evidence['variation_summary'],
                      'evidence':str(out/'evidence.json'),'video':None if args.no_video else str(out/'result.mp4')},indent=2))

if __name__=='__main__':main()
