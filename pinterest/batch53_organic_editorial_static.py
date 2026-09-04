#!/usr/bin/env python3
"""Generate 200 random organic editorial static Pinterest cards."""

from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
import runpy
import sys

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
base = runpy.run_path(str(HERE / "batch52_urban_spectrum_static.py"))
runtime = base["runtime"]
cover = base["cover"]
fetch_house = base["fetch_house"]
fit_font = base["fit_font"]

OUT_DIR = HERE / "batch53_organic_editorial_static_output"
WORK_DIR = HERE / "batch53_organic_editorial_static_work"
ASSET_CHECKOUT = Path(os.environ.get("ASSET_CHECKOUT", ROOT / "pinterest_asset_checkout"))
ASSET_FOLDER = "generated_batch_53_organic_editorial_static"
IMAGE_DIR = ASSET_CHECKOUT / "pinterest" / ASSET_FOLDER
CSV_PATH = OUT_DIR / "catalog_plans_pinterest_organic_editorial_static_batch_53_200.csv"
ASSET_REF = os.environ.get("ASSET_BRANCH", "catalog-plans-pinterest-assets")
CAMPAIGN = "generated_organic_editorial_static_batch_53"
START_PIN = 9912

runtime.update({"OUT_DIR":OUT_DIR,"WORK_DIR":WORK_DIR,"MEDIA_DIR":WORK_DIR/"media","PLAN_DIR":WORK_DIR/"plan_slides","FACADE_DIR":WORK_DIR/"facade_slides","STATIC_DIR":WORK_DIR/"house_slides","VIDEO_DIR":IMAGE_DIR,"ASSET_CHECKOUT":ASSET_CHECKOUT,"ASSET_BRANCH":ASSET_REF,"CAMPAIGN":CAMPAIGN,"START_PIN":START_PIN})

SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FREE = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
FREE_BOLD = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"

def font(size,bold=False,family="sans"):
    paths={"sans":(SANS,SANS_BOLD),"serif":(SERIF,SERIF_BOLD),"free":(FREE,FREE_BOLD)}; pair=paths[family]
    return ImageFont.truetype(pair[1] if bold else pair[0],size)

def seed_for(project): return int(hashlib.sha256(("organic|"+project).encode()).hexdigest()[:16],16)
def facts(record): return (("ПЛОЩАДЬ",f"{record.area} м²"),("ЭТАЖНОСТЬ",runtime["floor_text"](record.floors)),("ГАБАРИТЫ",f"{record.dimensions} м"))

def layout_botanical(record,house):
    green,gold,terra,cream="#4A7C59","#F9A620","#B7472A","#F5F3ED"
    canvas=Image.new("RGB",(1000,1500),cream);draw=ImageDraw.Draw(canvas)
    draw.ellipse((-160,-180,340,320),fill="#DDE7D9");draw.ellipse((780,1160,1160,1540),fill="#E8D7C7")
    draw.text((62,55),"КАТАЛОГ ПРОЕКТОВ ДОМОВ",font=font(18,True,"serif"),fill=green)
    draw.text((62,105),f"№ {record.project}",font=font(39,True,"serif"),fill=terra)
    mask=Image.new("L",(860,690),0);md=ImageDraw.Draw(mask);md.rounded_rectangle((0,0,860,690),radius=150,fill=255)
    canvas.paste(cover(house,(860,690)),(70,220),mask);draw=ImageDraw.Draw(canvas)
    title=f"Дом {record.area} м²";draw.text((70,955),title,font=fit_font(draw,title,820,48,30,True),fill=green)
    for i,(label,value) in enumerate(facts(record)):
        left=70+i*290;draw.text((left,1035),label,font=font(14,True),fill=terra);draw.text((left,1075),value,font=fit_font(draw,value,250,25,17,True),fill=green)
    draw.line((70,1140,930,1140),fill="#C9D2C3",width=3)
    draw.text((70,1190),str(record.material).capitalize(),font=font(25,False,"serif"),fill=green)
    draw.rounded_rectangle((595,1160,930,1250),radius=44,fill=gold);draw.text((650,1190),"СМОТРЕТЬ ПРОЕКТ",font=font(18,True),fill="#243A2B")
    draw.text((70,1405),"catalog-plans.ru",font=font(23,True,"serif"),fill=green);return canvas

