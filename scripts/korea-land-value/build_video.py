# -*- coding: utf-8 -*-
"""
스토리보드(build_storyboard.py)에서 컷 데이터를 읽어 영상을 조립한다.

  python3 build_video.py                # 720p 프리뷰, 임시 음성(espeak), 컷 1~끝
  python3 build_video.py --res 1080     # 1080p
  python3 build_video.py --cuts 1-10    # 일부 컷만
  python3 build_video.py --voice none   # 무음(자막만)
  python3 build_video.py --voice audio/ # audio/001.wav ... 실제 나레이션 파일이 있으면 사용
  python3 build_video.py --images images/   # images/001.png ... 실제 이미지가 있으면 배경으로 사용

이미지가 없는 컷은 자막과 화면 설명을 얹은 타이포 프레임으로 렌더링한다.
출력: out/<res>/final.mp4, out/자막.srt, out/컷리스트.csv
"""
import os, sys, io, csv, math, wave, ctypes, argparse, subprocess, shutil, html, glob
HERE=os.path.dirname(os.path.abspath(__file__))
ap=argparse.ArgumentParser()
ap.add_argument('--res',type=int,default=720); ap.add_argument('--cuts',default='all')
ap.add_argument('--voice',default='espeak'); ap.add_argument('--images',default=os.path.join(HERE,'images'))
ap.add_argument('--out',default=os.path.join(HERE,'out')); ap.add_argument('--zoom',type=int,default=1)
A=ap.parse_args()
W,H=(1920,1080) if A.res==1080 else (1280,720)
FPS=30

# --- 컷 데이터 로드 ---
ns={'__file__':os.path.join(HERE,'build_storyboard.py'),'__name__':'lib'}
_o=sys.stdout; sys.stdout=io.StringIO(); exec(open(ns['__file__'],encoding='utf-8').read(),ns); sys.stdout=_o
CUTS=ns['cuts']; SCENES=ns['scene_ranges']
if A.cuts!='all':
    a,b=A.cuts.split('-'); sel=range(int(a),int(b)+1)
else: sel=range(1,len(CUTS)+1)

try:
    import imageio_ffmpeg; FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG=shutil.which('ffmpeg')
OUT=os.path.join(A.out,str(A.res)); os.makedirs(OUT,exist_ok=True)
for d in ('frames','audio','clips'): os.makedirs(os.path.join(OUT,d),exist_ok=True)

