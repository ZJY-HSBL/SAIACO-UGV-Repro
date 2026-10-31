"""v0.4.0: pre-declared held-out confirmation, no new parameter search.

20 NEW seeds (2000..2019), 8 reconstructed maps, 3 conditions, 480 runs.
Statistical sampling unit is the seed (8-map mean), not each of 160
correlated map/seed observations. Elite reinforcement is NON-PAPER.
"""
from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
from statistics import mean, stdev
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from saiaco_ugv import Grid, AntColony, Config, evaluate, valid_path
from saiaco_ugv.cli import MAPS
from saiaco_ugv.oracles import shortest_grid_path
from study_v03 import bootstrap, sign_p, write_csv

MAIN=("paper20","paper30")
SPECIAL=("u_maze","double_hook_maze","loop_maze","traditional_maze","staircase_maze","x_maze")
MAP_NAMES=MAIN+SPECIAL
CONDITIONS=("paper_inspired","elite_greedy","elite_sa")
PAIRS=(("elite_sa","elite_greedy"),("elite_sa","paper_inspired"))
ELITE_WEIGHT=3.0

def config_for(condition,seed,ants,iterations):
    if condition not in CONDITIONS: raise ValueError(condition)
    return Config(seed=seed,ants=ants,iterations=iterations,
        elite_deposit_weight=0.0 if condition=="paper_inspired" else ELITE_WEIGHT,
        sa_enabled=(condition!="elite_greedy"))

def run_one(grid,name,seed,condition,ants,iterations,opt):
    cfg=config_for(condition,seed,ants,iterations)
    result=AntColony(grid,cfg,"hybrid").run()
    assert result.path and result.raw_path and result.seed_path
    assert valid_path(grid,result.raw_path), (name,seed,condition,"raw")
    assert valid_path(grid,result.path,allow_shortcuts=True),(name,seed,condition,"smooth")
    final=evaluate(result.path)
    raw=evaluate(result.raw_path)
    init=evaluate(result.seed_path)
    assert raw.length+1e-9>=opt and final.length<=raw.length+1e-9
    return dict(map=name,group="main" if name in MAIN else "special",
        seed=seed,condition=condition,length=round(final.length,6),turns=final.turns,
        smoothness=round(final.smoothness,6),raw_length=round(raw.length,6),
        astar4_length=round(init.length,6),
        raw_search_gain=round(init.length-raw.length,6),
        smoothing_gain=round(raw.length-final.length,6),
        dijkstra8_length=round(opt,6),successful_ants=result.successes,
        success_rate=round(result.successes/(ants*iterations),6),
        sa_uphill_accepted=result.sa_uphill_accepted,
        sa_nonworse_accepted=result.sa_nonworse_accepted,
        elite_deposit_rounds=result.elite_deposit_rounds,
        best_iteration=result.first_best_iteration or "")

def analyze(rows,seed_start,n_seeds,boot):
    rng=random.Random(20261031)
    lookup={(r["map"],r["seed"],r["condition"]):r for r in rows}
    assert len(rows)==len(lookup)==len(MAP_NAMES)*len(CONDITIONS)*n_seeds
    seeds=range(seed_start,seed_start+n_seeds)
    summary=[];map_comparisons=[]
    for name in MAP_NAMES:
        for method in CONDITIONS:
            group=[lookup[name,s,method] for s in seeds]
            lengths=[t["length"] for t in group]
            low,high=bootstrap(lengths,rng,boot)
            summary.append(dict(map=name,group=group[0]["group"],condition=method,n=n_seeds,
                mean_length=round(mean(lengths),5),
                sd_length=round(stdev(lengths),5) if n_seeds>1 else 0,
                ci95_low=round(low,5),ci95_high=round(high,5),
                mean_turns=round(mean(t["turns"] for t in group),3),
                mean_raw_gain=round(mean(t["raw_search_gain"] for t in group),5),
                mean_smoothing_gain=round(mean(t["smoothing_gain"] for t in group),5),
                mean_success_rate=round(mean(t["success_rate"] for t in group),5),
                mean_uphill_accepts=round(mean(t["sa_uphill_accepted"] for t in group),3)))
    for name in MAP_NAMES:
        for candidate,reference in PAIRS:
            diffs=[lookup[name,s,reference]["length"]-lookup[name,s,candidate]["length"] for s in seeds]
            low,high=bootstrap(diffs,rng,boot)
            map_comparisons.append(dict(map=name,group="main" if name in MAIN else "special",
                candidate=candidate,reference=reference,n=n_seeds,
                mean_length_reduction=round(mean(diffs),5),
                ci95_low=round(low,5),ci95_high=round(high,5),
                wins=sum(x>1e-9 for x in diffs),losses=sum(x< -1e-9 for x in diffs),
                ties=sum(abs(x)<=1e-9 for x in diffs),
                unadjusted_sign_p=round(sign_p(diffs),8)))
    primary=[]
    for candidate,reference in PAIRS:
        per_seed=[]
        for seed in seeds:
            effects=[100*(lookup[name,seed,reference]["length"]-
                 lookup[name,seed,candidate]["length"])/lookup[name,seed,reference]["length"]
                 for name in MAP_NAMES]
            per_seed.append(mean(effects))
        low,high=bootstrap(per_seed,rng,boot)
        primary.append(dict(candidate=candidate,reference=reference,
            unit="paired seed (8-map mean)",n_seeds=n_seeds,
            mean_relative_gain_percent=round(mean(per_seed),5),
            ci95_low=round(low,5),ci95_high=round(high,5),
            wins=sum(x>1e-9 for x in per_seed),losses=sum(x< -1e-9 for x in per_seed),
            ties=sum(abs(x)<=1e-9 for x in per_seed),
            raw_sign_p=sign_p(per_seed)))
    # Holm family-wise correction for the two predeclared comparisons only.
    order=sorted(range(len(primary)),key=lambda i:primary[i]["raw_sign_p"])
    adjusted=[0.0]*len(primary);maximum=0.0
    for rank,index in enumerate(order):
        maximum=max(maximum,min(1.,(len(primary)-rank)*primary[index]["raw_sign_p"]))
        adjusted[index]=maximum
    for index,item in enumerate(primary):
        item["raw_sign_p"]=round(item["raw_sign_p"],8)
        item["holm_sign_p"]=round(adjusted[index],8)
        item["reject_0_05"]=adjusted[index]<0.05
    return summary,map_comparisons,primary

