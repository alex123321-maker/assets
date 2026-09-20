#!/usr/bin/env python3
"""Pure Vector SVG Generator for Cube Siege HUD Visual Kit.

Generates 100% self-contained resolution-independent vector SVG sources
for all 27 icons with native vector paths, polygons, circles, lines,
gradients, and SVG filter glows. Zero external raster images.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple


def svg_header(title: str, defs: str = "") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <title>{title}</title>
  <defs>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="12" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
    <filter id="glow-lg" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="22" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
{defs}
  </defs>
"""


def svg_footer() -> str:
    return "</svg>\n"


# -------------------------------------------------------------------------
# RESOURCES (4)
# -------------------------------------------------------------------------

def build_svg_resource_wood() -> str:
    defs = """    <linearGradient id="bark" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#7A3E10"/>
      <stop offset="100%" stop-color="#4A2508"/>
    </linearGradient>
    <linearGradient id="wood-end" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#F1C588"/>
      <stop offset="50%" stop-color="#D29A5B"/>
      <stop offset="100%" stop-color="#B87D3F"/>
    </linearGradient>"""
    body = """  <g filter="url(#glow)">
    <!-- Bottom Left Log -->
    <polygon points="105,310 235,310 361,250 231,250" fill="url(#bark)" stroke="#4A2508" stroke-width="4"/>
    <ellipse cx="170" cy="310" rx="65" ry="45" fill="url(#wood-end)" stroke="#4A2508" stroke-width="5"/>
    <ellipse cx="170" cy="310" rx="45" ry="31" fill="none" stroke="#B87D3F" stroke-width="3"/>
    <ellipse cx="170" cy="310" rx="26" ry="18" fill="none" stroke="#B87D3F" stroke-width="3"/>
    <ellipse cx="170" cy="310" rx="9" ry="6" fill="#4A2508"/>

    <!-- Bottom Right Log -->
    <polygon points="230,330 350,330 462,265 342,265" fill="url(#bark)" stroke="#4A2508" stroke-width="4"/>
    <ellipse cx="290" cy="330" rx="60" ry="42" fill="url(#wood-end)" stroke="#4A2508" stroke-width="5"/>
    <ellipse cx="290" cy="330" rx="42" ry="29" fill="none" stroke="#B87D3F" stroke-width="3"/>
    <ellipse cx="290" cy="330" rx="24" ry="17" fill="none" stroke="#B87D3F" stroke-width="3"/>
    <ellipse cx="290" cy="330" rx="8" ry="6" fill="#4A2508"/>

    <!-- Top Center Log -->
    <polygon points="160,210 300,210 432,139 292,139" fill="url(#bark)" stroke="#4A2508" stroke-width="4"/>
    <ellipse cx="230" cy="210" rx="70" ry="48" fill="url(#wood-end)" stroke="#4A2508" stroke-width="5"/>
    <ellipse cx="230" cy="210" rx="49" ry="33" fill="none" stroke="#B87D3F" stroke-width="3"/>
    <ellipse cx="230" cy="210" rx="28" ry="19" fill="none" stroke="#B87D3F" stroke-width="3"/>
    <ellipse cx="230" cy="210" rx="10" ry="7" fill="#4A2508"/>
  </g>"""
    return svg_header("Wood Resource", defs) + body + svg_footer()


def build_svg_resource_stone() -> str:
    body = """  <g filter="url(#glow)">
    <polygon points="120,380 256,440 392,380 330,320 180,320" fill="#334155" stroke="#1E293B" stroke-width="4"/>
    <polygon points="120,380 180,320 210,210 110,260" fill="#475569" stroke="#1E293B" stroke-width="4"/>
    <polygon points="180,320 330,320 290,190 210,210" fill="#64748B" stroke="#1E293B" stroke-width="4"/>
    <polygon points="330,320 392,380 410,270 340,210" fill="#475569" stroke="#1E293B" stroke-width="4"/>
    <polygon points="110,260 210,210 256,120 160,150" fill="#94A3B8" stroke="#1E293B" stroke-width="4"/>
    <polygon points="210,210 290,190 340,210 256,120" fill="#CBD5E1" stroke="#1E293B" stroke-width="4"/>
    <!-- Specular ridges -->
    <line x1="256" y1="120" x2="210" y2="210" stroke="#F1F5F9" stroke-width="5" stroke-linecap="round"/>
    <line x1="210" y1="210" x2="180" y2="320" stroke="#F1F5F9" stroke-width="5" stroke-linecap="round"/>
    <line x1="256" y1="120" x2="290" y2="190" stroke="#F1F5F9" stroke-width="5" stroke-linecap="round"/>
    <line x1="290" y1="190" x2="330" y2="320" stroke="#F1F5F9" stroke-width="5" stroke-linecap="round"/>
    <!-- Small pebble -->
    <polygon points="80,390 140,360 160,420 100,430" fill="#64748B" stroke="#334155" stroke-width="3"/>
  </g>"""
    return svg_header("Stone Resource") + body + svg_footer()


