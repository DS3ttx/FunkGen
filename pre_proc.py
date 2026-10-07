import os
import mido
import math
from collections import defaultdict
import glob

# 1. Configuração do Alfabeto e Mapeamento MIDI
NOTE_MAPPING = {
    36: 'K',  # C1 - Kick
    38: 'S',  # D1 - Caixa / Snare / Clap
    41: 'B',  # F1 - Beatbox grave / Tom
    40: 'P'   # E1 - Prato / Perc / Estalo
}

def quantize_midi_to_sequence(file_path):
    """
    Lê um arquivo MIDI, quantiza para 1/16 e retorna uma lista de símbolos.
    """
    try:
        midi = mido.MidiFile(file_path)
    except Exception as e:
        print(f"Erro ao ler {file_path}: {e}")
        return []

    # O padrão do MIDI: 1 semínima (beat) = ticks_per_beat
    # 1 semicolcheia (1/16) = 1/4 de semínima
    ticks_per_16th = midi.ticks_per_beat / 4
    
    notes = []
    
    # Extrair tempo absoluto e eventos Note On com velocity > 0
    for track in midi.tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                if msg.note in NOTE_MAPPING:
                    notes.append((abs_time, msg.note, msg.velocity))
                    
    if not notes:
        return []

    # Agrupar notas na grade quantizada
    steps = defaultdict(set)
    max_step = 0
    
    for abs_time, note, vel in notes:
        # Arredonda o tempo absoluto para o slot de 1/16 mais próximo
        step = round(abs_time / ticks_per_16th)
        steps[step].add(NOTE_MAPPING[note])
        if step > max_step:
            max_step = step

    # Construir a sequência final com tratamento de silêncio (.)
    sequence = []
    
    # CORREÇÃO MUSICAL: Um compasso 4/4 tem 16 semicolcheias.
    # Precisamos arredondar o tamanho total da música para o múltiplo de 16 mais próximo (fechar os compassos).
    # Isso impede que loops acabem quebrados (ex: length 125 ao invés de 128)
    total_steps = math.ceil((max_step + 1) / 16) * 16
    
    for i in range(total_steps):
        if i in steps:
            # CORREÇÃO DE POLIFONIA: Usar '_' para juntar as notas no mesmo passo de tempo (ex: K_S)
            combined_symbol = "_".join(sorted(list(steps[i])))
            sequence.append(combined_symbol)
        else:
            sequence.append(".")
            
    return sequence

def export_to_aabb(sequences, output_file="funk_bh_beats.aabb"):
    """
    Exporta as sequências para o formato .aabb padrão (usado no FlexFringe/ALERGIA).
    Formato da linha: 1 <tamanho_da_sequencia> <simbolo_1> <simbolo_2> ...
    """
    valid_sequences = [seq for seq in sequences if len(seq) > 0]
    
    # O C++ do FlexFringe exige que os símbolos sejam NÚMEROS INTEIROS (0, 1, 2...). 
    # Letras (como 'K') fazem o parser quebrar. Vamos mapeá-las:
    unique_symbols = set()
    for seq in valid_sequences:
        unique_symbols.update(seq)
        
    unique_symbols = sorted(list(unique_symbols))
    symbol_to_int = {sym: str(i) for i, sym in enumerate(unique_symbols)}
    
    # Salvar o dicionário para você saber qual nota cada número representa!
    with open("symbol_mapping.txt", "w") as map_file:
        for sym, idx in symbol_to_int.items():
            map_file.write(f"{idx} : {sym}\n")
            
    alphabet_size = len(unique_symbols)
    
    with open(output_file, 'w') as f:
        # Cabeçalho Abbadingo exige EXATAMENTE: TOTAL_DE_SEQUENCIAS TAMANHO_DO_ALFABETO
        f.write(f"{len(valid_sequences)} {alphabet_size}\n")
        
        for seq in valid_sequences:
            seq_length = len(seq)
            # Converter a lista de letras para números antes de salvar
            int_seq = [symbol_to_int[sym] for sym in seq]
            symbols_str = " ".join(int_seq)
            f.write(f"1 {seq_length} {symbols_str}\n")

if __name__ == "__main__":
    midi_directory = "./beats"
    midi_files = glob.glob(os.path.join(midi_directory, "*.mid")) + glob.glob(os.path.join(midi_directory, "*.midi"))
    
    all_sequences = []
    
    for midi_file in midi_files:
        print(f"Processando: {os.path.basename(midi_file)}")
        seq = quantize_midi_to_sequence(midi_file)
        if seq:
            all_sequences.append(seq)
            
    if all_sequences:
        output_path = "dataset_funk.aabb"
        export_to_aabb(all_sequences, output_path)
        print(f"\nConcluído! {len(all_sequences)} sequências exportadas para '{output_path}'.")
    else:
        print("\nNenhuma sequência válida foi encontrada. Verifique o mapeamento das notas.")
