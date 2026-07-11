import argparse

from loop.orchestrator import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Auto Research: generator-critic paper pipeline")
    parser.add_argument(
        "--topic",
        default="Adaptive learning rate scheduling for small-batch SGD",
        help="Research topic/seed for the AI Scientist agent",
    )
    parser.add_argument(
        "--mode",
        choices=["single", "loop"],
        default="loop",
        help="single = one-pass baseline (no critic loop); loop = generator-critic revision loop",
    )
    parser.add_argument("--rounds", type=int, default=3, help="Max critic-revision rounds in loop mode")
    parser.add_argument("--outdir", default="outputs")
    args = parser.parse_args()

    run_pipeline(args.topic, mode=args.mode, rounds=args.rounds, outdir=args.outdir)


if __name__ == "__main__":
    main()
