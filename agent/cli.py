"""命令列版：uv run python -m agent.cli "下雨天想吃辣，預算 300" """
import sys
import time

from .llm import MODEL, PROFILE, client
from .schemas import SYSTEM, DecisionReport


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or "今天有點累，想吃熱的，預算 200"
    t0 = time.perf_counter()
    r = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": prompt}],
        response_format=DecisionReport,
    )
    report = r.choices[0].message.parsed
    print(f"[{PROFILE}/{MODEL}] {time.perf_counter() - t0:.1f}s "
          f"tokens={r.usage.total_tokens if r.usage else '?'}")
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
