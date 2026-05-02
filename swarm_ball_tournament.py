#!/usr/bin/env python3
"""
SWARM BALL TOURNAMENT — 9-team round-robin sphere-arena tournament for cocoon ensembles.

Loads a cocoon ensemble, partitions organisms into N teams, runs every team
against every other team in pairwise sphere-arena matches, prints a leaderboard.

Default: 18 organisms split into 9 teams of 2, every team plays every other
team once (36 matches), headless, weights frozen.

Vow note: enable_training=False. No weight updates during tournament.

Usage:
    python swarm_ball_tournament.py Children/cocoon_ensemble_20260428224400.py
    python swarm_ball_tournament.py <cocoon> --teams sequential
    python swarm_ball_tournament.py <cocoon> --teams random --num-balls 3 --visual
"""

import argparse
import importlib.util
import itertools
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_cocoon(cocoon_path: str):
    """Dynamic import of a cocoon .py file; instantiate CocoonAgent."""
    cocoon_path = os.path.abspath(cocoon_path)
    if not os.path.exists(cocoon_path):
        raise FileNotFoundError(f"Cocoon not found: {cocoon_path}")

    module_name = os.path.basename(cocoon_path).replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, cocoon_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    agent = module.CocoonAgent()
    n = len(agent.brains)
    print(f"  loaded: {n} organisms")
    return agent


def discover_alliances(agent) -> Optional[List[List[int]]]:
    """Inspect cocoon agent for alliance/team metadata; return list of index groups or None."""
    candidates = ("alliances", "alliance_pairs", "team_assignments",
                  "social_graph", "alliance_groups", "coalitions",
                  "confederation", "clans")
    for attr in candidates:
        if hasattr(agent, attr):
            value = getattr(agent, attr)
            print(f"  found alliance metadata: agent.{attr} (type={type(value).__name__})")
            return None  # parsing format-specific; surface presence only for now
    return None


def form_teams_sequential(agent, n_teams: int, team_size: int) -> Dict[str, List[int]]:
    teams = {}
    for t in range(n_teams):
        teams[f"team_{t+1}"] = list(range(t * team_size, (t + 1) * team_size))
    return teams


def form_teams_random(agent, n_teams: int, team_size: int, seed: int) -> Dict[str, List[int]]:
    import random
    rng = random.Random(seed)
    indices = list(range(len(agent.brains)))
    rng.shuffle(indices)
    teams = {}
    for t in range(n_teams):
        teams[f"team_{t+1}"] = indices[t * team_size:(t + 1) * team_size]
    return teams


def form_teams_alliance(agent, n_teams: int, team_size: int, seed: int) -> Dict[str, List[int]]:
    """Try alliance-derived teams; fall back to sequential."""
    discover_alliances(agent)
    print("  alliance-derived teams not yet decoded; using sequential")
    return form_teams_sequential(agent, n_teams, team_size)


@dataclass
class MatchResult:
    team_a: str
    team_b: str
    a_score: float
    b_score: float
    winner: str
    duration: float
    details: Dict = field(default_factory=dict)


@dataclass
class TeamRecord:
    name: str
    members: List[int]
    wins: int = 0
    losses: int = 0
    draws: int = 0
    points_for: float = 0.0
    points_against: float = 0.0
    matches: int = 0


def run_match(agent, a_name: str, a_idx: List[int], b_name: str, b_idx: List[int],
              max_misses: int, headless: bool, num_balls: int,
              seed: Optional[int]) -> MatchResult:
    from sphere_arena import SphereArena, GameMode

    arena = SphereArena(
        agent=agent,
        organism_indices=a_idx + b_idx,
        max_misses=max_misses,
        headless=headless,
        mode=GameMode.SWARM_DEFENSE,
        teams={"alpha": a_idx, "beta": b_idx},
        num_balls=num_balls,
        enable_training=False,
        enable_command_chain=True,
        seed=seed,
    )

    start = time.time()
    result = arena.run() if hasattr(arena, "run") else {}
    duration = time.time() - start

    # Score: remaining team lives. team_lives is set per-team in _setup_teams
    # and decremented as misses accrue. Higher remaining = better defense.
    a_score = float(arena.team_lives.get("alpha", 0)) if hasattr(arena, "team_lives") else 0.0
    b_score = float(arena.team_lives.get("beta", 0)) if hasattr(arena, "team_lives") else 0.0

    # Fallback: if team_lives didn't track per-team (older sphere builds), use
    # alive-organism counts at end as a coarse proxy.
    if a_score == 0.0 and b_score == 0.0:
        alive = getattr(arena, "alive_organisms", [])
        a_score = float(sum(1 for i in alive if i in a_idx))
        b_score = float(sum(1 for i in alive if i in b_idx))

    if a_score > b_score:
        winner = a_name
    elif b_score > a_score:
        winner = b_name
    else:
        winner = "draw"

    return MatchResult(
        team_a=a_name, team_b=b_name,
        a_score=a_score, b_score=b_score,
        winner=winner, duration=duration, details=result,
    )


