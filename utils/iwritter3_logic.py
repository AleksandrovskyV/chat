import re, time, random
import subprocess
import keyboard

import itertools
import pyperclip
import os,json, csv
import logging
import uuid

## SEQUENCE TYPING

# Разделение raw_text на блоки, где в качестве разделителя является пустая строчка 
# Последующая печать текста в случайной последовательности, а по завершению печати всех блоков - возврат к исходному состоянию
# Тестировалось в NOTEPAD / SUBLIME | аккуратнее во время процесса печати, при переключении активного окна возможны казусы

# В доработке - сложные блоки + более адекватное деление с несколькими пробелами (пока только заранее подготовленный текст)

## VARIABLES

MODE = "NOTEPAD" # OR SUBLIME

# debug : states 0 - disable / 1 - allperms / 2 - action info / 3 - deep info
# debug mode : match / mismatch  / all
DEBUG_STATE = 0
debug_const = 0  # Выбор итерации (при нуле - цикл по всем возможным)
debug_mode = "all" 

# Для диапазона запуска: указываем оба (min-max)
debug_use_range = False 
debug_const_min = 13
debug_const_max = 24

# Базовый путь до файла логов (без расширения)
debug_file_fold = "logs"
debug_file_mode = "notepad_" if MODE == "NOTEPAD" else "sublime_" if MODE == "SUBLIME" else ""
debug_file_base = f"{debug_file_fold}/debug_{debug_file_mode}output"
debug_file_ext = ".txt"  # .txt | .json | .csv

def get_unique_debug_file(base, ext):
    path = base + ext
    if os.path.exists(path):
        unique_id = uuid.uuid4().hex[:6]
        path = f"{base}_{unique_id}{ext}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def activate_logging():

    debug_file = get_unique_debug_file(debug_file_base, debug_file_ext)

    logging.basicConfig(
        level=logging.DEBUG if DEBUG_STATE else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(debug_file, mode='a', encoding='utf-8')
        ]
    )

# special prints

def aprint(*args, **kwargs):
    if DEBUG_STATE == 2:
        print(*args, **kwargs)

def dprint(*args, **kwargs):
    if DEBUG_STATE == 3:
        print(*args, **kwargs)



# Подготовка блоков и метаинформации

def raw_text_to_blocks(raw_text):
    parts = re.split(r"\n\s*\n", raw_text.strip())
    blocks = [p for p in parts if p.strip()]
    all_lines = raw_text.strip().splitlines()
    blank_counts = []
    cursor = 0
    for block in blocks:
        lines = block.splitlines()
        cursor += len(lines)
        count = 0
        while cursor < len(all_lines) and all_lines[cursor].strip() == '':
            count += 1
            cursor += 1
        blank_counts.append(count)
    return blocks, blank_counts

def determine_text_data_type(block):
    return 1 if re.search(r"[=(){}\[\]]", block) else 0

def randomize_blocks(blocks):
    """
    Возвращает список индексов в случайном порядке, где
    последний индекс всегда остаётся неизменным (назначается в конец).
    
    :param blocks: список любых элементов
    :return: список индексов от 0 до len(blocks)-1,
             перемешанных за исключением последнего, который остаётся в конце
    """
    n = len(blocks)
    if n <= 1:
        # Если блоков 0 или 1, возвращаем их как есть
        return list(range(n))
    
    # Все индексы, кроме последнего
    indices = list(range(n - 1))
    random.shuffle(indices)
    
    # Добавляем последний индекс в конец
    indices.append(n - 1)
    return indices

def blocks_meta(blocks, blank_counts):
    meta_by_index = {}
    for idx, block in enumerate(blocks):
        lines_count = len([l for l in block.splitlines() if l.strip()])
        text_type = determine_text_data_type(block)
        blank_after = blank_counts[idx]
        meta_by_index[idx] = (text_type, lines_count, blank_after)
    return meta_by_index



# Модуль печати

TYPE_SPEED = 0.04
ACTION_SPEED = 0.22

#TYPE_SPEED = 0.2 # 0.005
#ACTION_SPEED = 0.13 # 0.05

