"""v0.3.0: pre-specified 30-seed paired SA-IACO audit, figure-derived maps."""
from __future__ import annotations
import argparse,csv,hashlib,json,random
from dataclasses import asdict
from math import comb
from pathlib import Path
from statistics import mean,stdev
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from saiaco_ugv import Grid,AntColony,Config,evaluate,valid_path
from saiaco_ugv.cli import MAPS
from saiaco_ugv.oracles import shortest_grid_path

CONDITIONS=("full","no_sa","no_direction","no_smoothing","elite_sa","elite_no_sa")
MAPS_MAIN=("paper20","paper30")
ELITE_WEIGHT=3.0  # Explicit NON-PAPER extension; value frozen before study.

def cfg_for(base,condition,seed):
    kw=asdict(base);kw["seed"]=seed
    if condition in ("no_sa","elite_no_sa"):kw["sa_enabled"]=False
    if condition=="no_direction":kw["direction_u"]=0.0
    if condition=="no_smoothing":kw["smoothing_enabled"]=False
    if condition.startswith("elite_"):kw["elite_deposit_weight"]=ELITE_WEIGHT
    return Config(**kw)

def measure(grid,name,seed,condition,base,optimal):
    config=cfg_for(base,condition,seed)
    result=AntColony(grid,config,"hybrid").run()
    assert result.path and result.raw_path and result.seed_path,(name,seed,condition)
    assert valid_path(grid,result.raw_path)
    assert valid_path(grid,result.path,allow_shortcuts=config.smoothing_enabled)
    final=evaluate(result.path);raw=evaluate(result.raw_path)
    a_star=evaluate(result.seed_path)
    return dict(map=name,seed=seed,condition=condition,length=round(final.length,6),
        turns=final.turns,smoothness=round(final.smoothness,6),
        raw_length=round(raw.length,6),astar_length=round(a_star.length,6),
        raw_search_gain=round(a_star.length-raw.length,6),
        smoothing_gain=round(raw.length-final.length,6),
        grid_optimum=round(optimal,6),raw_to_discrete_optimum=round(raw.length/optimal,6),
        accepted_best_iteration=result.first_best_iteration,success_walks=result.successes,
        success_rate=round(result.successes/(config.ants*config.iterations),6))

def bootstrap(xs,rng,nboot):
    if len(xs)==1:return xs[0],xs[0]
    n=len(xs)
    estimates=sorted(mean(xs[rng.randrange(n)] for k in range(n)) for j in range(nboot))
    return estimates[int(.025*nboot)],estimates[min(nboot-1,int(.975*nboot))]

def sign_p(diffs):
    pos=sum(d>1e-8 for d in diffs);neg=sum(d< -1e-8 for d in diffs)
    n=pos+neg
    return min(1.0,2*sum(comb(n,k) for k in range(min(pos,neg)+1))/2**n) if n else 1.0

def write_csv(dest,rows):
    with dest.open("w",newline="",encoding="utf-8") as fp:
        out=csv.DictWriter(fp,list(rows[0]))
        out.writeheader();out.writerows(rows)

def analyze(rows,nboot):
    rng=random.Random(314159)
    summary=[];comparisons=[]
    for name in MAPS_MAIN:
        groups={c:sorted((r for r in rows if r["map"]==name and r["condition"]==c),
                         key=lambda r:r["seed"]) for c in CONDITIONS}
        assert len({tuple(r["seed"] for r in v) for v in groups.values()})==1
        for c,v in groups.items():
            lengths=[float(r["length"]) for r in v]
            gains=[float(r["raw_search_gain"]) for r in v]
            lo,hi=bootstrap(lengths,rng,nboot)
            summary.append(dict(map=name,condition=c,n=len(v),
                mean_length=round(mean(lengths),4),sd_length=round(stdev(lengths),4),
                ci95_low=round(lo,4),ci95_high=round(hi,4),
                mean_raw_gain=round(mean(gains),4),
                raw_improvement_rate=round(sum(x>1e-8 for x in gains)/len(gains),4),
                mean_smoothing_gain=round(mean(float(r["smoothing_gain"]) for r in v),4),
                mean_turns=round(mean(r["turns"] for r in v),3),
                mean_success_rate=round(mean(r["success_rate"] for r in v),4)))
        for a,b in (("full","no_sa"),("full","no_direction"),("full","no_smoothing"),
                    ("elite_sa","elite_no_sa"),("elite_sa","full")):
            differences=[float(rb["length"])-float(ra["length"]) for ra,rb in zip(groups[a],groups[b])]
            lo,hi=bootstrap(differences,rng,nboot)
            comparisons.append(dict(map=name,candidate=a,reference=b,n=len(differences),
                mean_gain=round(mean(differences),4),ci95_low=round(lo,4),ci95_high=round(hi,4),
                wins=sum(d>1e-8 for d in differences),losses=sum(d< -1e-8 for d in differences),
                ties=sum(abs(d)<=1e-8 for d in differences),sign_test_p=round(sign_p(differences),7)))
    return summary,comparisons