def build_svg_resource_iron() -> str:
    defs = """    <linearGradient id="iron-top" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#CBD5E1"/>
      <stop offset="50%" stop-color="#F1F5F9"/>
      <stop offset="100%" stop-color="#94A3B8"/>
    </linearGradient>
    <linearGradient id="iron-front" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#94A3B8"/>
      <stop offset="100%" stop-color="#475569"/>
    </linearGradient>"""
    body = """  <g filter="url(#glow)">
    <!-- Bottom Ingot -->
    <polygon points="150,280 330,280 372,250 192,250" fill="url(#iron-top)" stroke="#1E293B" stroke-width="4"/>
    <polygon points="330,280 370,370 412,340 372,250" fill="#64748B" stroke="#1E293B" stroke-width="4"/>
    <polygon points="150,280 330,280 370,370 110,370" fill="url(#iron-front)" stroke="#1E293B" stroke-width="4"/>
    <rect x="201" y="302" width="78" height="45" fill="#64748B" stroke="#1E293B" stroke-width="3"/>

    <!-- Top Ingot -->
    <polygon points="190,170 350,170 388,142 228,142" fill="url(#iron-top)" stroke="#1E293B" stroke-width="4"/>
    <polygon points="350,170 390,255 428,227 388,142" fill="#64748B" stroke="#1E293B" stroke-width="4"/>
    <polygon points="190,170 350,170 390,255 150,255" fill="url(#iron-front)" stroke="#1E293B" stroke-width="4"/>
    <rect x="234" y="191" width="72" height="42" fill="#64748B" stroke="#1E293B" stroke-width="3"/>

    <!-- Specular Glint -->
    <line x1="345" y1="140" x2="395" y2="140" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>
    <line x1="370" y1="115" x2="370" y2="165" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>
  </g>"""
    return svg_header("Iron Resource", defs) + body + svg_footer()


def build_svg_resource_magic_stone() -> str:
    defs = """    <linearGradient id="crystal-purple" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#E879F9"/>
      <stop offset="50%" stop-color="#A855F7"/>
      <stop offset="100%" stop-color="#581C87"/>
    </linearGradient>"""
    body = """  <g filter="url(#glow-lg)">
    <!-- Ambient Energy Aura -->
    <ellipse cx="256" cy="256" rx="160" ry="160" fill="#A855F7" opacity="0.25"/>

    <!-- Left Crystal -->
    <polygon points="150,210 100,360 145,400 150,330" fill="#9333EA" stroke="#581C87" stroke-width="3"/>
    <polygon points="150,210 150,330 145,400 190,370" fill="#581C87" stroke="#581C87" stroke-width="3"/>
    <polygon points="150,210 150,330 145,400" fill="#C084FC"/>
    <line x1="150" y1="210" x2="150" y2="330" stroke="#38BDF8" stroke-width="4"/>

    <!-- Right Crystal -->
    <polygon points="360,230 310,380 365,410 360,340" fill="#9333EA" stroke="#581C87" stroke-width="3"/>
    <polygon points="360,230 360,340 365,410 400,360" fill="#581C87" stroke="#581C87" stroke-width="3"/>
    <polygon points="360,230 360,340 365,410" fill="#C084FC"/>
    <line x1="360" y1="230" x2="360" y2="340" stroke="#38BDF8" stroke-width="4"/>

    <!-- Center Spire -->
    <polygon points="256,90 170,380 256,430 256,340" fill="#9333EA" stroke="#581C87" stroke-width="3"/>
    <polygon points="256,90 256,340 256,430 342,380" fill="#581C87" stroke="#581C87" stroke-width="3"/>
    <polygon points="256,90 256,340 256,430" fill="url(#crystal-purple)"/>
    <line x1="256" y1="90" x2="256" y2="340" stroke="#FFFFFF" stroke-width="5"/>

    <!-- Sparkles -->
    <circle cx="170" cy="140" r="6" fill="#FFFFFF"/>
    <circle cx="330" cy="160" r="6" fill="#FFFFFF"/>
    <circle cx="220" cy="240" r="5" fill="#38BDF8"/>
    <circle cx="290" cy="280" r="5" fill="#38BDF8"/>
  </g>"""
    return svg_header("Magic Stone Resource", defs) + body + svg_footer()


# -------------------------------------------------------------------------
# GLOBAL HUD (4)
# -------------------------------------------------------------------------