if debug_const==0 and DEBUG_STATE==1:
    # ускорения, чтобы быстрее дебажить
    TYPE_SPEED=0.001
    ACTION_SPEED = 0.01

def block_typing(block, block_index, text_type):

    if MODE == "NOTEPAD":      
        keyboard.write(block, delay=TYPE_SPEED)
        if DEBUG_STATE == 0:
            print(f"[+] Block {block_index} complete")

    elif MODE == "SUBLIME":   
        if text_type==1:
            lines = block.split('\n')
            for line_index, line in enumerate(lines):
                keyboard.write(line, delay=TYPE_SPEED)
                time.sleep(ACTION_SPEED)
                sublime_cor()
            time.sleep(ACTION_SPEED/2)
            sublime_remove_trash()
            time.sleep(ACTION_SPEED/2)
            keyboard.press_and_release('backspace')
            keyboard.press_and_release('backspace')
            time.sleep(ACTION_SPEED/2)

        else:
            keyboard.write(block, delay=TYPE_SPEED)

        if DEBUG_STATE == 0:
            print(f"[+] Block {block_index} complete")



    return True


# Действия

# SUBLIME NOTES
# PAGE DOWN > В КОНЕЦ
# 2x HOME -  перемещение между табуляцией и и началом строки
# Новая строка ENTER+HOME

def action_empty():
    # пустая заготовка
    time.sleep(ACTION_SPEED)


def sublime_cor():
    time.sleep(ACTION_SPEED)
    keyboard.press_and_release('enter')
    time.sleep(ACTION_SPEED)
    #keyboard.press_and_release('delete')
    #keyboard.press_and_release('delete')
    keyboard.press_and_release('ctrl+l')
    keyboard.press_and_release('shift+left')
    keyboard.press_and_release('delete')
    #keyboard.press_and_release('home')

def sublime_remove_trash():
    time.sleep(ACTION_SPEED*4)
    keyboard.press_and_release('ctrl+l')
    time.sleep(ACTION_SPEED*4)
    #keyboard.press_and_release('shift+left')
    time.sleep(ACTION_SPEED*4)
    keyboard.press_and_release('delete')
    keyboard.press_and_release('enter')

    print("SUBLIME_TRASH_CLEAN")


def action_refresh():
    # перенос указателя к началу строки
    time.sleep(ACTION_SPEED)
    if MODE=="NOTEPAD":       
        keyboard.press_and_release('home')
    if MODE=="SUBLIME":       
        keyboard.press_and_release('home')
        keyboard.press_and_release('home')

def action_end_line():
     # главная цель экшена - создание новой строки

    time.sleep(ACTION_SPEED)
    if MODE=="NOTEPAD":      
        keyboard.press_and_release('enter')
        #dprint(f"[ACTION] ADD SHIFT IN END")
    if MODE=="SUBLIME":      
        keyboard.press_and_release('enter')
        time.sleep(ACTION_SPEED/2)
        keyboard.press_and_release('home')
        #dprint("SUBLIME_TEST")
    
    time.sleep(ACTION_SPEED)

def action_next_line():
    
     # цель экшена спуск на сдедующую строчку, после печати
    time.sleep(ACTION_SPEED)
    keyboard.press_and_release('right')
    dprint(f"[ACTION] next_line")
    time.sleep(ACTION_SPEED)

def action_add_empty_line(n):
    
    # добавление пустых строк (спуски после блоков)

    time.sleep(ACTION_SPEED)
    if n > 0: # проверка на всякий
        for _ in range(n):
            time.sleep(ACTION_SPEED)
            if MODE=="NOTEPAD":      
                keyboard.press_and_release('enter')
            if MODE=="SUBLIME":      
                keyboard.press_and_release('enter')
                #dprint("SUBLIME_TEST")
                time.sleep(ACTION_SPEED/2)
                keyboard.press_and_release('home')


    dprint(f"[ACTION] ADD EMPTY = {n} ")
    time.sleep(ACTION_SPEED)

