import json
import os.path
import random

import mido
import argparse

from collections import defaultdict

SILENCE = "."

STEPS_PER_BAR = 16

TEXT_TO_MIDI = {
    'K': 36,
    'S': 38,
    'B': 41,
    'P': 40
}


def read_symbol_mapping(filename: str) -> dict:
    mapping = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            idx, sym = line.split(" : ", 1)
            mapping[idx] = sym
    return mapping


def read_model(filename: str) -> dict:
    graph = defaultdict(list)
    model: dict | None = None

    with open(filename, 'r') as f:
        model = json.load(f)

    if not model:
        raise Exception("Erro ao abrir o arquivo do modelo.")

    weights = {}
    for node in model["nodes"]:
        id = str(node["id"])
        weights[id] = node['data']['trans_counts']

    for edge in model["edges"]:
        source = edge["source"]
        target = edge["target"]
        symbol = edge["name"]

        weight = weights[source].get(symbol, "0")
        weight = int(weight)

        if weight > 0:
            graph[source].append({
                "target": target,
                "symbol": symbol,
                "weight": weight
            })

    return graph


def calculate_dynamic_chaos(base_chaos: float, chosen_weight: int, max_weight: int) -> float:
    if max_weight == 0:
        return base_chaos
        
    rarity_factor = chosen_weight / max_weight
    return (base_chaos * 0.3) + (base_chaos * 0.7 * rarity_factor)


def generate(model: dict, symbol_mapping: dict, base_chaos: float):
    actual_state = "-1" # Default root state by FlexFringe
    beat = []

    current_chaos = base_chaos

    for step in range(128):
        if step > 0 and step % STEPS_PER_BAR == 0:
            actual_state = "-1"

        options = model.get(actual_state, [])

        # Dead-end
        if len(options) == 0:
            actual_state = "-1"
            options = model.get(actual_state, [])

            if len(options) == 0:
                break

        transitions = []
        weights = []
        raw_weights = [op["weight"] for op in options]
        max_weight = max(raw_weights)

        for op in options:
            transitions.append(op)
            new_weight = (op["weight"] / max_weight) ** (1 / max(0.01, current_chaos))
            weights.append(new_weight)

        node_sorted = random.choices(transitions, weights=weights, k=1)[0]
        symbol_str = symbol_mapping[node_sorted["symbol"]]
        beat.append(symbol_str)

        actual_state = node_sorted["target"]
        current_chaos = calculate_dynamic_chaos(base_chaos, node_sorted["weight"], max_weight)

    return beat


def output_music(msc_symbols: list[str], filename: str):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(130)))

    ticks_per_16th = mid.ticks_per_beat // 4
    time_acc = 0
    CHANNEL = 9

    for symbol in msc_symbols:
        if symbol == SILENCE:
            time_acc += ticks_per_16th
            continue

        notes = symbol.split('_')
        
        # Note On
        first_note = True
        for n in notes:
            if n not in TEXT_TO_MIDI:
                continue

            midi_note = TEXT_TO_MIDI[n]
            delta = time_acc if first_note else 0

            track.append(mido.Message('note_on', note=midi_note, velocity=100, time=delta, channel=CHANNEL))
            first_note = False

        # Set duration
        duration = int(ticks_per_16th * 0.8)
        
        # Note Off
        first_note_off = True
        for n in notes:
            if n in TEXT_TO_MIDI:
                midi_note = TEXT_TO_MIDI[n]
                delta = duration if first_note_off else 0
                track.append(mido.Message('note_off', note=midi_note, velocity=64, time=delta, channel=CHANNEL))
                first_note_off = False

        time_acc = ticks_per_16th - duration

    track.append(mido.MetaMessage('end_of_track', time=time_acc))

    mid.save(filename=filename)


def main():
    parser = argparse.ArgumentParser(description="FunkGen")
    parser.add_argument("model", help="The path of the model in format .json")
    parser.add_argument("chaos", type=float, nargs="?", default=1.0, help="Parameter of creativity.")
    parser.add_argument("-n", type=int, default=1, help="Quantity of beats to generate.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    parser.add_argument("--mapping", default="symbol_mapping.txt", help="Path of symbol_mapping.txt.")

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    model = read_model(args.model)
    symbol_mapping = read_symbol_mapping(args.mapping)

    for i in range(args.n):
        beat = generate(model, symbol_mapping, args.chaos)
        output_path = os.path.join("beats", f"beat_c{args.chaos}_s{args.seed}_{i}.mid")
        output_music(beat, output_path)


if __name__ == "__main__":
    main()