def build_svg_global_day() -> str:
    defs = """    <linearGradient id="sun-grad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FEF08A"/>
      <stop offset="60%" stop-color="#FBBF24"/>
      <stop offset="100%" stop-color="#F59E0B"/>
    </linearGradient>"""
    body = """  <g filter="url(#glow-lg)">
    <!-- Sunburst Corona -->
    <g fill="#FBBF24" stroke="#B45309" stroke-width="3">
      <!-- 8-12 Rays -->
      <polygon points="256,71 276,161 236,161"/>
      <polygon points="441,256 351,276 351,236"/>
      <polygon points="256,441 236,351 276,351"/>
      <polygon points="71,256 161,236 161,276"/>
      <polygon points="387,125 343,189 315,161"/>
      <polygon points="387,387 315,351 343,323"/>
      <polygon points="125,387 169,323 197,351"/>
      <polygon points="125,125 197,161 169,189"/>
    </g>
    <!-- Sun Disc -->
    <circle cx="256" cy="256" r="85" fill="url(#sun-grad)" stroke="#B45309" stroke-width="6"/>
    <circle cx="256" cy="256" r="65" fill="#FEF08A" opacity="0.6"/>
    <ellipse cx="256" cy="230" rx="35" ry="18" fill="#FFFFFF" opacity="0.75"/>
  </g>"""
    return svg_header("Day Indicator", defs) + body + svg_footer()


def build_svg_global_night() -> str:
    body = """  <g filter="url(#glow-lg)">
    <!-- Crescent Moon Path -->
    <path d="M 240,111 A 145,145 0 0,0 240,401 A 135,135 0 0,1 295,131 Z" fill="#38BDF8" stroke="#0284C7" stroke-width="4"/>
    <path d="M 240,111 A 145,145 0 0,0 150,256" fill="none" stroke="#BAE6FD" stroke-width="6" stroke-linecap="round"/>
    <!-- Stars -->
    <polygon points="340,136 347,160 371,160 352,174 358,198 340,184 322,198 328,174 309,160 333,160" fill="#BAE6FD"/>
    <polygon points="380,244 385,260 401,260 388,270 392,286 380,276 368,286 372,270 359,260 375,260" fill="#BAE6FD"/>
  </g>"""
    return svg_header("Night Indicator") + body + svg_footer()


def build_svg_global_settings() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Gear Body -->
    <path d="M 244,81 L 268,81 L 273,121 L 321,141 L 357,117 L 374,134 L 350,170 L 370,218 L 410,223 L 410,247 L 410,265 L 410,289 L 370,294 L 350,342 L 374,378 L 357,395 L 321,371 L 273,391 L 268,431 L 244,431 L 239,391 L 191,371 L 155,395 L 138,378 L 162,342 L 142,294 L 102,289 L 102,265 L 102,247 L 102,223 L 142,218 L 162,170 L 138,134 L 155,117 L 191,141 L 239,121 Z" fill="#64748B" stroke="#1E293B" stroke-width="6"/>
    <circle cx="256" cy="256" r="110" fill="#94A3B8" stroke="#1E293B" stroke-width="5"/>
    <circle cx="256" cy="256" r="55" fill="#1E293B" stroke="#475569" stroke-width="4"/>
    <circle cx="256" cy="256" r="30" fill="#E2E8F0"/>
    <!-- Rivets -->
    <circle cx="316" cy="196" r="8" fill="#E2E8F0" stroke="#1E293B" stroke-width="2"/>
    <circle cx="316" cy="316" r="8" fill="#E2E8F0" stroke="#1E293B" stroke-width="2"/>
    <circle cx="196" cy="316" r="8" fill="#E2E8F0" stroke="#1E293B" stroke-width="2"/>
    <circle cx="196" cy="196" r="8" fill="#E2E8F0" stroke="#1E293B" stroke-width="2"/>
  </g>"""
    return svg_header("Settings", "") + body + svg_footer()


def build_svg_global_build() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Architect Drafting Ruler -->
    <polygon points="130,390 370,150 410,190 170,430" fill="#CBD5E1" stroke="#0F172A" stroke-width="4"/>
    <line x1="150" y1="410" x2="166" y2="426" stroke="#0F172A" stroke-width="3"/>
    <line x1="187" y1="373" x2="203" y2="389" stroke="#0F172A" stroke-width="3"/>
    <line x1="223" y1="337" x2="239" y2="353" stroke="#0F172A" stroke-width="3"/>
    <line x1="260" y1="300" x2="276" y2="316" stroke="#0F172A" stroke-width="3"/>
    <line x1="297" y1="263" x2="313" y2="279" stroke="#0F172A" stroke-width="3"/>
    <line x1="333" y1="227" x2="349" y2="243" stroke="#0F172A" stroke-width="3"/>

    <!-- Forged Hammer -->
    <line x1="140" y1="160" x2="380" y2="400" stroke="#92400E" stroke-width="26" stroke-linecap="round"/>
    <polygon points="100,160 210,90 260,140 150,210" fill="#F59E0B" stroke="#0F172A" stroke-width="5"/>
    <polygon points="100,160 140,120 160,140 120,180" fill="#FEF08A"/>
  </g>"""
    return svg_header("Build Mode") + body + svg_footer()


# -------------------------------------------------------------------------
# WARRIOR (5)
# -------------------------------------------------------------------------