def action_clean():
    # Освобождение места, перед набором
    time.sleep(ACTION_SPEED)
    keyboard.press_and_release('enter')
    keyboard.press_and_release('enter')
    keyboard.press_and_release('up')
    dprint(f"[ACTION] CLEAN LINE")

def action_clean_up(flag):
    # Освобождение места после перемещения?

    time.sleep(ACTION_SPEED*2)    
    keyboard.press_and_release('enter')
    time.sleep(ACTION_SPEED*2)
    keyboard.press_and_release('enter')

    time.sleep(ACTION_SPEED*2)
    keyboard.press_and_release('up')
    
    pr = 1

    if flag==1:
        # только для первого (у него нет спуска)
        pr += 1
        keyboard.press_and_release('up')

    time.sleep(ACTION_SPEED)
    dprint(f"[ACTION][CLEAN SPACE][actionflag:{flag}] UP ={pr}")

def action_JumpDown(n):
    # Перемещение наверх
    pr = 0
    for _ in range(n):
        time.sleep(ACTION_SPEED)
        keyboard.press_and_release('down')
        pr +=1
    dprint(f"[ACTION] down {pr}")   

def action_JumpUp(n):
    # перемещение вниз
    pr = 0
    time.sleep(ACTION_SPEED)
    for _ in range(n):
        time.sleep(ACTION_SPEED)
        keyboard.press_and_release('up')
        pr +=1

    dprint(f"[ACTION][JUMP_UP] ={pr}")

def action_JumpEnd():
    # Прыжок в самый конец
    time.sleep(ACTION_SPEED)
    keyboard.press_and_release('ctrl+end')
    dprint(f"[ACTION] JUMP_END")

def action_CopyBuffer():
    # Последовательность для копирования в буффер обмена (для дебага)
    time.sleep(ACTION_SPEED)
    keyboard.press_and_release('ctrl+a')
    keyboard.press_and_release('ctrl+c')
    keyboard.press_and_release('ctrl+end')
    print(f"[ACTION] COPY BUFFER")

def action_delete_all():
    # удаление всего текста после печати \ в основном для дебага

    time.sleep(ACTION_SPEED)

    keyboard.press_and_release('ctrl+a')

    time.sleep(ACTION_SPEED*2)

    keyboard.press_and_release('delete')
    
    dprint(f"[ACTION] DELETE ALL")

def action_backspace():
    # Удаление
    time.sleep(ACTION_SPEED)
    keyboard.press_and_release('backspace')
    dprint(f"[ACTION][CLEAN SPACE] down+backspace")

def action_clean_end():
    # удаление лишнего спуска, после завершения всей печати
    time.sleep(ACTION_SPEED)
    keyboard.press_and_release('down')
    time.sleep(ACTION_SPEED)
    keyboard.press_and_release('backspace')
    dprint(f"[ACTION] CLEAN ONE LINE")


### BASIC COMMENT 
### ПРОЩЕ РАБОТАТЬ С ЦЕЛЫМ ПАКЕТОМ ИЗ ПУСТЫХ СТРОК И ТЕКСТОМ, НО РАЗ УЖ РЕШИЛ ДЕЛАТЬ ВКЛ СПУСКИ:
### ПОСЛЕ КАЖДОГО СООБЩЕНИЯ ДОЛЖЕН СТАВИТЬСЯ СПУСК (1 ШТ)
### ПРИ ПЕЧАТИ СЛЕДУЮЩИМ - (ДЕЛАТЬ + 1 СПУСК) И ПЕЧАТАТЬ СЛЕД 
### ПРИ ПОДЪЕМЕ НАВЕРХ ЧЕРЕЗ БЛОКИ, НУЖНО ВЫЧИТАЕТ ЕГО (КОЛ-ВО ЗАПОЛНЕННЫХ БЛОКОВ + ТЕКУЩИЙ - 1 ) ЧТОБЫ СКОРЕРКТИРОВАТЬ СПУСК
### ПРИ СПУСКЕ ВНИЗ ЧЕРЕЗ БЛОКИ, НУЖНО ВЫСЧИТАТЬ (КОЛ-ВО ЗАПОЛНЕННЫХ БЛОКОВ (СТРОКИ+ПУСТЫЕ) + ENTER+UP