def charts(summary,comparisons,dest):
    fig,axs=plt.subplots(1,2,figsize=(14,5.5),layout="constrained")
    for ax,name in zip(axs,MAPS_MAIN):
        s=[v for v in summary if v["map"]==name]
        ax.bar(range(len(s)),[v["mean_length"] for v in s],
            yerr=[[v["mean_length"]-v["ci95_low"] for v in s],
                  [v["ci95_high"]-v["mean_length"] for v in s]],capsize=3)
        ax.set_xticks(range(len(s)),[v["condition"] for v in s],rotation=45,ha="right")
        ax.set_title(name+" — 30 paired seeds");ax.set_ylabel("Final path length")
        ax.grid(axis="y",alpha=.25)
    fig.savefig(dest/"mean_length_ci.png",dpi=165);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(13,5.5),layout="constrained")
    for ax,name in zip(axs,MAPS_MAIN):
        cc=[v for v in comparisons if v["map"]==name]
        ax.errorbar([v["mean_gain"] for v in cc],range(len(cc)),xerr=[
            [v["mean_gain"]-v["ci95_low"] for v in cc],
            [v["ci95_high"]-v["mean_gain"] for v in cc]],fmt="o",capsize=4)
        ax.axvline(0,linestyle="--")
        ax.set_yticks(range(len(cc)),[v["candidate"]+" vs "+v["reference"] for v in cc])
        ax.set_xlabel("Mean paired reduction (positive favors candidate)")
        ax.set_title(name);ax.grid(axis="x",alpha=.25)
    fig.savefig(dest/"paired_effects.png",dpi=165);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,4.7),layout="constrained")
    for ax,name in zip(axs,MAPS_MAIN):
        s=next(v for v in summary if v["map"]==name and v["condition"]=="full")
        ax.bar(["Raw search gain","Smoothing gain"],[s["mean_raw_gain"],s["mean_smoothing_gain"]])
        ax.axhline(0,color="black",linewidth=.8);ax.set_title(name)
        ax.set_ylabel("Mean path length reduction")
    fig.savefig(dest/"gain_decomposition.png",dpi=165);plt.close(fig)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seeds",type=int,default=30)
    p.add_argument("--seed-start",type=int,default=1000)
    p.add_argument("--ants",type=int,default=10)
    p.add_argument("--iterations",type=int,default=15)
    p.add_argument("--bootstrap",type=int,default=4000)
    p.add_argument("--out",type=Path,default=Path("outputs/study_v03"))
    args=p.parse_args()
    if min(args.seeds,args.ants,args.iterations,args.bootstrap)<1:p.error("Positive counts required")
    args.out.mkdir(parents=True,exist_ok=True)
    base=Config(ants=args.ants,iterations=args.iterations)
    rows=[];references={}
    for name in MAPS_MAIN:
        path=MAPS/(name+".txt")
        grid=Grid.from_text(path.read_text(encoding="utf-8"))
        shortest=shortest_grid_path(grid)
        assert shortest is not None
        optimal=evaluate(shortest).length
        references[name]=dict(grid_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            discrete_8_neighbor_optimum=round(optimal,6),
            grid_obstacles=sum(s.count("#") for s in grid.cells),
            start=grid.start,goal=grid.goal,
            note="Digitized approximation, not an original author map")
        for seed in range(args.seed_start,args.seed_start+args.seeds):
            for condition in CONDITIONS:
                rows.append(measure(grid,name,seed,condition,base,optimal))
            if (seed-args.seed_start+1)%5==0:
                print(name,"seeds",seed-args.seed_start+1,"/",args.seeds,flush=True)
    summary,pairs=analyze(rows,args.bootstrap)
    write_csv(args.out/"runs.csv",rows)
    write_csv(args.out/"summary.csv",summary)
    write_csv(args.out/"paired_comparisons.csv",pairs)
    manifest=dict(study="v0.3.0 paired RNG audit",seed_start=args.seed_start,seeds=args.seeds,
        conditions=CONDITIONS,ants=args.ants,iterations=args.iterations,
        bootstrap=args.bootstrap,elite_weight=ELITE_WEIGHT,references=references,
        note="Exploratory. Non-paper elite variant. Original paper maps and parameters unknown.")
    (args.out/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    charts(summary,pairs,args.out)
    print(json.dumps(dict(summary=summary,comparisons=pairs),indent=2))

if __name__=="__main__":main()