def build_svg_warrior_sword_attack() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Slash Arc -->
    <path d="M 120,380 A 180,180 0 0,1 380,120" fill="none" stroke="#EF4444" stroke-width="28" stroke-linecap="round"/>
    <path d="M 140,360 A 170,170 0 0,1 370,140" fill="none" stroke="#F97316" stroke-width="16" stroke-linecap="round"/>
    <path d="M 170,330 A 160,160 0 0,1 350,170" fill="none" stroke="#FEF08A" stroke-width="8" stroke-linecap="round"/>

    <!-- Broadsword -->
    <polygon points="370,120 195,325 180,320 165,295" fill="#E2E8F0" stroke="#1E293B" stroke-width="4"/>
    <line x1="370" y1="120" x2="180" y2="310" stroke="#38BDF8" stroke-width="4"/>
    <line x1="370" y1="120" x2="165" y2="295" stroke="#FFFFFF" stroke-width="5"/>
    <!-- Guard & Pommel -->
    <line x1="130" y1="270" x2="230" y2="370" stroke="#F59E0B" stroke-width="16" stroke-linecap="round"/>
    <line x1="180" y1="310" x2="120" y2="370" stroke="#78350F" stroke-width="12"/>
    <circle cx="120" cy="370" r="14" fill="#F59E0B" stroke="#1E293B" stroke-width="3"/>
  </g>"""
    return svg_header("Warrior Sword Attack") + body + svg_footer()


def build_svg_warrior_cleave() -> str:
    body = """  <g filter="url(#glow-lg)">
    <!-- Whirlwind Flame Vortex -->
    <path d="M 370,140 A 160,160 0 1,1 140,370" fill="none" stroke="#EA580C" stroke-width="36" stroke-linecap="round"/>
    <path d="M 350,160 A 140,140 0 1,1 160,350" fill="none" stroke="#F97316" stroke-width="20" stroke-linecap="round"/>
    <path d="M 330,180 A 120,120 0 1,1 180,330" fill="none" stroke="#FBBF24" stroke-width="10" stroke-linecap="round"/>
    <path d="M 310,200 A 100,100 0 1,1 200,310" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
    <!-- Embers -->
    <circle cx="110" cy="160" r="7" fill="#FFFBEB"/>
    <circle cx="380" cy="140" r="7" fill="#FFFBEB"/>
    <circle cx="410" cy="290" r="7" fill="#FFFBEB"/>
    <circle cx="140" cy="380" r="7" fill="#FFFBEB"/>
  </g>"""
    return svg_header("Warrior Cleave") + body + svg_footer()


def build_svg_warrior_dash() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Speed Lines -->
    <line x1="60" y1="180" x2="220" y2="180" stroke="#FBBF24" stroke-width="10" stroke-linecap="round"/>
    <line x1="40" y1="240" x2="260" y2="240" stroke="#F97316" stroke-width="16" stroke-linecap="round"/>
    <line x1="50" y1="300" x2="240" y2="300" stroke="#FBBF24" stroke-width="14" stroke-linecap="round"/>
    <line x1="80" y1="360" x2="200" y2="360" stroke="#EF4444" stroke-width="8" stroke-linecap="round"/>
    <!-- Armored Boot Silhouette -->
    <polygon points="220,150 290,180 290,280 390,340 380,380 240,380 200,280" fill="#CBD5E1" stroke="#0F172A" stroke-width="6"/>
    <line x1="210" y1="210" x2="290" y2="230" stroke="#FBBF24" stroke-width="5"/>
    <line x1="200" y1="280" x2="300" y2="300" stroke="#FBBF24" stroke-width="5"/>
    <polygon points="160,240 220,230 190,290" fill="#F97316" stroke="#0F172A" stroke-width="4"/>
  </g>"""
    return svg_header("Warrior Dash") + body + svg_footer()