# Модуль для переходов и запуска действий (ядро)
def blocks_control_module(blocks, meta_by_index, sequence):

    complete_blocks = []
    process_order = []
    last_index = None
    max_index = max(sequence)

    current_first = sequence[0]
    current_last = 1
    flag_complete = 0


    for current_index in sequence:
        block = blocks[current_index]
        text_type, lines_count, blank_after = meta_by_index[current_index]

        dprint(f"[INFO] >>> Переход к блоку {current_index}")
        dprint(f"[INFO][TEXT]: '{block[:24]}...'")
        dprint(f"[INFO][META]: Lines ={lines_count}, NumberBlankLines ={blank_after}")

        if last_index is None:
            dprint("[DEBUG_STATE][FIRST_WRITE]")

            block_typing(block, current_index,text_type)
            
            complete_blocks.append(current_index)
            process_order.append(current_index)
            if blank_after > 0:
                action_end_line()
            elif current_index==max_index:
                action_end_line()
            else:
                pass

            last_index = current_index
            continue

        diff = current_index-last_index

        # пустой список индексов уже напечатанных блоков (сброс перед вхождением в цикл)
        between_blocks_ids = []
        scan_range = []

        endflag = 0
        hard_move_flag = 0

        if all(current_index > process for process in complete_blocks):
            current_last = current_index
            endflag = 1
            #dprint(f"[DEBUG_STATE] {current_index} — новый последний печатаемый блок.")
       
        # Определяем границы диапазона между last_index и current_index
        if diff > 0:
            scan_range = range(last_index + 1, current_index) #?
        else:
            scan_range = range(current_index + 1, last_index) #?


        for temp_comp_id in scan_range: # Проход в промежутке
            # Нахиодим есть ли между текущим и прошлым уже напечатанные блоки
            if temp_comp_id in complete_blocks:
                 # Список id уже напечатанных блоков в промежутке между текущим и последним
                between_blocks_ids.append(temp_comp_id)
                    

        if diff == 1:  # Печать блока стоящего сразу после текущего напечатанного

            dprint("[DEBUG_STATE][NEXT BLOCK]")
            before_ind = current_index-1
            action_end_line()
            if before_ind in complete_blocks:
                pass

            flag_post = 0
            if any(i > current_index for i in complete_blocks):
                flag_post = 1


            block_typing(block, current_index,text_type)

            if flag_post==1 and MODE=="SUBLIME" and text_type==1:
                keyboard.press_and_release('enter')
                keyboard.press_and_release('left')

        elif diff > 0: #Печать блока с переносом указателя вниз через уже напечатанные блоки                # DOWN
            #dprint("DIFF>0")    
            hard_move_flag = 0
            link_meta = meta_by_index[last_index]
            n_comp = 0 # сброс перед вхождением в цикл
            #dprint(f"LAST INDEX ={last_index}")

            for comp_id in between_blocks_ids:
                # получаем кортеж метаданных именно этого блока
                n_comp_link = meta_by_index[comp_id]
                n_comp_lines = n_comp_link[1] # кол-во строк
                n_comp_spusk = n_comp_link[2] # кол-во спусков
                #dprint(f"[N_COMP][L] = {n_comp_lines}, [S] = {n_comp_spusk}")
                n_comp += n_comp_lines + n_comp_spusk


            if not between_blocks_ids:
                # отсутствие напечатанных блоков между ними

                hard_move_flag = 0
                n = ( link_meta[1] + link_meta[2] ) + 1 
                dprint(f"[DEBUG_STATE][SIMPLE DOWN] BlankLine = {n}")
            else:
                # подсчет строк перехода: у только что напечатанного блока, что спуститься вниз
                hard_move_flag = 1
                n = n_comp+1 #подсчёт завершённых
                dprint(f"[DEBUG_STATE][MOVE DOWN] between_blocks = {between_blocks_ids}, MOVE COUNT ={n}")
            

            #
            # доп действия перед набором 
            # необходимы, чтобы освободить место, и печатать с свободной строкой
            flag_post = 0
            if any(i > current_index for i in complete_blocks):
                flag_post = 1

            if hard_move_flag==1:
                action_JumpDown(n) 
                if any(i > current_index for i in complete_blocks):
                    action_clean()


            else:
                if endflag==0: # last pravkas 20
                    action_next_line()
                    action_clean()
                pass
  

            if endflag==1:
                dprint("[DEBUG_STATE][END FLAG]")
                action_clean()
                pass

            #набор
            
            time.sleep(ACTION_SPEED)

            block_typing(block, current_index,text_type)

            if flag_post==1 and MODE=="SUBLIME" and text_type==1:
                keyboard.press_and_release('enter')
                keyboard.press_and_release('left')
            
            time.sleep(ACTION_SPEED)


        elif diff < 0: # Печать блока с переносом указателя наверх через уже напечатанные блоки            # UP

            link_meta = meta_by_index[last_index]
            n_comp = 0 # сброс перед вхождением в цикл
            hard_move_flag = 0
            #print(f"LAST INDEX ={last_index}")
            
            for comp_id in between_blocks_ids:
                # получаем кортеж метаданных именно этого блока
                n_comp_test = []
                n_comp_link = meta_by_index[comp_id]
                n_comp_lines = n_comp_link[1] # кол-во строк
                n_comp_spusk = n_comp_link[2] # кол-во спусков
                #dprint(f"[N_COMP][L] = {n_comp_lines}, [S] = {n_comp_spusk}")
                n_comp += n_comp_lines + n_comp_spusk
                


            if not between_blocks_ids:
                hard_move_flag = 0
                
                # отсутствие напечатанных блоков между ними
                plus = 0

                if last_index==max_index:
                    plus = 1 

                n = ( link_meta[1] + link_meta[2] ) + plus    # подъем только на себя 

                dprint(f"[DEBUG_STATE][SIMPLE UP] BlankLine = {n}")
                dprint(f"[LINES] = {link_meta[1]}, SPUSK = {link_meta[2]}")

            else:
                hard_move_flag = 1
                plus = 0

                if last_index==max_index:
                    plus = 1 

                # подсчет строк перехода: у только что напечатанного блока + строчки уже напечатанных (между ними), чтобы подняться наверх
                n = ( ( link_meta[1] + link_meta[2] ) + (n_comp) ) + plus
                dprint(f"[DEBUG_STATE][MOVE UP] between_blocks = {between_blocks_ids}, MOVE COUNT ={n}")
                dprint(f"[DEBUG_STATE][MOVE UP] SELF = {link_meta[1]}, {link_meta[2]}")


            action_refresh()
            action_JumpUp(n)

            # доп действия перед набором 
            # необходимы, чтобы освободить место, и печатать с свободной строкой

            flag_post = 0
            
            if any(i > current_index for i in complete_blocks):
                flag_post = 1

            startflag = 0

            if current_index < current_first:
                current_first = current_index
                startflag = 1
                dprint("[DEBUG_STATE][NEW FIRST BLOCK]")

            action_refresh()
            if hard_move_flag ==1:
                action_clean_up(startflag)
            else:
                action_clean_up(startflag)

            #набор

            time.sleep(ACTION_SPEED)

            block_typing(block, current_index,text_type)


            if flag_post==1 and MODE=="SUBLIME" and text_type==1:
                keyboard.press_and_release('enter')
                keyboard.press_and_release('left')


            time.sleep(ACTION_SPEED)

        else:
            pass



        complete_blocks.append(current_index)
        process_order.append(current_index)

        # ставить спуск после каждого блока, если печатается следующий 
        # исключение, если следующий индекс уже есть в списке напечатанных

        if blank_after > 0: # кол-во пустых строк "после" блока 

            cur_id = sequence.index(current_index)

            if cur_id + 1 < len(sequence):  # Предотвращаем выход за границы
                next_index = sequence[cur_id + 1]
                after_index = current_index + 1
                past_index = current_index - 1
                last_in_sequence = sequence[-1]

                if current_index != last_in_sequence:  # Если current_index - не последний элемент в списке печати
                    if next_index not in complete_blocks:
                        if next_index > current_index:
                            if after_index not in complete_blocks:
                                if next_index != after_index:
                                    if endflag ==1:
                                        action_add_empty_line(blank_after)
                                        aprint(f"[POST ACTION INFO][A] {blank_after}")
                                    else:
                                        action_empty()
                                        aprint("[POST ACTION INFO][B]")
                                    pass
                                else:
                                    action_add_empty_line(blank_after)
                                    aprint("[POST ACTION INFO][C]")
                            else:
                                action_empty()
                                aprint("[POST ACTION INFO][D]")
                                pass
                        else:
                            if not any(i >= after_index for i in complete_blocks):
                                action_add_empty_line(blank_after)
                                aprint("[POST ACTION INFO][E]")
                            else:
                                #action_empty()
                                action_next_line()
                                aprint("[POST ACTION INFO][F]")
                else:
                    if current_index == last_in_sequence:     
                        action_end_line()
                        aprint("[POST ACTION INFO][G]")
                    else:
                        aprint("[POST ACTION INFO][H]")
                        pass
            else:
                if current_index != max_index:
                    if current_index == sequence[-1]:
                        pass

                    if hard_move_flag==1:
                        pass
                    else:
                        pass
                    aprint("[POST ACTION INFO][I]")
                else:
                    aprint("[POST ACTION INFO][J]")
                    pass
        else:
            action_end_line()
            aprint("[POST ACTION INFO][K]")


        last_index = current_index

    dprint("[INFO][BLOCK COMPLETE]")

    if current_index == sequence[-1]:
        dprint("[INFO][ALL_PRINTED]")
        flag_complete=1
        action_JumpEnd()
        time.sleep(1) 
        action_backspace()
        time.sleep(.2) 
        action_CopyBuffer()
        return flag_complete

