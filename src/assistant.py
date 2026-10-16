# src/assistant.py
import sys
from pathlib import Path
import pandas as pd

# Ensure query module can be imported
sys.path.append(str(Path(__file__).resolve().parent))
from query import (
    get_dataset_summary,
    get_smallest_particles,
    get_highest_yield,
    compare_reducing_agents,
    compare_stabilizers,
    search_experiments
)


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)


def display_results(df: pd.DataFrame):
    if df.empty:
        print("\n[!] No matching experimental runs found.")
    else:
        print("\n" + df.to_string(index=False))


def interactive_menu():
    while True:
        print_header("Silver Nanoparticle Experimental Research Assistant")
        print("1. View Overall Dataset Summary")
        print("2. Find Optimal Conditions for Minimum Particle Size")
        print("3. Find Protocols for Maximum Yield (>= 90%)")
        print("4. Compare Performance Across Reducing Agents")
        print("5. Analyze Stabilizers (Zeta Potential & Size)")
        print("6. Custom Multi-Parameter Search")
        print("7. Exit")

        choice = input("\nEnter choice [1-7]: ").strip()

        if choice == "1":
            print_header("Dataset Summary Statistics")
            display_results(get_dataset_summary())

        elif choice == "2":
            n = input("How many top records to retrieve? (default: 5): ").strip()
            top_n = int(n) if n.isdigit() else 5
            print_header(f"Top {top_n} Experiments for Smallest Nanoparticles")
            display_results(get_smallest_particles(top_n=top_n))

        elif choice == "3":
            min_y = input("Enter minimum yield percentage (default: 95.0): ").strip()
            try:
                min_yield = float(min_y) if min_y else 95.0
            except ValueError:
                min_yield = 95.0
            print_header(f"Protocols with Yield >= {min_yield}%")
            display_results(get_highest_yield(min_yield=min_yield))

        elif choice == "4":
            print_header("Reducing Agent Comparison")
            display_results(compare_reducing_agents())

        elif choice == "5":
            print_header("Stabilizer Performance (Stability & Aggregation)")
            display_results(compare_stabilizers())

        elif choice == "6":
            print_header("Custom Search Filters (Press Enter to skip any filter)")
            solvent = input("Solvent (water / ethanol / water-ethanol 1:1): ").strip() or None
            reducing = input("Reducing Agent (e.g. glucose, ascorbic acid): ").strip() or None
            
            size_in = input("Max Particle Size (nm): ").strip()
            max_size = float(size_in) if size_in else None

            yield_in = input("Min Yield (%): ").strip()
            min_yield = float(yield_in) if yield_in else None

            print_header("Search Results")
            results = search_experiments(
                solvent=solvent,
                reducing_agent=reducing,
                max_size=max_size,
                min_yield=min_yield
            )
            display_results(results)

        elif choice == "7":
            print("\nExiting Research Assistant. Goodbye!\n")
            break
        else:
            print("\n[!] Invalid option. Please select 1 through 7.")

        input("\nPress Enter to return to menu...")


if __name__ == "__main__":
    interactive_menu()