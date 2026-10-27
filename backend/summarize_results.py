import json

with open("data-analysis/evaluation/ablation_results.json") as f:
    data = json.load(f)

for name in ["instantaneous_only", "window_only", "combined"]:
    print(f"\n=== Configuration: {name} ===")
    for item in data[name]:
        print(f"Detector: {item['detector']}")
        print(f"  Overall: F1={item['f1']:.3f}, Prec={item['precision']:.3f}, Rec={item['recall']:.3f}, FPR={item['fpr']:.3f}, Delay={item['delay']}")
        if "max-7.0" in item['detector'] or "mean-2.5" in item['detector']:
            print("  Breakdown by Fault:")
            for fault, stats in sorted(item['by_fault'].items()):
                d = f"{stats['mean_delay']:.1f}s" if stats['mean_delay'] is not None else "None"
                print(f"    {fault:<8} Count={stats['count']} F1={stats['mean_f1']:.3f} Prec={stats['mean_precision']:.3f} Rec={stats['mean_recall']:.3f} FPR={stats['mean_fpr']:.3f} Delay={d}")