# --- 음성 ---
def espeak_init():
    import espeakng_loader
    lib=ctypes.CDLL(espeakng_loader.get_library_path())
    rate=lib.espeak_Initialize(2,0,espeakng_loader.get_data_path().encode(),0)
    buf=bytearray()
    CB=ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)
    def cb(wav,n,ev):
        if n>0: buf.extend(ctypes.string_at(wav,n*2))
        return 0
    cbf=CB(cb); lib.espeak_SetSynthCallback(cbf); lib.espeak_SetVoiceByName(b'ko'); lib.espeak_SetParameter(1,170,0)
    def synth(text,path):
        buf.clear(); t=text.encode('utf-8'); lib.espeak_Synth(t,len(t)+1,0,0,0,1,None,None)
        w=wave.open(path,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(bytes(buf)); w.close()
        return len(buf)/2/rate
    return synth,cbf
def wav_dur(p):
    w=wave.open(p,'rb'); d=w.getnframes()/w.getframerate(); w.close(); return d
def probe_dur(p):
    r=subprocess.run([FFMPEG,'-i',p],capture_output=True,text=True).stderr
    import re; m=re.search(r'Duration: (\d+):(\d+):([\d.]+)',r); return int(m[1])*3600+int(m[2])*60+float(m[3])

synth=None
if A.voice=='espeak': synth,_keep=espeak_init()

# --- 프레임 렌더 (HTML -> PNG) ---
FONT_R=os.path.join(HERE,'fonts','NotoSansKR-Regular.ttf'); FONT_B=os.path.join(HERE,'fonts','NotoSansKR-Bold.ttf')
CSS=f"""
@font-face{{font-family:NK;src:url(file://{FONT_R});font-weight:400}}
@font-face{{font-family:NK;src:url(file://{FONT_B});font-weight:700}}
*{{box-sizing:border-box}} body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;font-family:NK,sans-serif;color:#fff;position:relative;background:#0b1a33}}
.bg{{position:absolute;inset:0;background-size:cover;background-position:center}}
.bgP{{background:radial-gradient(ellipse at 30% 20%,#1d3557 0%,#0b1a33 60%,#050b17 100%)}}
.bgI{{background:radial-gradient(ellipse at 70% 80%,#14213d 0%,#0b1a33 60%,#050b17 100%)}}
.bgL{{background:radial-gradient(ellipse at 50% 50%,#3d2b1f 0%,#1a1208 70%)}}
.grain{{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.015) 0 2px,transparent 2px 4px)}}
.top{{position:absolute;top:{int(H*.045)}px;left:{int(W*.05)}px;right:{int(W*.05)}px;display:flex;justify-content:space-between;font-size:{int(H*.026)}px;letter-spacing:.08em;color:rgba(255,255,255,.55)}}
.head{{position:absolute;left:{int(W*.08)}px;right:{int(W*.08)}px;top:{int(H*.30)}px;font-weight:700;font-size:{int(H*.085)}px;line-height:1.25;text-shadow:0 4px 30px rgba(0,0,0,.6);word-break:keep-all}}
.desc{{position:absolute;left:{int(W*.08)}px;right:{int(W*.08)}px;top:{int(H*.62)}px;font-size:{int(H*.03)}px;color:rgba(255,255,255,.5);word-break:keep-all}}
.sub{{position:absolute;left:{int(W*.06)}px;right:{int(W*.06)}px;bottom:{int(H*.07)}px;text-align:center;font-size:{int(H*.042)}px;line-height:1.4;word-break:keep-all}}
.sub span{{background:rgba(0,0,0,.62);padding:{int(H*.008)}px {int(H*.018)}px;border-radius:6px;box-decoration-break:clone;-webkit-box-decoration-break:clone}}
.bar{{position:absolute;left:0;bottom:0;height:{max(4,int(H*.006))}px;background:#f2c14e}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.25) 0%,rgba(0,0,0,0) 35%,rgba(0,0,0,.55) 100%)}}
"""
def frame_html(n,scene_title,line,vis,sub,st,img,progress):
    bg=f'<div class="bg" style="background-image:url(file://{img})"></div><div class="shade"></div>' if img else f'<div class="bg bg{st}"></div><div class="grain"></div>'
    head='' if img or sub=='자막 없음' else f'<div class="head">{html.escape(sub)}</div>'
    desc='' if img else f'<div class="desc">{html.escape(vis)}</div>'
    subt=f'<div class="sub"><span>{html.escape(line)}</span></div>'
    return f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{bg}<div class="top"><div>{html.escape(scene_title)}</div><div>{n:03d}</div></div>{head}{desc}{subt}<div class="bar" style="width:{progress*100:.2f}%"></div></body></html>'

from playwright.sync_api import sync_playwright
rows=[]; srt=[]; concat=[]; t=0.0
with sync_playwright() as p:
    br=p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg=br.new_page(viewport={'width':W,'height':H})
    total=len(CUTS)
    for n in sel:
        si,title,c,a,b=CUTS[n-1]; line,vis,sub,ip,st=c
        est=b-a
        # 음성
        wav=os.path.join(OUT,'audio',f'{n:03d}.wav'); adur=None
        if A.voice=='espeak':
            adur=synth(line,wav)
        elif A.voice!='none' and os.path.isdir(A.voice):
            cand=[f for f in glob.glob(os.path.join(A.voice,f'{n:03d}.*'))]
            if cand: wav=cand[0]; adur=probe_dur(wav)
        dur=(adur+0.6) if adur else est
        # 이미지
        img=None
        for ext in ('png','jpg','jpeg','webp'):
            cand=os.path.join(A.images,f'{n:03d}.{ext}')
            if os.path.exists(cand): img=cand; break
        png=os.path.join(OUT,'frames',f'{n:03d}.png')
        pg.set_content(frame_html(n,title,line,vis,sub,st,img,(n-1)/total)); pg.screenshot(path=png)
        # 클립
        clip=os.path.join(OUT,'clips',f'{n:03d}.mp4')
        vf=f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
        if A.zoom and img:
            frames=int(dur*FPS)
            vf+=f",zoompan=z='min(zoom+0.0006,1.08)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}"
        cmd=[FFMPEG,'-y','-loglevel','error','-loop','1','-framerate',str(FPS),'-i',png]
        if adur: cmd+=['-i',wav]
        else: cmd+=['-f','lavfi','-i','anullsrc=r=22050:cl=mono']
        cmd+=['-t',f'{dur:.3f}','-vf',vf,'-r',str(FPS),'-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-ar','44100','-ac','1','-af','apad',clip]
        subprocess.run(cmd,check=True)
        rows.append([n,si,title,f'{t:.2f}',f'{t+dur:.2f}',f'{dur:.2f}',st,line,sub,vis,ip,os.path.basename(img) if img else ''])
        def ts(x): return f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(round((x%1)*1000)):03d}"
        srt.append(f"{len(srt)+1}\n{ts(t)} --> {ts(t+dur-0.05)}\n{line}\n")
        concat.append(f"file '{clip}'"); t+=dur
        print(f"컷 {n:03d} {dur:5.1f}s  누적 {int(t//60)}:{int(t%60):02d}",flush=True)
    br.close()

lst=os.path.join(OUT,'concat.txt'); open(lst,'w').write("\n".join(concat))
final=os.path.join(OUT,'final.mp4')
subprocess.run([FFMPEG,'-y','-loglevel','error','-f','concat','-safe','0','-i',lst,'-c','copy','-movflags','+faststart',final],check=True)
open(os.path.join(A.out,'자막.srt'),'w',encoding='utf-8').write("\n".join(srt))
with open(os.path.join(A.out,'컷리스트.csv'),'w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f); w.writerow(['컷','장면','장면제목','시작(초)','끝(초)','길이(초)','스타일','대본','자막','화면구성','이미지프롬프트','사용이미지']); w.writerows(rows)
print(f"완료: {final}  총 {int(t//60)}:{int(t%60):02d}  크기 {os.path.getsize(final)/1e6:.1f}MB")
