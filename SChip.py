import random, re

#4x5 hex fontset
from fontset import fontset

class SCHIPError(Exception):
    pass

class SCHIP:
    def __init__(self, cartdata=bytes()):
        self.memory = bytearray(4096)
        self.V = bytearray(16)
        self.I = 0
        self.pc = 512
        self.gfx = bytearray(128*64)

        self.delay_timer = 0
        self.sound_timer = 0

        self.keys = bytearray(16)

        self.drawFlag = False

        self.stack = []
        
        self.keypress_tmp = set()
        
        self.hires = False

        for i in range(len(fontset)):
            self.memory[i + 80] = fontset[i]

        for i in range(len(cartdata)):
            self.memory[i + 512] = cartdata[i]

    def cycle(self, delta):
        # Get Opcode
        opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
        ophex = "{:0>4}".format(hex(opcode)[2:]).upper()
        
        # Decode and Execute Opcode
        if re.fullmatch("00C.", ophex):
            # 00Cx: Scroll the display down x pixels
            amount = int(ophex[3],16) * 128
            self.gfx = self.gfx[:-amount].rjust(128*64, b"\x00")
        elif ophex == "00E0":
            # 00E0: Clear screen
            self.gfx = bytearray(128*64)
            self.drawFlag = True
        elif ophex == "00EE":
            # 00EE: Return from subroutine
            if len(self.stack) == 0:
                raise CHIP8Error(f"Return at {hex(self.pc)} has nowhere to go")
            self.pc = self.stack.pop() - 2
        elif ophex == "00FE":
            # 00FF: Set low resolution
            self.hires = False
            # Same as 00E0: Clear screen
            self.gfx = bytearray(128*64)
            self.drawFlag = True
        elif ophex == "00FF":
            # 00FF: Set high resolution
            self.hires = True
            # Same as 00E0: Clear screen
            self.gfx = bytearray(128*64)
            self.drawFlag = True
        elif re.fullmatch("1...", ophex):
            # 1xxx: Jump to [nnn]
            self.pc = int(ophex[1:],16) - 2
        elif re.fullmatch("2...", ophex):
            # 2nnn: Call subroutine at [nnn]
            if len(self.stack) == 16:
                raise CHIP8Error(f"Stack is full, cannot call subroutine")
            self.stack.append(self.pc + 2)
            self.pc = int(ophex[1:],16) - 2
        elif re.fullmatch("3...", ophex):
            # 3xnn: Skips next instruction if V[x] equals [nn]
            if self.V[int(ophex[1],16)] == int(ophex[2:],16):
                self.pc += 2
        elif re.fullmatch("4...", ophex):
            # 4xnn: Skips next instruction if V[x] doesn't equal [nn]
            if self.V[int(ophex[1],16)] != int(ophex[2:],16):
                self.pc += 2
        elif re.fullmatch("5..0", ophex):
            # 5xy0: Skips next instruction if V[x] equals V[y]
            if self.V[int(ophex[1],16)] == self.V[int(ophex[2],16)]:
                self.pc += 2
        elif re.fullmatch("6...", ophex):
            # 6xnn: Set V[x] to [nn]
            self.V[int(ophex[1],16)] = int(ophex[2:],16)
        elif re.fullmatch("7...", ophex):
            # 7xnn: Add [nn] to V[x]
            self.V[int(ophex[1],16)] = (
                self.V[int(ophex[1],16)] + int(ophex[2:],16)
            ) % 256
        elif re.fullmatch("8..0", ophex):
            # 8xy0: Set V[x] to V[y]
            self.V[int(ophex[1],16)] = self.V[int(ophex[2],16)]
        elif re.fullmatch("8..1", ophex):
            # 8xy1: Set V[x] to V[x] OR V[y]
            self.V[int(ophex[1],16)] |= self.V[int(ophex[2],16)]
        elif re.fullmatch("8..2", ophex):
            # 8xy2: Set V[x] to V[x] AND V[y]
            self.V[int(ophex[1],16)] &= self.V[int(ophex[2],16)]
        elif re.fullmatch("8..3", ophex):
            # 8xy3: Set V[x] to V[x] XOR V[y]
            self.V[int(ophex[1],16)] ^= self.V[int(ophex[2],16)]
        elif re.fullmatch("8..4", ophex):
            # 8xy4: Add V[y] to V[x], and set Vf to whether there was an
            # overflow or not
            total = self.V[int(ophex[1],16)] + self.V[int(ophex[2],16)]
            self.V[int(ophex[1],16)] = total % 256
            self.V[15] = total > 256
        elif re.fullmatch("8..5", ophex):
            # 8xy7: Subtract V[y] from V[x], and set Vf to whether there was
            # a borrow or not
            total =  self.V[int(ophex[1],16)] - self.V[int(ophex[2],16)]
            self.V[int(ophex[1],16)] = total % 256
            self.V[15] = total >= 0
        elif re.fullmatch("8..6", ophex):
            # 8xy6: Shifts V[y] to the right by 1, putting the underflowflow
            # in Vf, and putting the result in V[x]
            self.V[15] = self.V[int(ophex[2],16)] & 1
            self.V[int(ophex[1],16)] = (self.V[int(ophex[2],16)]>>1)%256
        elif re.fullmatch("8..7", ophex):
            # 8xy7: Subtract V[y] from V[x], and set Vf to whether there was
            # a borrow or not
            total = self.V[int(ophex[2],16)] - self.V[int(ophex[1],16)]
            self.V[int(ophex[1],16)] = total % 256
            self.V[15] = total >= 0
        elif re.fullmatch("8..E", ophex):
            # 8xyE: Shifts V[y] to the left by 1, putting the overflow in Vf,
            # and putting the result in V[x]
            self.V[15] = self.V[int(ophex[2],16)]//128
            self.V[int(ophex[1],16)] = (self.V[int(ophex[2],16)]<<1)%256
        elif re.fullmatch("9..0", ophex):
            # 9xy0: Skips next instruction if V[x] doesn't equal V[y]
            if self.V[int(ophex[1],16)] != self.V[int(ophex[2],16)]:
                self.pc += 2
        elif re.fullmatch("A...", ophex):
            # Annn: Set I to [nnn]
            self.I = int(ophex[1:],16)
        elif re.fullmatch("B...", ophex):
            # Bnnn: Jump to [nnn] plus V0
            self.pc = int(ophex[1:],16) + self.V[0] - 2
        elif re.fullmatch("C...", ophex):
            # Cxnn: Set V[x] to a random number, and bitwise-AND it with [nn]
            self.V[int(ophex[1],16)] = random.randint(0, 255) & int(ophex[2:],16)
        elif re.fullmatch("D...", ophex):
            # Dxyn: XOR sprite stored at the I pointer with height [n] at [x], [y] onto display
            flipped_on = False
            x, y = self.V[int(ophex[1],16)], self.V[int(ophex[2],16)]
            if int(ophex[3],16) > 0:
                for sy in range(int(ophex[3],16)):
                    for sx in range(8):
                        sprite_index = self.I + sy
                        if not self.memory[sprite_index] & (128 >> sx):
                            continue
                        if self.hires:
                            gfx_index = ((x+sx)%128) + (((y+sy)%64)*128)
                        else:
                            gfx_index = ((x+sx)%64) + (((y+sy)%32)*64)
                        if self.gfx[gfx_index]:
                            flipped_on = True
                        self.gfx[gfx_index] ^= 1
            else:
                for sy in range(16):
                    for sx in range(16):
                        sprite_index = self.I + sy*2 + sx//8
                        if not self.memory[sprite_index] & (128 >> (sx%8)):
                            continue
                        if self.hires:
                            gfx_index = ((x+sx)%128) + (((y+sy)%64)*128)
                        else:
                            gfx_index = ((x+sx)%64) + (((y+sy)%32)*64)
                        if self.gfx[gfx_index]:
                            flipped_on = True
                        self.gfx[gfx_index] ^= 1
            self.V[15] = int(flipped_on)
            self.drawFlag = True
        elif re.fullmatch("E.9E", ophex):
            # ExA1: Skips next instruction if the key V[x] is pressed
            if self.V[int(ophex[1],16)] < 16 and self.keys[self.V[int(ophex[1],16)]]:
                self.pc += 2
        elif re.fullmatch("E.A1", ophex):
            # ExA1: Skips next instruction if the key V[x] is not pressed
            if self.V[int(ophex[1],16)] > 15 or not self.keys[self.V[int(ophex[1],16)]]:
                self.pc += 2
        elif re.fullmatch("F.07", ophex):
            # Fx07: Set V[x] to delay timer
            self.V[int(ophex[1],16)] = int(self.delay_timer)
        elif re.fullmatch("F.15", ophex):
            # Fx15: Set delay timer to V[x]
            self.delay_timer = self.V[int(ophex[1],16)]
        elif re.fullmatch("F.18", ophex):
            # Fx15: Set sound timer to V[x]
            self.sound_timer = self.V[int(ophex[1],16)]
        elif re.fullmatch("F.0A", ophex):
            # Fx0A: Await key press and release and store in V[x]
            success = False
            for i in range(16):
                if self.keys[i]:
                    self.keypress_tmp.add(i)
            to_remove = []
            for i in self.keypress_tmp:
                if not self.keys[i]:
                    self.V[int(ophex[1],16)] = i
                    success = True
                    to_remove.append(i)
            for i in to_remove:
                self.keypress_tmp.remove(i)
            if not success:
                self.pc -= 2
        elif re.fullmatch("F.1E", ophex):
            # Fx1E: Add V[x] to I, and set Vf to whether there was an overflow or not
            total = self.I + self.V[int(ophex[1],16)]
            self.I = total % 0x1000
            self.V[15] = total > 0xFFF
        elif re.fullmatch("F.29", ophex):
            # Fx29: Set I to the fontset index of the value of V[x]
            self.I = 0x50 + (len(fontset) // 48) * (
                self.V[int(ophex[1],16)]%16
            )
        elif re.fullmatch("F.30", ophex):
            # Fx30: Set I to the large fontset index of the value of V[x]
            self.I = 0x50 + (len(fontset) // 48) * (16 + 
                self.V[int(ophex[1],16)]%16 * 2
            )
        elif re.fullmatch("F.33", ophex):
            # Fx33: Dump the 3-digit decimal representation of V[x] into
            # memory, starting at I
            dec = str(self.V[int(ophex[1],16)]).zfill(3)
            for i in range(3):
                self.memory[self.I + i] = int(dec[i])
        elif re.fullmatch("F.55", ophex):
            # Fx55: Dump V0..V[x] into memory, starting at I
            for i in range(int(ophex[1],16)+1):
                self.memory[self.I + i] = self.V[i]
            self.I += int(ophex[1],16)+1
        elif re.fullmatch("F.65", ophex):
            # Fx65: Load memory into V0..V[x], starting at I
            for i in range(int(ophex[1],16)+1):
                self.V[i] = self.memory[self.I + i]
            self.I += int(ophex[1],16)+1
        elif ophex == "00FB":
            # 00FB: Scroll the display right 4 pixels
            for row in range(64):
                ind = row*128
                self.gfx[ind:ind+128] = self.gfx[ind:ind+124].rjust(128, b"\x00")
        elif ophex == "00FC":
            # 00FC: Scroll the display left 4 pixels
            for row in range(64):
                ind = row*128
                self.gfx[ind:ind+128] = self.gfx[ind+4:ind+128].ljust(128, b"\x00")
        else:
            raise CHIP8Error(f"Unknown OpCode at {hex(self.pc)}: 0x{ophex}")
        self.pc += 2

        # Update timers
        
        self.delay_timer = max(0, self.delay_timer - (delta * 60))
        self.sound_timer = max(0, self.sound_timer - (delta * 60))

CHIP8 = SCHIP
CHIP8Error = SCHIPError