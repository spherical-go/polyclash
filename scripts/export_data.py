import json
from pathlib import Path
from typing import Any

import numpy as np

from polyclash.data.data import (
    axis,
    cities,
    decoder,
    encoder,
    neighbors,
    pentagons,
    polylarges,
    polysmalls,
    triangles,
)


def ndarray_to_list(obj: "np.ndarray[Any, Any]") -> list[Any]:
    return list(obj.tolist())


def neighbors_to_dict(nb: dict[int, set[int]]) -> dict[str, list[int]]:
    return {str(k): sorted(v) for k, v in sorted(nb.items())}


def encoder_to_list(enc: list[tuple[int, ...]]) -> list[list[int]]:
    return [list(t) for t in enc]


def decoder_to_dict(dec: dict[tuple[int, ...], int]) -> dict[str, int]:
    return {str(list(k)): v for k, v in dec.items()}


def export_board(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "cities": ndarray_to_list(cities),
        "neighbors": neighbors_to_dict(neighbors),
        "pentagons": ndarray_to_list(pentagons),
        "triangles": ndarray_to_list(triangles),
        "polysmalls": ndarray_to_list(polysmalls),
        "polylarges": ndarray_to_list(polylarges),
        "encoder": encoder_to_list(encoder),
        "decoder": decoder_to_dict(decoder),
        "axis": ndarray_to_list(axis),
    }

    with open(output_path, "w") as f:
        json.dump(data, f)

    size_kb = output_path.stat().st_size / 1024
    print(f"Exported board data to {output_path} ({size_kb:.1f} KB)")
    print(f"  cities: {len(data['cities'])} points")
    print(f"  neighbors: {len(data['neighbors'])} entries")
    print(f"  pentagons: {len(data['pentagons'])} faces")
    print(f"  triangles: {len(data['triangles'])} faces")
    print(f"  polysmalls: {len(data['polysmalls'])} quads")
    print(f"  polylarges: {len(data['polylarges'])} quads")
    print(f"  encoder: {len(data['encoder'])} entries")
    print(f"  decoder: {len(data['decoder'])} entries")
    print(f"  axis: {len(data['axis'])} directions")


if __name__ == "__main__":
    export_board(Path("web/data/board.json"))
