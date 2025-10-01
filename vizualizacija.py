#!/usr/bin/env python3
# geodesic_viewer.py
# Render interactive 3D geodesic viewer (outside notebooks) as a standalone HTML.

import argparse
import json
import sys
import webbrowser
from pathlib import Path

import numpy as np


HTML_TEMPLATE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Geodesic Viewer</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{ color-scheme: dark; }}
    body {{ margin:0; font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:#0b0b0c; color:#eee; }}
    #wrap {{ padding:12px; }}
    #controls {{ display:flex; gap:12px; align-items:center; margin-bottom:8px; flex-wrap:wrap; }}
    input[type=range] {{ width:420px; }}
    #plot {{ width:100%; height:80vh; }}
    .badge {{ background:#1a1a1b; padding:4px 8px; border-radius:12px; font-size:12px; }}
    label {{ display:flex; gap:6px; align-items:center; }}
    button {{ padding:6px 10px; border-radius:8px; background:#222; color:#eee; border:1px solid #333; cursor:pointer; }}
    button:active {{ transform: translateY(1px); }}
  </style>
</head>
<body>
<div id="wrap">
  <div id="controls">
    <span class="badge">Step:</span>
    <input id="slider" type="range" min="0" max="{Nmax}" value="0" step="1"/>
    <button id="play">▶ Play</button>
    <span class="badge">Tail:</span>
    <input id="tail" type="range" min="0" max="{Nmax}" value="{tail}" step="1"/>
    <label><input id="horizon" type="checkbox" {horizon_checked}/> Show horizon</label>
    <span class="badge" id="rs">r_s = {rs_text}</span>
  </div>
  <div id="plot"></div>
</div>

<script>
const D = {data_json};

function horizonMesh(rs, nT=28, nP=56) {{
  const th = Array.from({{length:nT}}, (_,i)=> i*(Math.PI/(nT-1)));
  const ph = Array.from({{length:nP}}, (_,j)=> j*(2*Math.PI/(nP-1)));
  const x=[], y=[], z=[];
  for (let i=0;i<nT;i++) {{
    const si = Math.sin(th[i]), ci = Math.cos(th[i]);
    const rowx=[], rowy=[], rowz=[];
    for (let j=0;j<nP;j++) {{
      rowx.push(D.rs*si*Math.cos(ph[j]));
      rowy.push(D.rs*si*Math.sin(ph[j]));
      rowz.push(D.rs*ci);
    }}
    x.push(rowx); y.push(rowy); z.push(rowz);
  }}
  return {{x, y, z}};
}}

const plt = document.getElementById('plot');
const slider = document.getElementById('slider');
const playBtn = document.getElementById('play');
const tailInput = document.getElementById('tail');
const horizonToggle = document.getElementById('horizon');

const traces = [];
traces.push({{
  type: 'scatter3d',
  mode: 'lines',
  x: D.x, y: D.y, z: D.z,
  opacity: 0.35,
  line: {{width: 2}},
  name: 'Path'
}});

let horizonIndex = null;
if (D.show_horizon) {{
  const H = horizonMesh(D.rs);
  traces.push({{
    type: 'surface',
    x: H.x, y: H.y, z: H.z,
    showscale: false,
    opacity: 0.25,
    name: 'Event horizon'
  }});
  horizonIndex = traces.length - 1;
}}

traces.push({{
  type: 'scatter3d',
  mode: 'lines',
  x: [D.x[0]], y: [D.y[0]], z: [D.z[0]],
  line: {{width: 6}},
  name: 'Recent segment'
}});
const tailIndex = traces.length - 1;

traces.push({{
  type: 'scatter3d',
  mode: 'markers',
  x: [D.x[0]], y: [D.y[0]], z: [D.z[0]],
  marker: {{size: 6}},
  name: 'Particle'
}});
const particleIndex = traces.length - 1;

Plotly.newPlot(plt, traces, {{
  title: 'Geodesic around Schwarzschild BH',
  scene: {{
    xaxis: {{title:'x', range:[-D.lim, D.lim], zeroline:false}},
    yaxis: {{title:'y', range:[-D.lim, D.lim], zeroline:false}},
    zaxis: {{title:'z', range:[-D.lim, D.lim], zeroline:false}},
    aspectmode: 'data',
    dragmode: 'orbit'
  }},
  showlegend: true,
  margin: {{l:0, r:0, t:50, b:0}},
}});

let timer = null;
function setIndex(i) {{
  i = Math.max(0, Math.min(D.N-1, i|0));
  const tailLen = parseInt(tailInput.value);
  const j0 = Math.max(0, i - tailLen);
  Plotly.restyle(plt, {{
    x: [D.x.slice(j0, i+1)], y: [D.y.slice(j0, i+1)], z: [D.z.slice(j0, i+1)]
  }}, [tailIndex]);
  Plotly.restyle(plt, {{
    x: [[D.x[i]]], y: [[D.y[i]]], z: [[D.z[i]]]
  }}, [particleIndex]);
}}

slider.addEventListener('input', e => setIndex(e.target.value));
tailInput.addEventListener('input', e => setIndex(slider.value));
horizonToggle.addEventListener('change', e => {{
  if (horizonIndex !== null) {{
    Plotly.restyle(plt, {{ visible: e.target.checked ? true : 'legendonly' }}, [horizonIndex]);
  }}
}});

playBtn.addEventListener('click', () => {{
  if (timer) {{
    clearInterval(timer);
    timer = null;
    playBtn.textContent = '▶ Play';
    return;
  }}
  playBtn.textContent = '⏸ Pause';
  timer = setInterval(() => {{
    let i = (1 + parseInt(slider.value)) % D.N;
    slider.value = i;
    setIndex(i);
  }}, 20);
}});

// Initialize view
setIndex(0);
</script>
</body>
</html>
"""


def spherical_to_cartesian(r: np.ndarray, th: np.ndarray, ph: np.ndarray):
    x = r * np.sin(th) * np.cos(ph)
    y = r * np.sin(th) * np.sin(ph)
    z = r * np.cos(th)
    return x, y, z


def load_trajectory(path: Path, file_format: str):
    if file_format == "npy":
        arr = np.load(path)
    elif file_format == "csv":
        arr = np.loadtxt(path, delimiter=",")
    else:
        raise ValueError("Unsupported format. Use 'npy' or 'csv'.")
    if arr.ndim != 2 or arr.shape[1] < 4:
        raise ValueError("Trajectory must be an array with columns [t, r, theta, phi].")
    return arr[:, :4]


def compute_rs(args):
    if args.rs is not None:
        return float(args.rs)
    if args.mass is not None and args.G is not None and args.c is not None:
        return 2.0 * args.G * args.mass / (args.c ** 2)
    return None  # horizon off by default if not provided


def main():
    p = argparse.ArgumentParser(description="Interactive geodesic viewer (HTML export).")
    p.add_argument("--input", required=True, help="Path to trajectory file (.npy or .csv with columns t,r,theta,phi)")
    p.add_argument("--format", choices=["npy", "csv"], default=None, help="Input format (auto by extension if omitted)")
    p.add_argument("--output", default="geodesic_viewer.html", help="Output HTML path")
    p.add_argument("--tail", type=int, default=800, help="Tail length (samples)")
    p.add_argument("--rs", type=float, default=None, help="Event horizon radius. If omitted, computed from --mass, --G, --c")
    p.add_argument("--mass", type=float, default=None, help="Mass parameter M (same units as your data)")
    p.add_argument("--G", type=float, default=None, help="Gravitational constant (default depends on your units)")
    p.add_argument("--c", type=float, default=None, help="Speed of light (default depends on your units)")
    p.add_argument("--open", action="store_true", help="Open HTML in the default browser")
    args = p.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ERROR: File not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    file_format = args.format
    if file_format is None:
        ext = in_path.suffix.lower()
        if ext == ".npy":
            file_format = "npy"
        elif ext == ".csv":
            file_format = "csv"
        else:
            print("ERROR: Could not infer format from extension. Use --format npy|csv", file=sys.stderr)
            sys.exit(1)

    traj = load_trajectory(in_path, file_format)
    t, r, th, ph = traj.T
    x, y, z = spherical_to_cartesian(r, th, ph)
    N = len(x)
    if N < 2:
        print("ERROR: Need at least 2 trajectory samples.", file=sys.stderr)
        sys.exit(1)

    rmax = float(np.max(np.abs([x, y, z])))
    lim = 1.05 * rmax if np.isfinite(rmax) and rmax > 0 else 1.0

    rs = compute_rs(args)
    show_horizon = rs is not None and np.isfinite(rs) and rs > 0

    data = {
        "x": x.tolist(),
        "y": y.tolist(),
        "z": z.tolist(),
        "N": int(N),
        "lim": float(lim),
        "rs": float(rs) if rs is not None else 0.0,
        "show_horizon": bool(show_horizon),
    }

    html = HTML_TEMPLATE.format(
        Nmax=N - 1,
        tail=min(max(0, args.tail), N - 1),
        rs_text=(f"{rs:.4g}" if rs is not None else "—"),
        horizon_checked=("checked" if show_horizon else ""),
        data_json=json.dumps(data),
    )

    out_path = Path(args.output)
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path.resolve()}")
    if args.open:
        webbrowser.open(out_path.resolve().as_uri())


if __name__ == "__main__":
    main()