def build_svg_warrior_parry() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Heater Shield -->
    <polygon points="150,150 330,150 350,280 240,420 130,280" fill="#1E3A8A" stroke="#F59E0B" stroke-width="10"/>
    <line x1="240" y1="160" x2="240" y2="420" stroke="#F59E0B" stroke-width="6"/>
    <!-- Deflecting Blade -->
    <line x1="380" y1="130" x2="120" y2="390" stroke="#E2E8F0" stroke-width="18" stroke-linecap="round"/>
    <line x1="380" y1="130" x2="120" y2="390" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round"/>
    <!-- Starburst Impact -->
    <g stroke="#FFFFFF" stroke-width="5" stroke-linecap="round">
      <line x1="260" y1="185" x2="260" y2="315"/>
      <line x1="195" y1="250" x2="325" y2="250"/>
      <line x1="214" y1="204" x2="306" y2="296"/>
      <line x1="214" y1="296" x2="306" y2="204"/>
    </g>
  </g>"""
    return svg_header("Warrior Parry") + body + svg_footer()


def build_svg_warrior_duel() -> str:
    body = """  <g filter="url(#glow-lg)">
    <!-- Crossed Blades -->
    <line x1="120" y1="130" x2="390" y2="400" stroke="#E2E8F0" stroke-width="16" stroke-linecap="round"/>
    <line x1="120" y1="130" x2="390" y2="400" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>
    <line x1="390" y1="130" x2="120" y2="400" stroke="#CBD5E1" stroke-width="16" stroke-linecap="round"/>
    <line x1="390" y1="130" x2="120" y2="400" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>
    <!-- Crown -->
    <polygon points="170,170 190,100 225,130 256,80 287,130 322,100 342,170" fill="#FBBF24" stroke="#18181B" stroke-width="5"/>
    <path d="M 160,296 A 96,96 0 0,0 352,296" fill="none" stroke="#FBBF24" stroke-width="12" stroke-linecap="round"/>
  </g>"""
    return svg_header("Warrior Duel") + body + svg_footer()


# -------------------------------------------------------------------------
# ARCHER (5)
# -------------------------------------------------------------------------

def build_svg_archer_shot() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Recurve Bow -->
    <path d="M 140,140 A 140,140 0 0,0 140,360" fill="none" stroke="#92400E" stroke-width="16" stroke-linecap="round"/>
    <line x1="140" y1="140" x2="210" y2="290" stroke="#E2E8F0" stroke-width="3"/>
    <line x1="210" y1="290" x2="140" y2="360" stroke="#E2E8F0" stroke-width="3"/>
    <!-- Loose Arrow -->
    <line x1="170" y1="340" x2="320" y2="190" stroke="#38BDF8" stroke-width="18" stroke-linecap="round" opacity="0.6"/>
    <line x1="190" y1="320" x2="400" y2="110" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round"/>
    <polygon points="400,110 365,120 390,145" fill="#38BDF8" stroke="#0C4A6E" stroke-width="3"/>
  </g>"""
    return svg_header("Archer Shot") + body + svg_footer()


def build_svg_archer_piercing_shot() -> str:
    body = """  <g filter="url(#glow-lg)">
    <!-- Shockwave Rings -->
    <circle cx="280" cy="230" r="90" fill="none" stroke="#00E5FF" stroke-width="5"/>
    <circle cx="330" cy="180" r="60" fill="none" stroke="#00E5FF" stroke-width="5"/>
    <circle cx="370" cy="140" r="40" fill="none" stroke="#00E5FF" stroke-width="5"/>
    <!-- Triple Arrows -->
    <!-- Lower -->
    <line x1="75" y1="415" x2="345" y2="145" stroke="#00E5FF" stroke-width="10"/>
    <line x1="75" y1="415" x2="345" y2="145" stroke="#FFFFFF" stroke-width="4"/>
    <polygon points="345,145 320,153 337,170" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
    <!-- Center -->
    <line x1="110" y1="380" x2="380" y2="110" stroke="#00E5FF" stroke-width="12"/>
    <line x1="110" y1="380" x2="380" y2="110" stroke="#FFFFFF" stroke-width="5"/>
    <polygon points="380,110 355,118 372,135" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
    <!-- Upper -->
    <line x1="145" y1="345" x2="415" y2="75" stroke="#00E5FF" stroke-width="10"/>
    <line x1="145" y1="345" x2="415" y2="75" stroke="#FFFFFF" stroke-width="4"/>
    <polygon points="415,75 390,83 407,100" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
  </g>"""
    return svg_header("Archer Piercing Shot") + body + svg_footer()


def build_svg_archer_roll() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Swirling Vortex -->
    <path d="M 296,256 A 40,40 0 0,1 256,296 A 70,70 0 0,1 186,256 A 100,100 0 0,1 256,156 A 130,130 0 0,1 386,256 A 160,160 0 0,1 256,416" fill="none" stroke="#38BDF8" stroke-width="14" stroke-linecap="round"/>
    <polygon points="236,196 276,226 256,306" fill="#BAE6FD" stroke="#0284C7" stroke-width="3"/>
  </g>"""
    return svg_header("Archer Roll") + body + svg_footer()


def build_svg_archer_decoy() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Cloak & Hood -->
    <polygon points="256,100 320,170 300,260 212,260 192,170" fill="#4338CA" opacity="0.6" stroke="#38BDF8" stroke-width="4"/>
    <polygon points="192,260 320,260 380,400 132,400" fill="#312E81" opacity="0.6" stroke="#818CF8" stroke-width="4"/>
    <!-- Scanlines -->
    <line x1="140" y1="180" x2="370" y2="180" stroke="#38BDF8" stroke-width="2" opacity="0.5"/>
    <line x1="140" y1="230" x2="370" y2="230" stroke="#38BDF8" stroke-width="2" opacity="0.5"/>
    <line x1="140" y1="280" x2="370" y2="280" stroke="#38BDF8" stroke-width="2" opacity="0.5"/>
    <line x1="140" y1="330" x2="370" y2="330" stroke="#38BDF8" stroke-width="2" opacity="0.5"/>
    <line x1="140" y1="380" x2="370" y2="380" stroke="#38BDF8" stroke-width="2" opacity="0.5"/>
    <!-- Glowing eyes -->
    <ellipse cx="237" cy="185" rx="8" ry="5" fill="#E0E7FF"/>
    <ellipse cx="274" cy="185" rx="8" ry="5" fill="#E0E7FF"/>
  </g>"""
    return svg_header("Archer Decoy") + body + svg_footer()


