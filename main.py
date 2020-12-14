#!/usr/bin/env python3
try:
    import better_exceptions as b_e
    import sys
    sys.excepthook = b_e.excepthook
except ImportError:
    pass

import pygame, re, sys, random, os, pickle
import pygame.locals as plocals

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    print("Usage: %s [filename]" % sys.argv[0])
    sys.exit(1)

OFF_COLOR =     ( 20, 50, 80)
FG1_COLOR =     (100,255,100)
FG2_COLOR =     (255,100,100)
BLENDED_COLOR = (255,255,100)
PIX_SIZE = 20
TPF = 200 # Ticks per Frame
FPS = 60 # Frames per Second
KEYMAP = {
    plocals.K_1: 0x1, plocals.K_2: 0x2, plocals.K_3: 0x3, plocals.K_4: 0xC,
    plocals.K_q: 0x4, plocals.K_w: 0x5, plocals.K_e: 0x6, plocals.K_r: 0xD,
    plocals.K_a: 0x7, plocals.K_s: 0x8, plocals.K_d: 0x9, plocals.K_f: 0xE,
    plocals.K_z: 0xA, plocals.K_x: 0x0, plocals.K_c: 0xB, plocals.K_v: 0xF,
    
    plocals.K_SPACE: 0x6,
    
                         plocals.K_UP:   0x5,
    plocals.K_LEFT: 0x7, plocals.K_DOWN: 0x8, plocals.K_RIGHT: 0x9,
}

pygame.mixer.init(44100, -16, 1, 64)
pygame.init()
win = pygame.display.set_mode((64*PIX_SIZE,32*PIX_SIZE))
pygame.display.set_caption("Chippy")

from XOChip import CHIP8, CHIP8Error
def printmem(chip):
    for i in range(0, 4096, 16):
        tmp = ""
        for j in chip.memory[i:i+(16)]:
            tmp += hex(j) + "\t"
        print(tmp)

def draw(chip, win):
    hires = chip.type in ["SCHIP", "XO-CHIP"] and chip.hires
    for i in range(64*32*(4 if hires else 1)):
        if hires:
            pix_rect = (
                i%128*(PIX_SIZE/2), i//128*(PIX_SIZE/2),
                (PIX_SIZE/2), (PIX_SIZE/2)
            )
        else:
            pix_rect = (
                i%64*PIX_SIZE, i//64*PIX_SIZE,
                PIX_SIZE, PIX_SIZE
            )
        if chip.gfx[i]:
            color = FG1_COLOR
        else:
            color = OFF_COLOR
        if chip.type == "XO-CHIP" and chip.gfx2[i]:
            color = (FG2_COLOR if color == OFF_COLOR else BLENDED_COLOR)
        pygame.draw.rect(win, color, pix_rect)
    pygame.display.update()

def loadfile(filename):
    f = open(filename, "rb")
    return f.read()

c = CHIP8(loadfile(filename)) #bytes([0x60, 0x01, 0x61, 0x01, 0x60, 0x00, 0x61, 0x00, 0x12, 0x00]))
# For IDLE autocomplete
self = c

draw(c, win)
clock = pygame.time.Clock()
buzz = pygame.mixer.Sound("buzzer.wav")
buzz_playing = False
if c.type in ["SCHIP", "XO-CHIP"]:
    if os.path.isfile(filename + ".flags"):
        flags = pickle.load(open(filename + ".flags", "rb"))
    else:
        flags = bytearray(8)
    c.flags = flags
buzz.set_volume(0)
buzz.play(-1)
try:
    while True:
        for _ in range(TPF-1):
            c.cycle(0)
            #opcode = c.memory[c.pc] << 8 | c.memory[c.pc + 1]
            #print("Registers: %s" % " ".join([str(i) for i in c.V]))
            #input(f"I: {hex(c.I)}\tPC: {hex(c.pc)}\tOphex: {hex(opcode)}")
        ret = c.cycle(clock.tick(FPS)/1000)
        if ret == "exit":
            raise KeyboardInterrupt()
        if c.drawFlag:
            c.drawFlag = False
            draw(c, win)
        # if buzz_playing != (c.sound_timer >= 0):
        #     if buzz_playing:
        #         buzz.stop()
        #     else:
        #         buzz.play(-1)
        #     buzz_playing = not buzz_playing
        buzz.set_volume(int(c.sound_timer>=1))
        for event in pygame.event.get():
            if event.type == 2: #Key down
                if event.key in KEYMAP:
                    c.keys[KEYMAP[event.key]] = 1
            if event.type == 3: #Key up
                if event.key in KEYMAP:
                    c.keys[KEYMAP[event.key]] = 0
            if event.type == 12: #Quit
                raise KeyboardInterrupt()
except CHIP8Error as e:
    sys.stderr.write("CHIP-8 Error: " + str(e) + "\n")
except KeyboardInterrupt:
    print("Goodbye!")
pygame.quit()
if c.type in ["SCHIP", "XO-CHIP"]:
    pickle.dump(c.flags, open(filename + ".flags", "wb+"))
