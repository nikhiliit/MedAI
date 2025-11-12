import sys
import time
import itertools
from typing import List

spinner_active = False

def show_processing_spinner():
    """Show a processing spinner while LLM is thinking."""
    global spinner_active
    spinner_chars = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    spinner_active = True

    while spinner_active:
        sys.stdout.write(f'\r{next(spinner_chars)} Analyzing your question... ')
        sys.stdout.flush()
        time.sleep(0.1)

    sys.stdout.write('\r' + ' ' * 30 + '\r')
    sys.stdout.flush()

def stop_spinner():
    """Stop the processing spinner."""
    global spinner_active
    spinner_active = False

def prompt_model_selection(available_models: List[str]) -> str:
    """Prompt user to select a model from available options."""
    print("\n🤖 Available LLM Models:")
    for i, model_name in enumerate(available_models, 1):
        print(f"  {i}. {model_name}")

    if not sys.stdin.isatty():
        print(f"⚠️  Non-interactive environment detected. Using default model: {available_models[0]}")
        return available_models[0]

    while True:
        try:
            choice = input(f"\nSelect model (1-{len(available_models)}) or enter model name: ").strip()

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(available_models):
                    selected = available_models[idx]
                    print(f"✅ Selected: {selected}")
                    return selected

            for model_name in available_models:
                if choice.lower() == model_name.lower():
                    print(f"✅ Selected: {model_name}")
                    return model_name

            print(f"❌ Invalid choice. Please select 1-{len(available_models)} or enter a valid model name.")

        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