def build_svg_archer_sniper() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Reticle Outer Ring -->
    <circle cx="256" cy="256" r="150" fill="none" stroke="#22D3EE" stroke-width="6"/>
    <circle cx="256" cy="256" r="70" fill="none" stroke="#F43F5E" stroke-width="4"/>
    <circle cx="256" cy="256" r="12" fill="#F43F5E" stroke="#FFFFFF" stroke-width="2"/>
    <!-- Crosshairs -->
    <line x1="76" y1="256" x2="216" y2="256" stroke="#22D3EE" stroke-width="4"/>
    <line x1="296" y1="256" x2="436" y2="256" stroke="#22D3EE" stroke-width="4"/>
    <line x1="256" y1="76" x2="256" y2="216" stroke="#22D3EE" stroke-width="4"/>
    <line x1="256" y1="296" x2="256" y2="436" stroke="#22D3EE" stroke-width="4"/>
    <!-- Corner Nodes -->
    <circle cx="337" cy="175" r="6" fill="#22D3EE"/>
    <circle cx="337" cy="337" r="6" fill="#22D3EE"/>
    <circle cx="175" cy="337" r="6" fill="#22D3EE"/>
    <circle cx="175" cy="175" r="6" fill="#22D3EE"/>
  </g>"""
    return svg_header("Archer Sniper") + body + svg_footer()


# -------------------------------------------------------------------------
# ENGINEER (5)
# -------------------------------------------------------------------------

def build_svg_engineer_hammer() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Hammer Head -->
    <polygon points="130,230 250,110 330,190 210,310" fill="#E2E8F0" stroke="#1E293B" stroke-width="6"/>
    <polygon points="180,180 230,130 280,180 230,230" fill="#F59E0B" stroke="#1E293B" stroke-width="4"/>
    <!-- Pneumatic Shaft -->
    <line x1="280" y1="150" x2="410" y2="40" stroke="#475569" stroke-width="22" stroke-linecap="round"/>
    <line x1="280" y1="150" x2="410" y2="40" stroke="#F59E0B" stroke-width="6"/>
    <!-- Electric Sparks -->
    <line x1="130" y1="230" x2="120" y2="250" stroke="#38BDF8" stroke-width="4"/>
    <line x1="130" y1="230" x2="90" y2="310" stroke="#38BDF8" stroke-width="4"/>
    <line x1="130" y1="230" x2="140" y2="340" stroke="#38BDF8" stroke-width="4"/>
    <line x1="130" y1="230" x2="70" y2="220" stroke="#38BDF8" stroke-width="4"/>
    <line x1="130" y1="230" x2="180" y2="360" stroke="#38BDF8" stroke-width="4"/>
  </g>"""
    return svg_header("Engineer Hammer") + body + svg_footer()