def figures(summary,comparisons,primary,out):
    fig,axs=plt.subplots(1,2,figsize=(14,7),layout="constrained")
    for ax,(candidate,reference) in zip(axs,PAIRS):
        rows=[r for r in comparisons if r["candidate"]==candidate and r["reference"]==reference]
        centers=[r["mean_length_reduction"] for r in rows]
        ax.errorbar(centers,range(len(rows)),xerr=[
            [r["mean_length_reduction"]-r["ci95_low"] for r in rows],
            [r["ci95_high"]-r["mean_length_reduction"] for r in rows]],fmt="o",capsize=3)
        ax.axvline(0,color="gray",linestyle="--")
        ax.set_yticks(range(len(rows)),[r["map"] for r in rows]);ax.invert_yaxis()
        ax.set_xlabel("Paired reduction in path length; positive favors candidate")
        ax.set_title(candidate+" vs "+reference+" (exploratory per-map)")
        ax.grid(axis="x",alpha=.2)
    fig.savefig(out/"heldout_map_effects.png",dpi=180);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(14,5.5),layout="constrained")
    for ax,column,title in zip(axs,("mean_raw_gain","mean_smoothing_gain"),
                               ("Raw search improvement vs A*","Postprocessing smoothing gain")):
        width=.25
        for offset,method in zip((-1,0,1),CONDITIONS):
            values=[next(r[column] for r in summary if r["map"]==name and
                         r["condition"]==method) for name in MAP_NAMES]
            ax.bar([i+width*offset for i in range(len(MAP_NAMES))],values,width,label=method)
        ax.set_xticks(range(len(MAP_NAMES)),MAP_NAMES,rotation=45,ha="right")
        ax.axhline(0,color="black",linewidth=.8)
        ax.set_ylabel("Mean length reduction");ax.set_title(title)
    axs[0].legend(fontsize=8)
    fig.savefig(out/"search_vs_smoothing.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4),layout="constrained")
    for i,row in enumerate(primary):
        x=row["mean_relative_gain_percent"]
        ax.errorbar(x,i,xerr=[[x-row["ci95_low"]],[row["ci95_high"]-x]],fmt="o",capsize=4)
    ax.axvline(0,color="gray",linestyle="--")
    ax.set_yticks(range(len(primary)),[r["candidate"]+" vs "+r["reference"] for r in primary])
    ax.set_xlabel("Mean 8-map relative gain (%); clustered by seed")
    ax.set_title("Held-out primary comparisons, paired bootstrap 95% intervals")
    fig.savefig(out/"heldout_primary.png",dpi=180);plt.close(fig)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed-start",type=int,default=2000)
    p.add_argument("--seeds",type=int,default=20)
    p.add_argument("--ants",type=int,default=10)
    p.add_argument("--iterations",type=int,default=15)
    p.add_argument("--bootstrap",type=int,default=4000)
    p.add_argument("--out",type=Path,default=Path("outputs/study_v04"))
    args=p.parse_args()
    if min(args.seed_start,args.seeds,args.ants,args.iterations,args.bootstrap)<1:
        p.error("All counts must be positive")
    args.out.mkdir(parents=True,exist_ok=True)
    data=[];provenance={}
    for name in MAP_NAMES:
        file=MAPS/(name+".txt")
        grid=Grid.from_text(file.read_text(encoding="utf-8"))
        optimum=shortest_grid_path(grid)
        assert optimum is not None
        length=evaluate(optimum).length
        provenance[name]=dict(sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
            shape=grid.shape,obstacles=sum(row.count("#") for row in grid.cells),
            start=grid.start,goal=grid.goal,discrete_shortest=round(length,6),
            endpoint_provenance="reconstructed; special map endpoints are assumed")
        for seed in range(args.seed_start,args.seed_start+args.seeds):
            for condition in CONDITIONS:
                data.append(run_one(grid,name,seed,condition,args.ants,args.iterations,length))
        print(name,args.seeds,"paired seeds completed",flush=True)
    summary,permap,primary=analyze(data,args.seed_start,args.seeds,args.bootstrap)
    write_csv(args.out/"runs.csv",data)
    write_csv(args.out/"summary.csv",summary)
    write_csv(args.out/"exploratory_map_comparisons.csv",permap)
    write_csv(args.out/"primary_comparisons.csv",primary)
    manifest=dict(version="v0.4.0",study="held-out 8-map SA feedback validation",
        config={key:(str(val) if isinstance(val,Path) else val) for key,val in vars(args).items()},
        conditions=CONDITIONS,primary_hypotheses=PAIRS,elite_weight=ELITE_WEIGHT,
        map_source="approximate figure digitization; original grids not available",
        analysis_unit="seed (8-map relative percentage gain average), n=20",
        map_provenance=provenance)
    (args.out/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    figures(summary,permap,primary,args.out)
    print(json.dumps(dict(primary=primary,map_comparisons=permap),indent=2))

if __name__=="__main__": main()
