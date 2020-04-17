import pygame, re, sys, random
import pygame.locals as plocals

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    print("Usage: %s [filename]" % sys.argv[0])
    sys.exit(1)

ON_COLOR = (205,205,205)
OFF_COLOR = (50,50,50)
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

from SChip import CHIP8, CHIP8Error
def printmem(chip):
    for i in range(0, 4096, 16):
        tmp = ""
        for j in chip.memory[i:i+(16)]:
            tmp += hex(j) + "\t"
        print(tmp)

def draw(chip, win):
    if "hires" in dir(chip) and chip.hires:
        for i in range(128*64):
            pix_rect = (
                i%128*(PIX_SIZE/2), i//128*(PIX_SIZE/2),
                (PIX_SIZE/2), (PIX_SIZE/2)
            )
            if chip.gfx[i]:
                pygame.draw.rect(win, ON_COLOR, pix_rect)
            else:
                pygame.draw.rect(win, OFF_COLOR, pix_rect)
    else:
        for i in range(64*32):
            pix_rect = (
                i%64*PIX_SIZE, i//64*PIX_SIZE,
                PIX_SIZE, PIX_SIZE
            )
            if chip.gfx[i]:
                pygame.draw.rect(win, ON_COLOR, pix_rect)
            else:
                pygame.draw.rect(win, OFF_COLOR, pix_rect)
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
try:
    while True:
        for _ in range(TPF-1):
            c.cycle(0)
            #opcode = c.memory[c.pc] << 8 | c.memory[c.pc + 1]
            #print("Registers: %s" % " ".join([str(i) for i in c.V]))
            #input(f"I: {hex(c.I)}\tPC: {hex(c.pc)}\tOphex: {hex(opcode)}")
        c.cycle(clock.tick(FPS)/1000)
        if c.drawFlag:
            c.drawFlag = False
            draw(c, win)
        if buzz_playing != (c.sound_timer >= 0):
            if buzz_playing:
                buzz.stop()
            else:
                buzz.play(-1)
            buzz_playing = not buzz_playing
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
    pygame.quit()
except KeyboardInterrupt:
    print("Goodbye!")
    pygame.quit()