def round_robin(agent, teams: Dict[str, List[int]], max_misses: int,
                headless: bool, num_balls: int, seed: int
                ) -> Tuple[Dict[str, TeamRecord], List[MatchResult]]:
    records = {name: TeamRecord(name=name, members=members)
               for name, members in teams.items()}
    matches: List[MatchResult] = []
    pairings = list(itertools.combinations(teams.keys(), 2))
    print(f"\nround-robin: {len(teams)} teams, {len(pairings)} matches\n")

    for i, (a_name, b_name) in enumerate(pairings, 1):
        a_idx, b_idx = teams[a_name], teams[b_name]
        print(f"[{i:2}/{len(pairings)}] {a_name}{a_idx} vs {b_name}{b_idx}")

        match = run_match(agent, a_name, a_idx, b_name, b_idx,
                          max_misses, headless, num_balls, seed + i)
        matches.append(match)

        ra, rb = records[a_name], records[b_name]
        ra.matches += 1; rb.matches += 1
        ra.points_for += match.a_score; ra.points_against += match.b_score
        rb.points_for += match.b_score; rb.points_against += match.a_score

        if match.winner == a_name:
            ra.wins += 1; rb.losses += 1
        elif match.winner == b_name:
            rb.wins += 1; ra.losses += 1
        else:
            ra.draws += 1; rb.draws += 1

        print(f"           -> {match.winner.upper()}  "
              f"({match.a_score:.0f} vs {match.b_score:.0f}, {match.duration:.1f}s)\n")

    return records, matches


def print_leaderboard(records: Dict[str, TeamRecord]):
    standings = sorted(
        records.values(),
        key=lambda r: (r.wins, r.points_for - r.points_against, r.points_for),
        reverse=True,
    )
    print("\n" + "=" * 70)
    print("FINAL STANDINGS")
    print("=" * 70)
    print(f"{'#':<4}{'Team':<10}{'Members':<14}{'W-L-D':<10}{'Diff':<8}{'PF':<6}{'PA':<6}")
    print("-" * 70)
    for rank, r in enumerate(standings, 1):
        diff = r.points_for - r.points_against
        members = "[" + ",".join(str(i) for i in r.members) + "]"
        wld = f"{r.wins}-{r.losses}-{r.draws}"
        print(f"{rank:<4}{r.name:<10}{members:<14}{wld:<10}"
              f"{diff:+.0f}".ljust(8)
              + f"{r.points_for:.0f}".ljust(6)
              + f"{r.points_against:.0f}")
    print("=" * 70)
    if standings:
        champ = standings[0]
        print(f"\nCHAMPION: {champ.name}  members={champ.members}  "
              f"record={champ.wins}-{champ.losses}-{champ.draws}")


def main():
    p = argparse.ArgumentParser(description="9-team swarm-ball round-robin tournament")
    p.add_argument("cocoon", help="path to cocoon .py file")
    p.add_argument("--teams", choices=["alliance", "sequential", "random"],
                   default="alliance", help="team formation strategy")
    p.add_argument("--n-teams", type=int, default=9)
    p.add_argument("--team-size", type=int, default=2)
    p.add_argument("--max-misses", type=int, default=10)
    p.add_argument("--num-balls", type=int, default=1)
    p.add_argument("--visual", action="store_true", help="render matches (default headless)")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    print("=" * 70)
    print("SWARM BALL TOURNAMENT")
    print("=" * 70)
    print(f"  cocoon:  {args.cocoon}")
    print(f"  teams:   {args.n_teams} x {args.team_size} ({args.teams})")
    print(f"  arena:   max_misses={args.max_misses}, num_balls={args.num_balls}, "
          f"headless={not args.visual}")

    agent = load_cocoon(args.cocoon)

    n = len(agent.brains)
    needed = args.n_teams * args.team_size
    if n < needed:
        print(f"\n  ERROR: cocoon has {n} organisms, need {needed} for "
              f"{args.n_teams} teams of {args.team_size}")
        sys.exit(1)
    if n > needed:
        print(f"\n  note: cocoon has {n} organisms; only first {needed} will be used")

    if args.teams == "alliance":
        teams = form_teams_alliance(agent, args.n_teams, args.team_size, args.seed)
    elif args.teams == "sequential":
        teams = form_teams_sequential(agent, args.n_teams, args.team_size)
    else:
        teams = form_teams_random(agent, args.n_teams, args.team_size, args.seed)

    print(f"\nteams:")
    for name, members in teams.items():
        print(f"  {name}: {members}")

    records, matches = round_robin(
        agent, teams,
        max_misses=args.max_misses,
        headless=not args.visual,
        num_balls=args.num_balls,
        seed=args.seed,
    )
    print_leaderboard(records)


if __name__ == "__main__":
    main()
