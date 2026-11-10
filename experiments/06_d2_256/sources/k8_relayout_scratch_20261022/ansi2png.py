import re,sys,unicodedata
from PIL import Image,ImageDraw,ImageFont
txt=sys.stdin.read().replace('\r','')
F=ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumGothicCodingBold.ttf',20)
SYM=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',18)
CW,CH=11,22
base={30:(0,0,0),31:(205,49,49),32:(13,188,121),33:(229,229,16),34:(36,114,200),37:(229,229,229),90:(102,102,102),97:(255,255,255),
      41:(205,49,49),42:(13,188,121),43:(229,229,16),44:(36,114,200),47:(229,229,229),100:(102,102,102),101:(241,76,76),107:(255,255,255)}
def c256(n):
    if n<16: return [(0,0,0),(205,49,49),(13,188,121),(229,229,16),(36,114,200),(188,63,188),(17,168,205),(229,229,229)][n%8]
    if n<232: n-=16; v=[0,95,135,175,215,255]; return (v[n//36],v[(n//6)%6],v[n%6])
    g=8+10*(n-232); return (g,g,g)
lines=txt.split('\n'); cols=100
img=Image.new('RGB',(cols*CW+20,len(lines)*CH+20),(30,30,30)); d=ImageDraw.Draw(img)
DEFBG,DEFFG=(30,30,30),(220,220,220)
for li,l in enumerate(lines):
    x=0; bg,fg=DEFBG,DEFFG
    for tok in re.split(r'(\x1b\[[0-9;]*m)',l):
        m=re.fullmatch(r'\x1b\[([0-9;]*)m',tok)
        if m:
            p=[int(v) for v in m.group(1).split(';') if v!='']or[0]; i=0
            while i<len(p):
                v=p[i]
                if v==0: bg,fg=DEFBG,DEFFG
                elif v==48 and p[i+1]==5: bg=c256(p[i+2]); i+=2
                elif v==38 and p[i+1]==5: fg=c256(p[i+2]); i+=2
                elif 40<=v<=47 or 100<=v<=107: bg=base.get(v,bg)
                elif 30<=v<=37 or 90<=v<=97: fg=base.get(v,fg)
                i+=1
            continue
        for ch in tok:
            w=2 if unicodedata.east_asian_width(ch) in 'WF' else 1
            X,Y=10+x*CW,10+li*CH
            if ch=='▄':
                d.rectangle([X,Y,X+CW-1,Y+CH//2-1],fill=bg); d.rectangle([X,Y+CH//2,X+CW-1,Y+CH-1],fill=fg); x+=1; continue
            if ch=='▀':
                d.rectangle([X,Y,X+CW-1,Y+CH//2-1],fill=fg); d.rectangle([X,Y+CH//2,X+CW-1,Y+CH-1],fill=bg); x+=1; continue
            d.rectangle([X,Y,X+w*CW,Y+CH],fill=bg)
            if 0x2800<=ord(ch)<=0x28FF:
                b=ord(ch)-0x2800
                for bit,(dx,dy) in enumerate([(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(0,3),(1,3)]):
                    if b>>bit&1:
                        ox,oy=X+2+dx*5,Y+2+dy*6; d.ellipse([ox,oy,ox+3,oy+3],fill=fg)
                x+=1; continue
            font=F if (w==2 or ch.isascii()) else SYM
            d.text((X,Y+3),ch,font=font,fill=fg)
            x+=w
img.save(sys.argv[1])
