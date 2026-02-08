import dsMIDI, os, json
from collections import Counter

os.chdir(r'C:\Users\Admin\Desktop\midi')
# 音高映射配置
BLOCKS = {'LONG': (
    "minecraft:oak_planks",    # 木头
    "minecraft:sand",          # 沙子
    "minecraft:dirt",          # 泥土
    "minecraft:glass",         # 玻璃
    "minecraft:stone"          # 石头
    ), 'SHORT': (
    "minecraft:white_wool",    # 羊毛
    "minecraft:clay",          # 黏土
    "minecraft:gold_block",    # 金块
    "minecraft:packed_ice",    # 浮冰
    "minecraft:bone_block"     # 骨块
)}

DIRECTIONS = {
    (1, 0): 'east',
    (-1, 0): 'west',
    (0, 1): 'south',
    (0, -1):'north'
}
DIRECTIONS2 = {
    (-1, 0): 'east',
    (1, 0): 'west',
    (0, -1): 'south',
    (0, 1):'north'
} #红石中继器的朝向与指向方向相反

BASE_NOTE = 54 # F♯3

def getBlock(pitch:int, dur:int):
    i0 = 'SHORT' if dur<720 else 'LONG'
    i1 = 2 + (pitch-BASE_NOTE)//12
    if i1==5: i1=4
    return BLOCKS[i0][i1]

def getNote(pitch:int):
    result = (pitch-BASE_NOTE)%12
    if (pitch-BASE_NOTE)//12==3:
        result += 12
    return result

def turn(cur:tuple[int,int], dir:str):
    seq = ((1,0),(0,-1),(-1,0),(0,1)) # 东北西南 逆时针
    if dir == 'left':
        return seq[(seq.index(cur)+1)%4]
    elif dir == 'right':
        return seq[seq.index(cur)-1]
    else:
        raise TypeError('dir could only be left or right')

def getCmdGroup(startPos:tuple[int, int], facing:tuple[int, int], notes:list[str,int], placed:list[bool]=[False,False], lastPlaced:list[bool]=[False,False], delay:int=4):
    curPlaced = placed
    lPlaced = lastPlaced
    commands = []
    x, z = startPos
    # 音符前连接中继器
    commands.append((f'setblock ~{x} ~ ~{z} minecraft:stone', (x,z)))
    commands.append((f'setblock ~{x} ~1 ~{z} minecraft:repeater[delay={delay},facing={DIRECTIONS2[facing]}]', (x,z)))
    x += facing[0]; z += facing[1]
    if not notes: # 空音符填充红石粉，直接return
        commands.append((f'setblock ~{x} ~ ~{z} minecraft:stone', (x,z)))
        commands.append((f'setblock ~{x} ~1 ~{z} minecraft:redstone_wire', (x,z)))
        return commands, curPlaced
    flag = False
    extra = None
    for i in range(len(notes)):
        if flag: # 当前音节非第一个方块
            if False in curPlaced: # 如果当前音节有剩余空间
                j = curPlaced.index(False)
                changePos = turn(facing, ['left','right'][j])
                bx, bz = x+changePos[0], z+changePos[1] # 计算可放置坐标
                curPlaced[j] = True
            elif False in lPlaced: # 没有剩余空间，借用上一个音节空间
                lastPos = [startPos[j]-facing[j] for j in range(2)]
                newFacing = turn(facing, ['left','right'][lPlaced.index(False)]) # 查询上一个音节剩余空间左右位置 计算转向后行进方向
                newStart = [lastPos[j]+newFacing[j] for j in range(2)]
                # print(notes, i)
                commands += getCmdGroup(newStart, newFacing, notes[i:], [False,False], [True,True], delay)[0] # 转换后递归调用
                break
            else: # 上一个音符空间不足，抛出报错
                # raise TypeError('Pos', (x,z), 'notes too much.', notes[i], 'failed to place.')
                newFacing = turn(facing, 'right')
                if extra==None:
                    extra = [j*8 for j in newFacing]
                bx, bz = x+newFacing[0]+extra[0], z+newFacing[1]+extra[1]
                extra[0]+=newFacing[0]; extra[1]+=newFacing[1]
                print('Pos', (x,z), 'notes too much.', notes[i:], 'failed to place.')
                # print(curPlaced)
        else: # 当前音节第一个方块，直接放在正中间
            bx, bz = x, z
            flag = True
        commands.append((f'setblock ~{bx} ~ ~{bz} {notes[i][0]}', (bx,bz)))
        commands.append((f'setblock ~{bx} ~1 ~{bz} minecraft:note_block[note={notes[i][1]}]', (bx,bz)))
    return commands, curPlaced
    

