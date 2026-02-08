import mido
from mido import MidiFile
from collections import defaultdict


def parse_midi_file(filename:str):
    # 读取MIDI文件
    mid = MidiFile(filename)
    
    # 收集所有事件并合并到全局时间轴
    events = []
    for track in mid.tracks:
        current_time = 0
        for msg in track:
            current_time += msg.time
            events.append((current_time, msg))
    # track = mid.tracks[3]
    # current_time = 0
    # for msg in track:
    #     current_time += msg.time
    #     events.append((current_time, msg))
    
    # 按绝对时间排序事件
    events.sort(key=lambda x: x[0])
    
    # 处理事件，收集音符信息
    active_notes = {}  # 键：(channel, note)，值：开始时间
    notes = []
    
    for current_time, msg in events:
        if msg.type == 'note_on' and msg.velocity > 0:
            key = (msg.channel, msg.note)
            active_notes[key] = current_time
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            key = (msg.channel, msg.note)
            if key in active_notes:
                start_time = active_notes.pop(key)
                duration = current_time - start_time
                notes.append({
                    'pitch': msg.note,
                    'duration': duration,
                    'start_time': start_time
                })
    
    return notes

def group_notes_by_quarter(notes):
    grouped = defaultdict(list)
    
    for note in notes:
        t = note['start_time']
        # 计算四舍五入到最近的二十四分音符位置
        quotient, remainder = divmod(t, 80)
        if remainder >= 40:
            rounded_time = (quotient + 1) * 80
        else:
            rounded_time = quotient * 80
        
        # 计算四分音符位置和开始时间类型
        index = rounded_time // 80
        position = index % 6
        index //= 6
        
        # 添加处理后的音符信息
        grouped[index].append({
            'pitch': note['pitch'],
            'duration': note['duration'],
            'position': position
        })
    
    # 创建连续的结果列表
    max_index = max(grouped.keys()) if grouped else -1
    if max_index == -1:
        return []
    
    return [grouped.get(i, []) for i in range(max_index + 1)]

# 使用示例
if __name__ == "__main__":
    midi_notes = parse_midi_file("空気力学少女と少年の詩 -Piano Ver.-.mid")  # 替换为你的MIDI文件路径
    quarter_note_list = group_notes_by_quarter(midi_notes)
    
    # 打印结果示例
    for i, quarter in enumerate(quarter_note_list):
        print(f"Quarter {i}:")
        for note in quarter:
            print(f"  Pitch: {note['pitch']}, Duration: {note['duration']}, Position: {note['position']}")
