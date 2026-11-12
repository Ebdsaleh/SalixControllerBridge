#!/usr/bin/env python3
"""Render KiCad .kicad_sch files to SVG for headless visual review.

Not a KiCad replacement: this intentionally renders the subset used by the
SalixControllerBridge Rev-A schematics (symbols, pins, wires, labels, notes,
references/values) and emits a simple overlap report.
"""
from __future__ import annotations
import argparse, html, json, math, re
from pathlib import Path

PAPER={"A5":(210,148),"A4":(297,210),"A3":(420,297),"A2":(594,420)}

def toks(s):
    i=0
    while i<len(s):
        c=s[i]
        if c.isspace(): i+=1; continue
        if c in "()": yield c; i+=1; continue
        if c=='"':
            i+=1; q=[]
            while i<len(s):
                c=s[i]
                if c=="\\" and i+1<len(s): i+=1; q.append({"n":"\n","t":"\t","r":"\r"}.get(s[i],s[i])); i+=1
                elif c=='"': i+=1; break
                else: q.append(c); i+=1
            yield "".join(q); continue
        j=i
        while j<len(s) and not s[j].isspace() and s[j] not in "()": j+=1
        yield s[i:j]; i=j

def parse(s):
    st=[]; root=None
    for t in toks(s):
        if t=="(":
            n=[]
            if st: st[-1].append(n)
            st.append(n)
        elif t==")":
            n=st.pop()
            if not st: root=n
        else: st[-1].append(t)
    return root

def H(n): return n[0] if isinstance(n,list) and n and isinstance(n[0],str) else None
def C(n,k): return [x for x in n[1:] if isinstance(x,list) and H(x)==k] if isinstance(n,list) else []
def O(n,k): return C(n,k)[0] if C(n,k) else None
def A(n,i=1,d=None): return n[i] if isinstance(n,list) and len(n)>i and not isinstance(n[i],list) else d
def F(x,d=0):
    try:return float(x)
    except:return d
def AT(n):
    a=O(n,"at")
    return (F(A(a,1)),F(A(a,2)),F(A(a,3))) if a else (0,0,0)
def FX(n):
    e=O(n,"effects"); size=1.; bold=False; hide=False; just=set()
    if e:
        fo=O(e,"font")
        if fo:
            z=O(fo,"size")
            if z:size=max(F(A(z,1),1),F(A(z,2),1))
            bold=bool(O(fo,"bold"))
        hide=bool(O(e,"hide"))
        j=O(e,"justify")
        if j: just={x for x in j[1:] if isinstance(x,str)}
    return size,bold,hide,just

def rot(x,y,d):
    d=round(d)%360
    if d==90:return -y,x
    if d==180:return -x,-y
    if d==270:return y,-x
    if d==0:return x,y
    r=math.radians(d);return x*math.cos(r)-y*math.sin(r),x*math.sin(r)+y*math.cos(r)

def xf(x,y,sx,sy,r):
    # KiCad symbol-local coordinates use +Y upward while sheet coordinates
    # use +Y downward. Rotate in symbol space, then flip Y into sheet space.
    x,y=rot(x,y,r);return sx+x,sy-y

class SVG:
    def __init__(self,w,h):
        self.p=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}mm" height="{h}mm">',
                '<rect width="100%" height="100%" fill="#fbfaf4"/>',
                '<g font-family="DejaVu Sans Mono,monospace" stroke-linecap="round" stroke-linejoin="round">']
    def line(self,a,b,col="#15803d",wid=.22): self.p.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{col}" stroke-width="{wid}"/>')
    def poly(self,ps,col="#9b1c1c",fill="none",wid=.22):
        q=" ".join(f"{x},{y}" for x,y in ps);self.p.append(f'<polyline points="{q}" stroke="{col}" stroke-width="{wid}" fill="{fill}"/>')
    def rect(self,x1,y1,x2,y2,col="#9b1c1c",fill="#fff8bf",wid=.22,op=1):
        x,y=min(x1,x2),min(y1,y2);w,h=abs(x2-x1),abs(y2-y1)
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" stroke="{col}" stroke-width="{wid}" fill="{fill}" fill-opacity="{op}"/>')
    def text(self,s,x,y,z=1,r=0,b=False,j=set(),col="#103e8f"):
        anc="end" if "right" in j else ("middle" if "center" in j else "start")
        tr=f' transform="rotate({r} {x} {y})"' if r else ""
        self.p.append(f'<text x="{x}" y="{y}" font-size="{z}px" font-weight="{"700" if b else "400"}" text-anchor="{anc}" fill="{col}"{tr}>{html.escape(str(s))}</text>')
    def done(self): return "\n".join(self.p+["</g>","</svg>"])