def layout_sunset(record,house):
    orange,coral,sand,deep="#E76F51","#F4A261","#E9C46A","#264653"
    canvas=Image.new("RGB",(1000,1500),deep);draw=ImageDraw.Draw(canvas)
    draw.rectangle((0,0,1000,270),fill=orange);draw.polygon([(760,0),(1000,0),(1000,270),(650,270)],fill=coral)
    draw.text((55,45),"ГОТОВЫЙ ПРОЕКТ",font=font(18,True,"serif"),fill=deep)
    title=f"Дом {record.area} м²";draw.text((55,95),title,font=fit_font(draw,title,690,55,34,True),fill=deep)
    draw.text((785,55),f"№ {record.project}",font=fit_font(draw,f"№ {record.project}",165,28,17,True),fill=deep)
    canvas.paste(cover(house,(1000,690)),(0,270));draw=ImageDraw.Draw(canvas)
    draw.rectangle((0,960,1000,1500),fill=sand)
    for i,(label,value) in enumerate(facts(record)):
        top=1010+i*82;draw.text((55,top),label,font=font(15,True),fill=deep);draw.text((350,top-5),value,font=fit_font(draw,value,565,25,17,True),fill=deep)
    draw.text((55,1270),"МАТЕРИАЛ",font=font(15,True),fill=deep);draw.text((220,1265),str(record.material).capitalize(),font=font(24),fill=deep)
    draw.rounded_rectangle((605,1240,945,1335),radius=16,fill=orange);draw.text((660,1273),"ОТКРЫТЬ ПРОЕКТ",font=font(18,True),fill=deep)
    draw.text((55,1415),"catalog-plans.ru",font=font(23,True,"serif"),fill=deep);return canvas

def layout_rose(record,house):
    rose,clay,sand,burgundy="#D4A5A5","#B87D6D","#E8D5C4","#5D2E46"
    canvas=Image.new("RGB",(1000,1500),sand);draw=ImageDraw.Draw(canvas)
    draw.rectangle((0,0,1000,185),fill=burgundy);draw.text((60,48),"АРХИТЕКТУРНЫЙ ПРОЕКТ",font=font(18,True,"free"),fill=sand)
    draw.text((760,45),f"№ {record.project}",font=fit_font(draw,f"№ {record.project}",185,29,18,True),fill=sand)
    canvas.paste(cover(house,(840,660)),(80,235));draw=ImageDraw.Draw(canvas)
    draw.rectangle((55,210,945,920),outline=clay,width=5)
    title=f"Проект дома {record.area} м²";draw.text((60,970),title,font=fit_font(draw,title,880,43,28,True),fill=burgundy)
    for i,(label,value) in enumerate(facts(record)):
        left=60+i*300;draw.rounded_rectangle((left,1050,left+272,1185),radius=22,fill="#F6ECE6")
        draw.text((left+20,1073),label,font=font(14,True,"free"),fill=clay);draw.text((left+20,1118),value,font=fit_font(draw,value,230,24,17,True),fill=burgundy)
    draw.text((60,1240),str(record.material).capitalize(),font=font(25,False,"free"),fill=burgundy)
    draw.rounded_rectangle((600,1215,940,1305),radius=45,fill=burgundy);draw.text((655,1245),"СМОТРЕТЬ ПРОЕКТ",font=font(18,True,"free"),fill="#FFFFFF")
    draw.line((60,1375,940,1375),fill=rose,width=3);draw.text((60,1415),"catalog-plans.ru",font=font(23,True,"free"),fill=burgundy);return canvas

def render_card(record):
    IMAGE_DIR.mkdir(parents=True,exist_ok=True);house=fetch_house(record.image_url);layouts=(layout_botanical,layout_sunset,layout_rose)
    layouts[seed_for(record.project)%3](record,house).save(IMAGE_DIR/f"{record.project}.jpg","JPEG",quality=93,optimize=True,progressive=True)

def validate_cards(records):
    files=[]
    for record in records:
        path=IMAGE_DIR/f"{record.project}.jpg"
        if not path.exists() or path.stat().st_size<80000: raise RuntimeError(f"Некорректная карточка: {path}")
        with Image.open(path) as image:
            if image.size!=(1000,1500) or image.format!="JPEG": raise RuntimeError(f"Некорректный формат: {path}")
        files.append(path.name)
    return {"images":len(files),"format":"JPEG","resolution":"1000x1500","files":files}

def write_csv(records):
    OUT_DIR.mkdir(parents=True,exist_ok=True);fields=["Title","Media URL","Pinterest board","Thumbnail","Description","Link","Publish date","Keywords"];rows=[]
    for offset,record in enumerate(records):
        material=str(record.material).strip();pin=START_PIN+offset
        rows.append({"Title":f"Проект дома №{record.project} площадью {record.area} м²","Media URL":f"https://raw.githubusercontent.com/nemchenik/test/{ASSET_REF}/pinterest/{ASSET_FOLDER}/{record.project}.jpg","Pinterest board":"Проекты частных домов","Thumbnail":"","Description":f"Готовый проект дома №{record.project}: площадь {record.area} м², {runtime['floor_text'](record.floors)}, габариты {record.dimensions} м, материал стен — {material}. Сохраните красивую визуализацию дома и откройте каталог, чтобы посмотреть подробности проекта и актуальную стоимость.","Link":f"{record.page_url}?utm_source=pinterest&utm_medium=organic&utm_campaign={CAMPAIGN}&utm_content=pin_{pin}_{record.project}_organic&utm_term=proekty-chastnyh-domov","Publish date":"","Keywords":f"проект дома {record.project}, проект дома {record.area} м², красивый дом, готовый проект дома, архитектура дома, {material}, catalog-plans.ru"})
    with CSV_PATH.open("w",encoding="utf-8-sig",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(rows)

runtime["generate_video"]=render_card;runtime["validate_local"]=validate_cards;runtime["write_csv"]=write_csv
if __name__=="__main__": runtime["main"]()