def build_svg_engineer_turret() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Tripod Legs -->
    <line x1="256" y1="330" x2="130" y2="410" stroke="#0F172A" stroke-width="14" stroke-linecap="round"/>
    <line x1="256" y1="330" x2="382" y2="410" stroke="#0F172A" stroke-width="14" stroke-linecap="round"/>
    <line x1="256" y1="330" x2="256" y2="430" stroke="#64748B" stroke-width="12" stroke-linecap="round"/>
    <ellipse cx="256" cy="330" rx="56" ry="30" fill="#64748B" stroke="#0F172A" stroke-width="5"/>
    <!-- Dome -->
    <polygon points="190,310 220,210 292,210 322,310" fill="#94A3B8" stroke="#0F172A" stroke-width="5"/>
    <!-- Barrels -->
    <line x1="230" y1="230" x2="120" y2="160" stroke="#0F172A" stroke-width="16" stroke-linecap="round"/>
    <line x1="120" y1="160" x2="105" y2="150" stroke="#F59E0B" stroke-width="14" stroke-linecap="round"/>
    <line x1="270" y1="250" x2="160" y2="180" stroke="#0F172A" stroke-width="16" stroke-linecap="round"/>
    <line x1="160" y1="180" x2="145" y2="170" stroke="#F59E0B" stroke-width="14" stroke-linecap="round"/>
    <!-- Eye Sensor -->
    <circle cx="256" cy="246" r="16" fill="#0EA5E9" stroke="#FFFFFF" stroke-width="2"/>
  </g>"""
    return svg_header("Engineer Turret") + body + svg_footer()


def build_svg_engineer_dash() -> str:
    body = """  <g filter="url(#glow-lg)">
    <!-- Backpack -->
    <rect x="170" y="150" width="172" height="50" rx="6" fill="#94A3B8" stroke="#0F172A" stroke-width="4"/>
    <!-- Left Thruster -->
    <polygon points="155,200 225,200 235,260 145,260" fill="#475569" stroke="#0F172A" stroke-width="4"/>
    <polygon points="152,260 190,420 228,260" fill="#F97316"/>
    <polygon points="170,260 190,370 210,260" fill="#FBBF24"/>
    <polygon points="180,260 190,320 200,260" fill="#FEF08A"/>
    <!-- Right Thruster -->
    <polygon points="287,200 357,200 367,260 277,260" fill="#475569" stroke="#0F172A" stroke-width="4"/>
    <polygon points="284,260 322,420 360,260" fill="#F97316"/>
    <polygon points="302,260 322,370 342,260" fill="#FBBF24"/>
    <polygon points="312,260 322,320 332,260" fill="#FEF08A"/>
  </g>"""
    return svg_header("Engineer Dash") + body + svg_footer()


def build_svg_engineer_mine() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Spikes -->
    <line x1="100" y1="166" x2="412" y2="346" stroke="#0F172A" stroke-width="22" stroke-linecap="round"/>
    <line x1="100" y1="346" x2="412" y2="166" stroke="#0F172A" stroke-width="22" stroke-linecap="round"/>
    <line x1="76" y1="256" x2="436" y2="256" stroke="#0F172A" stroke-width="22" stroke-linecap="round"/>
    <!-- Hex Body -->
    <polygon points="396,256 326,377 186,377 116,256 186,135 326,135" fill="#334155" stroke="#0F172A" stroke-width="6"/>
    <circle cx="256" cy="256" r="95" fill="#0F172A" stroke="#FBBF24" stroke-width="8"/>
    <!-- Sensor Dome -->
    <circle cx="256" cy="256" r="55" fill="#EF4444" stroke="#FFFFFF" stroke-width="3"/>
    <ellipse cx="245" cy="235" rx="16" ry="8" fill="#FFFFFF"/>
  </g>"""
    return svg_header("Engineer Mine") + body + svg_footer()


def build_svg_engineer_overclock() -> str:
    body = """  <g filter="url(#glow-lg)">
    <!-- Clockwork Gear -->
    <circle cx="256" cy="256" r="140" fill="#F59E0B" stroke="#1E293B" stroke-width="6"/>
    <circle cx="256" cy="256" r="85" fill="#1E293B" stroke="#F59E0B" stroke-width="6"/>
    <!-- Lightning Arcs -->
    <polyline points="100,120 180,200 220,180 260,260 380,360" fill="none" stroke="#38BDF8" stroke-width="12" stroke-linecap="round"/>
    <polyline points="100,120 180,200 220,180 260,260 380,360" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
    <polyline points="400,130 320,210 280,240 240,320 130,390" fill="none" stroke="#38BDF8" stroke-width="12" stroke-linecap="round"/>
    <polyline points="400,130 320,210 280,240 240,320 130,390" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
    <circle cx="256" cy="256" r="30" fill="#EF4444" stroke="#FFFFFF" stroke-width="3"/>
  </g>"""
    return svg_header("Engineer Overclock") + body + svg_footer()


# -------------------------------------------------------------------------
# AUXILIARY (4)
# -------------------------------------------------------------------------

def build_svg_hud_skull_wave() -> str:
    body = """  <g filter="url(#glow-lg)">
    <!-- Cranium -->
    <polygon points="160,240 170,150 256,110 342,150 352,240 312,310 200,310" fill="#FEE2E2" stroke="#1C1917" stroke-width="6"/>
    <polygon points="205,310 307,310 292,380 220,380" fill="#FEE2E2" stroke="#1C1917" stroke-width="6"/>
    <!-- Teeth -->
    <line x1="238" y1="330" x2="238" y2="380" stroke="#1C1917" stroke-width="5"/>
    <line x1="256" y1="330" x2="256" y2="380" stroke="#1C1917" stroke-width="5"/>
    <line x1="274" y1="330" x2="274" y2="380" stroke="#1C1917" stroke-width="5"/>
    <!-- Eyes -->
    <polygon points="195,220 235,240 205,265" fill="#EF4444" stroke="#1C1917" stroke-width="3"/>
    <polygon points="317,220 277,240 307,265" fill="#EF4444" stroke="#1C1917" stroke-width="3"/>
    <polygon points="256,270 248,295 264,295" fill="#1C1917"/>
  </g>"""
    return svg_header("Wave Skull Indicator") + body + svg_footer()


