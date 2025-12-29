"""
🎮 LeetCode Hero: Story-driven interactive CLI

This CLI allows the hero (you/dev) to explore the project realm,
select quests (problems we want to solve), and perform actions (run Marimo, open in VSCode, print contents) on objects (files, directories, etc).

Features:
- Smart indexing: only new/changed files are indexed.
- Persistent state: file hashes saved for fast future indexing.
- Progress feedback: tqdm shows live progress during indexing.
- Story-driven navigation: each function is a narrative chapter.

Notes:
- Draft of my story-driven development method inspired by Literate Programming (LP).
- Use of hashing inspired by Linux OS installation procedures where check downloaded hash against expected hash.
- Inspired by elm for this as well.
"""

import subprocess


def main():
    cmd = ["uv", "run", "python3", "-m", "scripts.cli", "run"]
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