def tbox(s,x,y,z,j):
    w=max(.7*z,len(s)*z*.58);h=z*1.25
    if "right" in j:x1,x2=x-w,x
    elif "center" in j:x1,x2=x-w/2,x+w/2
    else:x1,x2=x,x+w
    y1,y2=y-h,y+.25*h
    return [x1,y1,x2,y2]


def electrical_lint(root, libs):
    """Geometry-based electrical sanity checks.

    This is deliberately conservative. It catches labels floating in space and
    obvious role mismatches (for example a GND pin labelled 5V, D+ labelled DM,
    or SDA labelled SCL) without pretending to replace KiCad ERC.
    """
    pins=[]
    segs=[]
    labels=[]

    for n in root[1:]:
        if not isinstance(n,list):
            continue
        k=H(n)
        if k=="wire":
            ps=O(n,"pts")
            xy=[(F(A(x,1)),F(A(x,2))) for x in C(ps,"xy")] if ps else []
            for i in range(len(xy)-1):
                segs.append((xy[i],xy[i+1]))
        elif k in ("label","global_label","hierarchical_label"):
            x,y,_=AT(n)
            labels.append({"kind":k,"net":A(n,1,""),"point":(x,y)})
        elif k=="symbol":
            lib_id=A(O(n,"lib_id"),1)
            lib=libs.get(lib_id)
            if not lib:
                continue
            sx,sy,sr=AT(n)
            unit=int(F(A(O(n,"unit"),1),1))
            ref=""
            for pr in C(n,"property"):
                if A(pr,1)=="Reference":
                    ref=A(pr,2,"")
                    break
            for part in C(lib,"symbol"):
                nm=A(part,1,"")
                m=re.search(r"_(\d+)_(\d+)$",nm)
                if m and int(m.group(1)) not in (0,unit):
                    continue
                for pin in C(part,"pin"):
                    px,py,_=AT(pin)
                    x,y=xf(px,py,sx,sy,sr)
                    pins.append({
                        "ref":ref,
                        "lib":lib_id,
                        "number":A(O(pin,"number"),1,""),
                        "name":A(O(pin,"name"),1,""),
                        "point":(x,y),
                    })

    def eq(a,b,eps=1e-5):
        return abs(a[0]-b[0])<=eps and abs(a[1]-b[1])<=eps

    def on_seg(p,seg,eps=1e-5):
        x,y=p
        (x1,y1),(x2,y2)=seg
        cross=(x-x1)*(y2-y1)-(y-y1)*(x2-x1)
        if abs(cross)>eps:
            return False
        return (min(x1,x2)-eps<=x<=max(x1,x2)+eps and
                min(y1,y2)-eps<=y<=max(y1,y2)+eps)

    orphan=[]
    for lab in labels:
        p=lab["point"]
        if not any(eq(p,x["point"]) for x in pins) and not any(on_seg(p,seg) for seg in segs):
            orphan.append({
                "kind":lab["kind"],"net":lab["net"],
                "x":p[0],"y":p[1]
            })

    def connected_nets(point):
        reachable=[point]
        used=set()
        changed=True
        while changed:
            changed=False
            for i,seg in enumerate(segs):
                if i in used:
                    continue
                if any(on_seg(p,seg) for p in reachable):
                    used.add(i)
                    for q in seg:
                        if not any(eq(q,p) for p in reachable):
                            reachable.append(q)
                    changed=True

        nets=[]
        for lab in labels:
            p=lab["point"]
            if any(eq(p,q) for q in reachable):
                nets.append(lab["net"])
                continue
            for i in used:
                if on_seg(p,segs[i]):
                    nets.append(lab["net"])
                    break
        return sorted(set(nets))

    def role_ok(pin_name,net):
        p=pin_name.upper()
        n=net.upper()

        if p=="~" or not p:
            return True

        if p=="GND" or p.startswith("GND_"):
            return "GND" in n
        if p in ("VCC","VDD33","VDDA33","3V3","3V3_AUX"):
            return any(x in n for x in ("3V3","VCC","VDD"))
        if p.startswith("5V_"):
            return "5V" in n

        if "USBDM" in p or p.endswith("D-"):
            return "DM" in n or "D-" in n
        if "USBDP" in p or p.endswith("D+"):
            return "DP" in n or "D+" in n

        if p=="SDA" or p.startswith("SDA/"):
            return "SDA" in n
        if p=="SCL" or p.startswith("SCL/"):
            return "SCL" in n
        if p in ("CC1","CC2"):
            return p in n
        if p=="FAULT_N":
            return "FAULT" in n
        if p=="SINK_N":
            return "SINK" in n
        if p=="REF":
            return "REF" in n

        return True

    mismatches=[]
    pin_map=[]
    for pin in pins:
        nets=connected_nets(pin["point"])
        if nets:
            pin_map.append({
                "ref":pin["ref"],"pin":pin["number"],
                "pin_name":pin["name"],"nets":nets
            })
        for net in nets:
            if not role_ok(pin["name"],net):
                mismatches.append({
                    "ref":pin["ref"],"pin":pin["number"],
                    "pin_name":pin["name"],"net":net,
                    "x":pin["point"][0],"y":pin["point"][1],
                })

    return {
        "orphan_labels":orphan,
        "pin_net_mismatches":mismatches,
        "pin_map":pin_map,
    }