def build_svg_hud_health_cross() -> str:
    body = """  <g filter="url(#glow-lg)">
    <!-- Vitality Cross -->
    <polygon points="201,106 311,106 311,201 406,201 406,311 311,311 311,406 201,406 201,311 106,311 106,201 201,201" fill="#10B981" stroke="#064E3B" stroke-width="8"/>
    <polygon points="221,126 291,126 291,221 386,221 386,291 291,291 291,386 221,386 221,291 126,291 126,221 221,221" fill="#34D399"/>
    <line x1="256" y1="136" x2="256" y2="376" stroke="#ECFDF5" stroke-width="6" stroke-linecap="round"/>
    <line x1="136" y1="256" x2="376" y2="256" stroke="#ECFDF5" stroke-width="6" stroke-linecap="round"/>
  </g>"""
    return svg_header("Vitality Cross") + body + svg_footer()


def build_svg_hud_armor_shield() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Kite Shield -->
    <polygon points="150,120 362,120 372,260 256,420 140,260" fill="#3B82F6" stroke="#E2E8F0" stroke-width="12"/>
    <polygon points="256,130 355,255 256,400" fill="#1D4ED8"/>
    <!-- Rivets -->
    <circle cx="165" cy="140" r="6" fill="#E2E8F0" stroke="#0F172A" stroke-width="2"/>
    <circle cx="256" cy="135" r="6" fill="#E2E8F0" stroke="#0F172A" stroke-width="2"/>
    <circle cx="347" cy="140" r="6" fill="#E2E8F0" stroke="#0F172A" stroke-width="2"/>
    <circle cx="360" cy="250" r="6" fill="#E2E8F0" stroke="#0F172A" stroke-width="2"/>
    <circle cx="256" cy="405" r="6" fill="#E2E8F0" stroke="#0F172A" stroke-width="2"/>
    <circle cx="152" cy="250" r="6" fill="#E2E8F0" stroke="#0F172A" stroke-width="2"/>
  </g>"""
    return svg_header("Armor Shield") + body + svg_footer()


def build_svg_hud_target_range() -> str:
    body = """  <g filter="url(#glow)">
    <!-- Rings -->
    <circle cx="256" cy="256" r="160" fill="none" stroke="#F59E0B" stroke-width="6"/>
    <circle cx="256" cy="256" r="110" fill="none" stroke="#F59E0B" stroke-width="6"/>
    <circle cx="256" cy="256" r="60" fill="none" stroke="#F59E0B" stroke-width="6"/>
    <circle cx="256" cy="256" r="20" fill="#F59E0B" stroke="#FDE68A" stroke-width="3"/>
    <!-- Ticks -->
    <line x1="336" y1="256" x2="436" y2="256" stroke="#FDE68A" stroke-width="5"/>
    <line x1="76" y1="256" x2="176" y2="256" stroke="#FDE68A" stroke-width="5"/>
    <line x1="256" y1="76" x2="256" y2="176" stroke="#FDE68A" stroke-width="5"/>
    <line x1="256" y1="336" x2="256" y2="436" stroke="#FDE68A" stroke-width="5"/>
  </g>"""
    return svg_header("Target Range") + body + svg_footer()


# -------------------------------------------------------------------------
# REGISTRY & BUILDER
# -------------------------------------------------------------------------

SVG_BUILDERS: Dict[str, any] = {
    "resource_wood": build_svg_resource_wood,
    "resource_stone": build_svg_resource_stone,
    "resource_iron": build_svg_resource_iron,
    "resource_magic_stone": build_svg_resource_magic_stone,
    "global_day": build_svg_global_day,
    "global_night": build_svg_global_night,
    "global_settings": build_svg_global_settings,
    "global_build": build_svg_global_build,
    "warrior_sword_attack": build_svg_warrior_sword_attack,
    "warrior_cleave": build_svg_warrior_cleave,
    "warrior_dash": build_svg_warrior_dash,
    "warrior_parry": build_svg_warrior_parry,
    "warrior_duel": build_svg_warrior_duel,
    "archer_shot": build_svg_archer_shot,
    "archer_piercing_shot": build_svg_archer_piercing_shot,
    "archer_roll": build_svg_archer_roll,
    "archer_decoy": build_svg_archer_decoy,
    "archer_sniper": build_svg_archer_sniper,
    "engineer_hammer": build_svg_engineer_hammer,
    "engineer_turret": build_svg_engineer_turret,
    "engineer_dash": build_svg_engineer_dash,
    "engineer_mine": build_svg_engineer_mine,
    "engineer_overclock": build_svg_engineer_overclock,
    "hud_skull_wave": build_svg_hud_skull_wave,
    "hud_health_cross": build_svg_hud_health_cross,
    "hud_armor_shield": build_svg_hud_armor_shield,
    "hud_target_range": build_svg_hud_target_range,
}


def export_all_svgs(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for slug, fn in SVG_BUILDERS.items():
        svg_code = fn()
        out_file = target_dir / f"{slug}.svg"
        out_file.write_text(svg_code, encoding="utf-8")