def genCmds(blockList, facing:tuple[int, int]):
    commands = []
    x, z = facing # 主音轨，偶数时刻
    subDir = turn(facing, 'left') # 副音轨平移，奇数时刻，距离5
    lastPlaced = [[False]*2 for i in range(2)] # 前一格左右占用情况
    delay = 1
    for quarter in blockList:
        # x += facing[0]*2; z += facing[1]*2
        # 音符
        curUsed = [False]*2 #该格占用情况
        noteNums = Counter((i[2] for i in quarter))
        for i in range(3):
            if i*2 in noteNums or i*2+1 in noteNums:
                newCmd, lastPlaced[0] = getCmdGroup((x, z), facing, [q for q in quarter if q[2]==i*2], [False]*2, lastPlaced[0], delay)
                commands += newCmd
                newCmd, lastPlaced[1] = getCmdGroup((x+subDir[0]*4, z+subDir[1]*4), facing, [q for q in quarter if q[2]==i*2+1], [False]*2, lastPlaced[1], delay)
                commands += newCmd
                delay = 1
                x += facing[0]*2; z += facing[1]*2
            else:
                delay += 1
                if delay == 5:
                    commands.append((f'setblock ~{x} ~ ~{z} minecraft:stone', (x,z)))
                    commands.append((f'setblock ~{x} ~1 ~{z} minecraft:repeater[delay=4,facing={DIRECTIONS2[facing]}]', (x,z)))
                    commands.append((f'setblock ~{x+subDir[0]*4} ~ ~{z+subDir[1]*4} minecraft:stone', (x+subDir[0]*4, z+subDir[1]*4)))
                    commands.append((f'setblock ~{x+subDir[0]*4} ~1 ~{z+subDir[1]*4} minecraft:repeater[delay=4,facing={DIRECTIONS2[facing]}]', (x+subDir[0]*4, z+subDir[1]*4)))
                    x += facing[0]; z += facing[1]
                    commands.append((f'setblock ~{x} ~ ~{z} minecraft:stone', (x,z)))
                    commands.append((f'setblock ~{x} ~1 ~{z} minecraft:redstone_wire', (x,z)))
                    commands.append((f'setblock ~{x+subDir[0]*4} ~ ~{z+subDir[1]*4} minecraft:stone', (x+subDir[0]*4, z+subDir[1]*4)))
                    commands.append((f'setblock ~{x+subDir[0]*4} ~1 ~{z+subDir[1]*4} minecraft:redstone_wire', (x+subDir[0]*4, z+subDir[1]*4)))
                    lastPlaced = [[False]*2 for i in range(2)]
                    x += facing[0]; z += facing[1]
                    delay = 1
    return commands


if __name__ == '__main__':
    allNotes = dsMIDI.parse_midi_file("空気力学少女と少年の詩 -Piano Ver.-.mid")
    qList = dsMIDI.group_notes_by_quarter(allNotes)
    # with open('夢の歩みを見上げて.json', 'w', encoding='utf-8') as fb:
    #     json.dump(qList, fb, indent=2)
    blockL = []
    for i in qList:
        n = [(getBlock(j['pitch'], j['duration']), getNote(j['pitch']), j['position']) for j in i]
        blockL.append(sorted(n, key=lambda x: x[2]))
    cmds = genCmds(blockL, (1, 0))
    count = Counter((i[1] for i in cmds))
    print([[i, count[i]] for i in count.keys() if count[i]>2])
    a = [i for i in count.keys() if count[i]>2]
    with open('kuuki_rikigaku.mcfunction', 'w', encoding='utf-8') as fb:
        for i in cmds:
            fb.write(i[0]+'\n')
            if i[1] in a:
                fb.write('# Repeated '+str(count[i[1]]//2)+'\n')
                fb.write(f'setblock ~{i[1][0]} ~2 ~{i[1][1]} stone\n')
    # print(cmds)
    # print(blockL)