def render(path,out):
    root=parse(path.read_text(encoding="utf-8"))
    p=O(root,"paper"); pn=A(p,1,"A4") if p else "A4"; w,h=PAPER.get(pn,(297,210))
    svg=SVG(w,h);svg.rect(8,8,w-8,h-8,fill="none",wid=.18)
    # KiCad places the worksheet title block in the lower-right corner. Keep
    # review geometry out of that reserved area even when text/text lint is clean.
    title_keepout=[w-110,h-45,w-8,h-8]
    svg.rect(*title_keepout,col="#d97706",fill="#f59e0b",wid=.12,op=.06)
    lr=O(root,"lib_symbols");libs={A(x,1):x for x in C(lr,"symbol")} if lr else {}
    boxes=[]; texts=[]
    def addtxt(n,kind,col):
        s=A(n,1,"");x,y,r=AT(n);z,b,hi,j=FX(n)
        if hi:return
        svg.text(s,x,y,z,r,b,j,col);texts.append((kind,s,tbox(s,x,y,z,j)))
    for n in root[1:]:
        if not isinstance(n,list):continue
        k=H(n)
        if k=="wire":
            ps=O(n,"pts");q=[(F(A(x,1)),F(A(x,2))) for x in C(ps,"xy")] if ps else []
            if len(q)>1:svg.poly(q,col="#15803d")
        elif k in ("text","label","global_label","hierarchical_label"):
            addtxt(n,k,{"text":"#103e8f","label":"#111","global_label":"#7c1f7c","hierarchical_label":"#8a5500"}[k])
        elif k=="symbol":
            lib=libs.get(A(O(n,"lib_id"),1));sx,sy,sr=AT(n);unit=int(F(A(O(n,"unit"),1),1));ref=""
            for pr in C(n,"property"):
                if A(pr,1)=="Reference":ref=A(pr,2,"")
            pts=[]
            if lib:
                for part in C(lib,"symbol"):
                    nm=A(part,1,"");m=re.search(r"_(\d+)_(\d+)$",nm)
                    if m and int(m.group(1)) not in (0,unit):continue
                    for rr in C(part,"rectangle"):
                        st,en=O(rr,"start"),O(rr,"end")
                        if not st or not en:continue
                        x1,y1,x2,y2=F(A(st,1)),F(A(st,2)),F(A(en,1)),F(A(en,2))
                        q=[xf(x1,y1,sx,sy,sr),xf(x2,y1,sx,sy,sr),xf(x2,y2,sx,sy,sr),xf(x1,y2,sx,sy,sr)]
                        svg.poly(q+[q[0]],fill="#fff8bf");pts+=q
                    for pl in C(part,"polyline"):
                        pn2=O(pl,"pts");q=[xf(F(A(x,1)),F(A(x,2)),sx,sy,sr) for x in C(pn2,"xy")] if pn2 else []
                        if q:svg.poly(q);pts+=q
                    for pin in C(part,"pin"):
                        px,py,pr=AT(pin);ln=F(A(O(pin,"length"),1),2.54)
                        a=xf(px,py,sx,sy,sr);ex=px-ln*math.cos(math.radians(pr));ey=py+ln*math.sin(math.radians(pr));b=xf(ex,ey,sx,sy,sr)
                        svg.line(a,b,col="#9b1c1c")
                        no=A(O(pin,"number"),1,"");nm2=A(O(pin,"name"),1,"")
                        if no:svg.text(no,a[0],a[1]-.5,.58,col="#9b1c1c")
                        if nm2 and nm2!="~":svg.text(nm2,(a[0]+b[0])/2,(a[1]+b[1])/2-.45,.58,col="#267d6d")
            if pts:
                xs=[x for x,_ in pts];ys=[y for _,y in pts];boxes.append((ref,[min(xs),min(ys),max(xs),max(ys)]))
            for pr in C(n,"property"):
                if A(pr,1) in ("Reference","Value"):
                    s=A(pr,2,"");x,y,r=AT(pr);z,b,hi,j=FX(pr)
                    if not hi:svg.text(s,x,y,z,r,b,j,"#267d6d");texts.append((A(pr,1),s,tbox(s,x,y,z,j)))
    hits=[]
    for i,(ka,na,a) in enumerate(texts):
        for kb,nb,b in texts[i+1:]:
            if not (a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1]):
                if ka=="label" and kb=="label" and na==nb:continue
                hits.append({"type":"text-text","a":f"{ka}:{na}","b":f"{kb}:{nb}"})
    def intersects(a,b):
        return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])
    title_hits=[]
    for kind,name,box in texts:
        if intersects(box,title_keepout):
            title_hits.append({"type":"title-block-text","item":f"{kind}:{name}","box":box})
    for ref,box in boxes:
        if intersects(box,title_keepout):
            title_hits.append({"type":"title-block-symbol","item":ref or "<unnamed>","box":box})
    lint=electrical_lint(root,libs)
    report={
        "file":str(path),
        "likely_overlaps":hits,
        "title_block_intrusions":title_hits,
        "electrical_lint":lint,
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/(path.stem+".svg")).write_text(svg.done(),encoding="utf-8")
    (out/(path.stem+".overlaps.json")).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(
        f"{path.name}: {len(hits)} likely text overlap(s), "
        f"{len(title_hits)} title-block intrusion(s), "
        f"{len(lint['orphan_labels'])} orphan label(s), "
        f"{len(lint['pin_net_mismatches'])} obvious pin/net mismatch(es)"
    )
    return len(hits)+len(title_hits)+len(lint["orphan_labels"])+len(lint["pin_net_mismatches"])

def main():
    ap=argparse.ArgumentParser();ap.add_argument("input",type=Path);ap.add_argument("-o","--out",type=Path,default=Path("kicad_visuals"));ap.add_argument("--recursive",action="store_true")
    a=ap.parse_args()
    fs=sorted(a.input.glob("**/*.kicad_sch" if a.recursive else "*.kicad_sch")) if a.input.is_dir() else [a.input]
    total=sum(render(p,a.out) for p in fs);print("Total review findings:",total)
if __name__=="__main__":main()