def write_debug_entry(path, sequence_id, sequence, status):
    if DEBUG_STATE == 0:
        return  # не писать при DEBUG_STATE=0

    if debug_mode == "mismatch" and status != "mismatch":
        return  # не писать match в режиме mismatch

    _, ext = os.path.splitext(path)
    ext = ext.lower()
    line = f"{sequence_id}_[{','.join(map(str, sequence))}]_{status}"

    if ext == ".json":
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []
        data.append({
            "sequence_id": sequence_id,
            "sequence": sequence,
            "status": status
        })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    elif ext in (".txt", ".log"):
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    elif ext == ".csv":
        write_header = not os.path.exists(path)
        with open(path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["sequence_id", "sequence", "status"])
            writer.writerow([sequence_id, ",".join(map(str, sequence)), status])
    else:
        raise ValueError(f"Unsupported debug file format: {ext}")

def prepare_sequences(blocks, manual_sequence):
    if DEBUG_STATE == 0:
        return [manual_sequence]  # только один раз

    all_perms = list(itertools.permutations(range(len(blocks))))
    all_sequences = [manual_sequence] + [list(p) for p in all_perms if list(p) != manual_sequence]

    total = len(all_sequences)

    if debug_const > 0:
        if not (1 <= debug_const <= total):
            raise ValueError(f"debug_const={debug_const} out of range 0..{total}")
        return [all_sequences[debug_const]]

    if debug_const == 0 and debug_use_range:
        print(f"[DEBUG_STATE RANGE ACTIVE] MIN: {debug_const_min}, MAX: {debug_const_max} ")
        min_valid = 0 <= debug_const_min < total
        max_valid = 0 <= debug_const_max < total
        if min_valid and max_valid and debug_const_min <= debug_const_max:
            return all_sequences[debug_const_min : debug_const_max ]

    return all_sequences





def iWritter_PrepareText(debug=0): 
    global DEBUG_STATE

    if debug==1:
        DEBUG_STATE=1

    raw_text = pyperclip.paste()  # ← получаем текст
    raw_clean = raw_text.replace('\r\n', '\n').replace('\r', '\n').strip()


    total_lines = len(raw_clean.splitlines())
    blocks, blank_counts = raw_text_to_blocks(raw_clean)
    meta = blocks_meta(blocks, blank_counts)   

    print("\n[TOTAL_LINES]", total_lines)
    print("[BLOCK META]", meta,"\n\n")
    print("[RAW_CLEAN]", raw_clean,"\n") 

    return blocks


def main():
# если добавлять табуляцию - может не работать
    raw_text = """
я высох я похож на мумию
гнию как выпившая рыба
хандрить? и даже не подумаю

а = Analysis(
    ['main.py'],
    runtime_hooks=[],
    excludes=[
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.QtDataVisualization',
    ],
    noarchive=False,
)

спасибо жизнь за то что дадена
спасибо и друзья и вороги

спасибо тыщу раз и более

мне вырезали страх как грыжу
и вновь когда-нибудь увижу
    """

    raw_clean = raw_text.replace('\r\n', '\n').replace('\r', '\n').strip()
    total_lines = len(raw_text.splitlines())
    blocks, blank_counts = raw_text_to_blocks(raw_text)
    meta = blocks_meta(blocks, blank_counts)

    manual_sequence = [0, 1, 2, 3, 4]
    sequences = prepare_sequences(blocks, manual_sequence)
    
    if MODE == "NOTEPAD":
        subprocess.Popen(['notepad.exe'])
    elif MODE == "SUBLIME":
        subprocess.Popen([r"C:\Program Files\Sublime Text\sublime_text.exe"])
    else:
        print(f"[WARNING][SELECT MODE]")
        return

    if DEBUG_STATE>0:
        print(f"[INIT][DEBUG_STATE_MODE][APP: {MODE}]")
        print("[EXIT] HOLD [ESC]")
    else:
        print("[INIT][MANUAL_MODE]")
    
    print("\n[TOTAL_LINES]", total_lines)
    print("[MANUAL SEQUENCE]", manual_sequence)
    print("[BLOCK META]", meta,"\n")

    activate_logging()

    time.sleep(1.5)

    if debug_const !=0:
        startid = debug_const
    else:
        if debug_use_range==True:
            startid = debug_const_min
        else:
            startid = 0

    # 3. Итерация по последовательностям и вызов вашей логики управления курсором
    for idx, seq in enumerate(sequences, start=0):
        if keyboard.is_pressed('esc'):
            print("[INFO] ESC нажата — выходим из цикла.")
            break
        try:
            currendID = startid+idx

            # Здесь вызываем вашу функцию управления печатью:
            print(f"\n[START PRINTING][{currendID}]: {seq}")
            time.sleep(.5)

            result = blocks_control_module(blocks, meta, seq)

            if result == 1:
                
                time.sleep(.5)
                buffer_clean = pyperclip.paste().replace('\r\n', '\n').replace('\r', '\n').strip()

                if buffer_clean == raw_clean:
                    print("[MATCH]    Результат совпадает с raw.")
                    status = "match"
                else:
                    print("[MISMATCH] Результат не совпадает с raw.")
                    status = "mismatch"

                time.sleep(.2)
                #logging.debug(f"#{currendID}: {seq} -> {status}")
                time.sleep(.2)

                if DEBUG_STATE > 0:
                    if debug_mode == "all" and debug_const == 0:
                        print(f"[INFO] Печать завершена! ПЕРЕЗАПУСК ...")
                        write_debug_entry(debug_file, currendID, seq, status)
                        action_delete_all() # удаляем, чтобы освободить место, под следующую итерацию 
                    elif debug_mode == "mismatch" and debug_const == 0:
                        #запись debug файла с результатами mismatch
                        pass
                    elif debug_mode == "mismatch" and debug_const > 0:
                        #запись debug файла только с текущим результатом
                        pass
                    else:
                        # debug_const > 0 - значит выбран конкретный - не удаляем после печати
                        print(f"[INFO] Печать завершена! ...")

                time.sleep(1)

        except Exception as e:
            logging.error(f"Error at sequence {idx}: {e}")

if __name__ == "__main__":
    #main()
    pass


